import asyncio
import hashlib
import json

import pytest
from agents import ModelBehaviorError
from agents.tool_context import ToolContext

from soc_verifier.agents.tools import (
    MAX_RESULT_CHARACTERS,
    MAX_RESULTS,
    EvidenceContext,
    get_knowledge_entries,
    get_plan_items,
    get_requirements,
    get_source_blocks,
    search_knowledge,
    search_spec,
)


def invoke(tool, context, **arguments):
    encoded = json.dumps(arguments)
    wrapper = ToolContext(context, tool_name=tool.name, tool_call_id="test", tool_arguments=encoded)
    result = asyncio.run(tool.on_invoke_tool(wrapper, encoded))
    return json.loads(result)


def test_source_search_and_pagination_preserve_text(specification):
    text = "reset: " + "abc123" * 600
    block = specification.blocks[0].model_copy(update={"text": text})
    context = EvidenceContext(specification.model_copy(update={"blocks": [block]}))
    search = invoke(search_spec, context, query="reset")
    assert search["items"][0]["truncated"]
    rebuilt = ""
    offset = 0
    while offset is not None:
        page = invoke(get_source_blocks, context, ids=[block.id], start_character=offset)
        item = page["items"][0]
        rebuilt += item["text"]
        offset = item["next_character"]
        assert len(json.dumps(page)) <= MAX_RESULT_CHARACTERS
    assert rebuilt == text


@pytest.mark.parametrize("section_length", [10, 9000])
def test_source_search_pages_every_ranked_hit_within_response_limit(specification, section_length):
    blocks = [
        specification.blocks[0].model_copy(
            update={
                "id": f"P{i:05}",
                "section": "s" * section_length,
                "text": "timer reset" if i % 2 else "timer",
            }
        )
        for i in range(29)
    ]
    context = EvidenceContext(specification.model_copy(update={"blocks": blocks}))
    expected = [block.id for block in blocks[1::2] + blocks[::2]]
    first = invoke(search_spec, context, query="timer reset")
    assert first == invoke(search_spec, context, query="timer reset", offset=0)
    found, offset = [], 0
    while offset is not None:
        page = invoke(search_spec, context, query="timer reset", offset=offset)
        assert 0 < len(page["items"]) <= MAX_RESULTS
        assert len(json.dumps(page)) <= MAX_RESULT_CHARACTERS
        found.extend(item["id"] for item in page["items"])
        assert page["remaining"] == len(blocks) - len(found)
        assert page["next_offset"] == (len(found) if page["remaining"] else None)
        offset = page["next_offset"]
    assert found == expected
    assert len(set(found)) == len(found)
    for end in (len(blocks), len(blocks) + 100):
        assert invoke(search_spec, context, query="timer reset", offset=end) == {
            "items": [],
            "remaining": 0,
            "next_offset": None,
        }


@pytest.mark.parametrize(
    "arguments", [{"query": ""}, {"query": "a" * 257}, {"query": "reset", "offset": -1}]
)
def test_source_search_rejects_invalid_bounds(specification, arguments):
    with pytest.raises(ValueError):
        invoke(search_spec, EvidenceContext(specification), **arguments)


def test_source_search_handles_no_hits_and_rejects_oversized_item(specification):
    context = EvidenceContext(specification)
    assert invoke(search_spec, context, query="no-matching-signal") == {
        "items": [],
        "remaining": 0,
        "next_offset": None,
    }
    block = specification.blocks[0].model_copy(
        update={"section": "s" * MAX_RESULT_CHARACTERS, "text": "reset"}
    )
    context = EvidenceContext(specification.model_copy(update={"blocks": [block]}))
    with pytest.raises(ValueError, match="exceeds the tool response limit"):
        invoke(search_spec, context, query="reset")


def test_source_search_centers_late_unicode_match_and_audits_exact_span(specification):
    text = "ß\t" * 850 + "\nThe STRASSE interface has a reset latency.\n" + "tail " * 400
    block = specification.blocks[0].model_copy(update={"text": text, "section": "Interface"})
    records = []
    context = EvidenceContext(
        specification.model_copy(update={"blocks": [block]}), source_audit=records.append
    )
    item = invoke(search_spec, context, query="Straße")["items"][0]
    assert item["start_character"] > 1000
    assert "STRASSE" in item["text"]
    assert text[item["start_character"] : item["end_character"]] == item["text"]
    audit = records[-1]
    assert audit["query_sha256"] == hashlib.sha256("Straße".encode()).hexdigest()
    assert audit["source_ids"] == [block.id]
    assert audit["spans"][0]["excerpt_sha256"] == hashlib.sha256(item["text"].encode()).hexdigest()
    assert "STRASSE" not in json.dumps(audit)
    page = invoke(
        get_source_blocks, context, ids=[block.id], start_character=item["start_character"]
    )
    read = page["items"][0]
    assert text[read["start_character"] : read["end_character"]] == read["text"]
    assert records[-1]["tool"] == "get_source_blocks"
    with pytest.raises(ValueError, match="exceeds the block"):
        invoke(get_source_blocks, context, ids=[block.id], start_character=len(text))


@pytest.mark.parametrize("ids", [["invented"], [], ["P00001"] * 13])
def test_source_tool_rejects_unknown_or_unbounded_requests(specification, ids):
    with pytest.raises(ValueError):
        invoke(get_source_blocks, EvidenceContext(specification), ids=ids, start_character=0)


def test_tools_expose_validated_requirements_and_full_plan(
    specification, analysis, verification_plan
):
    context = EvidenceContext(specification, analysis, verification_plan)
    requirement = invoke(get_requirements, context, ids=[analysis.requirements[0].id])
    assert requirement["items"][0] == analysis.requirements[0].model_dump(mode="json")
    plan = invoke(get_plan_items, context, ids=[verification_plan.items[0].id])
    assert plan["items"][0]["stimulus"] == verification_plan.items[0].stimulus
    with pytest.raises(ValueError):
        invoke(get_plan_items, EvidenceContext(specification), ids=[verification_plan.items[0].id])


def test_knowledge_search_pages_all_hits_and_read_preserves_limits(
    specification, knowledge_snapshot
):
    entries = [
        knowledge_snapshot.entries[0].model_copy(update={"id": f"K{i:02}"}) for i in range(1, 13)
    ]
    text = "x" * 5000 + " reset limitation: preserve explicit exceptions."
    entries[0] = entries[0].model_copy(
        update={"text": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}
    )
    snapshot = knowledge_snapshot.model_copy(update={"entries": entries})
    audits = []
    context = EvidenceContext(specification, knowledge=snapshot, knowledge_audit=audits.append)
    offset, found = 0, []
    while offset is not None:
        page = invoke(search_knowledge, context, query="reset", offset=offset)
        found.extend(r["id"] for r in page["items"])
        assert len(page["items"]) <= 5
        offset = page["next_offset"]
    assert found == [entry.id for entry in entries]
    first = invoke(search_knowledge, context, query="limitation")["items"][0]
    assert "preserve explicit exceptions" in first["excerpt"]
    rebuilt, offset = "", 0
    while offset is not None:
        page = invoke(get_knowledge_entries, context, ids=["K01"], start_character=offset)
        assert len(json.dumps(page)) <= MAX_RESULT_CHARACTERS
        item = page["items"][0]
        rebuilt += item["text"]
        offset = item["next_character"]
    assert rebuilt == text
    assert audits[-1]["entry_hashes"] == {"K01": entries[0].sha256}
    assert audits[-1]["offset"] == 4000
    assert "text" not in audits[-1]


@pytest.mark.parametrize(
    "arguments",
    [
        {"ids": []},
        {"ids": ["K99"]},
        {"ids": ["K01"] * 2},
        {"ids": ["K01"], "start_character": -1},
        {"ids": ["K01"], "start_character": 10000},
    ],
)
def test_knowledge_reads_reject_invalid_bounds(specification, knowledge_snapshot, arguments):
    with pytest.raises((ValueError, ModelBehaviorError)):
        invoke(
            get_knowledge_entries,
            EvidenceContext(specification, knowledge=knowledge_snapshot),
            **arguments,
        )


@pytest.mark.parametrize(
    "arguments",
    [
        {"query": ""},
        {"query": "a" * 257},
        {"query": "reset", "offset": -1},
    ],
)
def test_knowledge_search_rejects_invalid_bounds(specification, knowledge_snapshot, arguments):
    with pytest.raises(ValueError):
        invoke(
            search_knowledge,
            EvidenceContext(specification, knowledge=knowledge_snapshot),
            **arguments,
        )


def test_knowledge_tools_require_bound_snapshot(specification):
    with pytest.raises(ValueError, match="No knowledge snapshot"):
        invoke(search_knowledge, EvidenceContext(specification), query="reset")
    with pytest.raises(ValueError, match="No knowledge snapshot"):
        invoke(get_knowledge_entries, EvidenceContext(specification), ids=["K01"])
