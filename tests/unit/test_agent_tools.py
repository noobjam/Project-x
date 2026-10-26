import asyncio
import json

import pytest
from agents.tool_context import ToolContext

from soc_verifier.agents.tools import (
    MAX_RESULT_CHARACTERS,
    EvidenceContext,
    get_plan_items,
    get_requirements,
    get_source_blocks,
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
