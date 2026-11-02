"""Bounded read-only evidence tools. No arbitrary files, shell or network access."""

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any

from agents import RunContextWrapper, function_tool
from pydantic import Field

from soc_verifier.agents.attempts import current_invocation
from soc_verifier.domain.hardware import HardwareSnapshot
from soc_verifier.domain.knowledge import KnowledgeSnapshot
from soc_verifier.domain.models import SpecAnalysis, Specification, VerificationPlan

logger = logging.getLogger(__name__)
MAX_RESULTS = 12
MAX_RESULT_CHARACTERS = 24_000


@dataclass(frozen=True)
class EvidenceContext:
    specification: Specification
    analysis: SpecAnalysis | None = None
    plan: VerificationPlan | None = None
    knowledge: KnowledgeSnapshot | None = None
    knowledge_audit: Callable[[dict[str, Any]], None] | None = None
    source_audit: Callable[[dict[str, Any]], None] | None = None
    hardware: HardwareSnapshot | None = None
    hardware_audit: Callable[[dict[str, Any]], None] | None = None


def _result(name: str, records: list[dict[str, Any]], *, offset: int | None = None) -> str:
    def response(items: list[dict[str, Any]]) -> dict[str, Any]:
        remaining = len(records) - len(items)
        result: dict[str, Any] = {"items": items, "remaining": remaining}
        if offset is not None:
            result["next_offset"] = offset + len(items) if remaining else None
        return result

    output: list[dict[str, Any]] = []
    for record in records[:MAX_RESULTS]:
        candidate = response([*output, record])
        if len(json.dumps(candidate)) > MAX_RESULT_CHARACTERS:
            break
        output.append(record)
    invocation = current_invocation.get()
    logger.info(
        "agent_tool name=%s returned=%s remaining=%s task=%s invocation=%s",
        name,
        len(output),
        len(records) - len(output),
        invocation.task.task_id if invocation else None,
        invocation.invocation_id if invocation else None,
    )
    if records and not output:
        raise ValueError("Evidence item exceeds the tool response limit; narrow the requested data")
    return json.dumps(response(output))


def _source_result(
    ctx: RunContextWrapper[EvidenceContext],
    name: str,
    records: list[dict[str, Any]],
    *,
    offset: int | None = None,
    query: str | None = None,
) -> str:
    result = _result(name, records, offset=offset)
    if ctx.context.source_audit is not None:
        page = json.loads(result)
        items = page["items"]
        ctx.context.source_audit(
            {
                "tool": name,
                "source_ids": [item["id"] for item in items],
                "query_sha256": hashlib.sha256(query.encode()).hexdigest()
                if query is not None
                else None,
                "offset": offset,
                "next_offset": page.get("next_offset"),
                "remaining": page["remaining"],
                "spans": [
                    {
                        "id": item["id"],
                        "start_character": item["start_character"],
                        "end_character": item["end_character"],
                        "excerpt_sha256": hashlib.sha256(item["text"].encode()).hexdigest(),
                    }
                    for item in items
                ],
            }
        )
    return result


def _excerpt_start(text: str, terms: list[str]) -> int:
    folded = text.casefold()
    hits = [folded.find(term) for term in terms if term in folded]
    if not hits:
        return 0  # A section-title match may have no corresponding match in the block.
    target = min(hits)
    folded_offset = 0
    for index, character in enumerate(text):
        folded_offset += len(character.casefold())
        if folded_offset > target:
            return max(0, index - 200)
    return 0


@function_tool(failure_error_function=None)
def search_spec(ctx: RunContextWrapper[EvidenceContext], query: str, offset: int = 0) -> str:
    """Search source text by words. Returns bounded matching blocks with source IDs.

    Follow next_offset with the same query to read more matches; null means complete.
    Text excerpts are centered on a match; character offsets refer to the original block.

    Args:
        query: Words or signal names to find in the specification.
        offset: Position in the ranked matches, starting at zero.
    """
    terms = query.casefold().split()
    if not terms or len(query) > 256:
        raise ValueError("Search query must contain 1 to 256 characters")
    if offset < 0:
        raise ValueError("Search offset must be non-negative")
    matches = []
    for block in ctx.context.specification.blocks:
        text = f"{block.section} {block.text}".casefold()
        score = sum(term in text for term in terms)
        if score:
            start = _excerpt_start(block.text, terms)
            end = min(len(block.text), start + 1000)
            matches.append(
                (
                    score,
                    {
                        "id": block.id,
                        "section": block.section,
                        "text": block.text[start:end],
                        "start_character": start,
                        "end_character": end,
                        "truncated": start > 0 or end < len(block.text),
                    },
                )
            )
    matches.sort(key=lambda item: item[0], reverse=True)
    return _source_result(
        ctx, "search_spec", [record for _, record in matches[offset:]], offset=offset, query=query
    )


@function_tool(failure_error_function=None)
def read_rtl(
    ctx: RunContextWrapper[EvidenceContext],
    source_id: str,
    start_line: int = 1,
    max_lines: int = 80,
) -> str:
    """Read pinned RTL evidence; line numbers are one-based and next_line continues the file.

    Args:
        source_id: An RTL source ID from the task's hardware source directory.
        start_line: First line to read, starting at one.
        max_lines: Number of lines to return, from one to 120.
    """
    hardware = ctx.context.hardware
    if hardware is None or start_line < 1 or not 1 <= max_lines <= 120:
        raise ValueError("RTL reads require a bound snapshot and valid line bounds")
    source = next((s for s in hardware.sources if s.id == source_id), None)
    if source is None:
        raise ValueError("Unknown RTL source ID")
    lines = source.text.splitlines()
    if start_line > len(lines):
        raise ValueError("RTL line offset exceeds the source")
    end = min(len(lines), start_line - 1 + max_lines)
    text = "\n".join(lines[start_line - 1 : end])
    record = {
        "id": source.id,
        "sha256": source.sha256,
        "start_line": start_line,
        "end_line": end,
        "next_line": end + 1 if end < len(lines) else None,
        "text": text,
    }
    result = _result("read_rtl", [record])
    if ctx.context.hardware_audit is not None:
        ctx.context.hardware_audit(
            {
                "tool": "read_rtl",
                "source_ids": [source.id],
                "source_sha256": source.sha256,
                "start_line": start_line,
                "end_line": end,
                "excerpt_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
        )
    return result


def _select(ids: list[str], records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not 1 <= len(ids) <= MAX_RESULTS:
        raise ValueError(f"Request between 1 and {MAX_RESULTS} IDs")
    if set(ids) - records.keys():
        raise ValueError("Requested IDs do not exist in the current evidence")
    return [records[identifier] for identifier in ids]


@function_tool(failure_error_function=None)
def get_source_blocks(
    ctx: RunContextWrapper[EvidenceContext],
    ids: list[str],
    start_character: int = 0,
) -> str:
    """Retrieve up to 12 source blocks by exact ID, at most 1500 characters per block.

    Use next_character to retrieve the next page of a long block; null means complete.
    """
    if start_character < 0:
        raise ValueError("Source offset must be non-negative")
    records = {
        block.id: {
            "id": block.id,
            "section": block.section,
            "text": block.text[start_character : start_character + 1500],
            "start_character": start_character,
            "end_character": min(len(block.text), start_character + 1500),
            "next_character": start_character + 1500
            if len(block.text) > start_character + 1500
            else None,
        }
        for block in ctx.context.specification.blocks
    }
    selected = _select(ids, records)
    if any(not item["text"] for item in selected):
        raise ValueError("Source character offset exceeds the block")
    return _source_result(ctx, "get_source_blocks", selected)


@function_tool(failure_error_function=None)
def get_requirements(ctx: RunContextWrapper[EvidenceContext], ids: list[str]) -> str:
    """Retrieve up to 12 validated requirements by their exact IDs."""
    analysis = ctx.context.analysis
    records = (
        {item.id: item.model_dump(mode="json") for item in analysis.requirements}
        if analysis
        else {}
    )
    return _result("get_requirements", _select(ids, records))


@function_tool(failure_error_function=None)
def get_plan_items(ctx: RunContextWrapper[EvidenceContext], ids: list[str]) -> str:
    """Retrieve up to 12 verification scenarios with full stimulus and expected results."""
    plan = ctx.context.plan
    records = {item.id: item.model_dump(mode="json") for item in plan.items} if plan else {}
    return _result("get_plan_items", _select(ids, records))


def _knowledge(ctx: RunContextWrapper[EvidenceContext]) -> KnowledgeSnapshot:
    if ctx.context.knowledge is None:
        raise ValueError("No knowledge snapshot is bound to this task")
    return ctx.context.knowledge


def _knowledge_result(
    ctx: RunContextWrapper[EvidenceContext], name: str, records: list[dict[str, Any]], offset: int
) -> str:
    result = _result(name, records)
    returned = json.loads(result)["items"]
    if ctx.context.knowledge_audit is not None:
        ctx.context.knowledge_audit(
            {
                "tool": name,
                "entry_ids": [r["id"] for r in returned],
                "offset": offset,
                "entry_hashes": {r["id"]: r["sha256"] for r in returned},
                "next_characters": {r["id"]: r.get("next_character") for r in returned},
            }
        )
    return result


@function_tool(failure_error_function=None)
def search_knowledge(ctx: RunContextWrapper[EvidenceContext], query: str, offset: int = 0) -> str:
    """Search reusable verification guidance, not design facts. Read matching entries before use.

    Returns at most five matches. Increase offset by the returned item count to page results.
    Entry status identifies approved knowledge versus provisional trial material.
    """
    if not query.strip() or len(query) > 256 or offset < 0:
        raise ValueError("Knowledge query must have 1-256 characters and a nonnegative offset")
    terms = query.casefold().split()
    matches = []
    for entry in _knowledge(ctx).entries:
        haystack = entry.text.casefold()
        score = sum(term in haystack for term in terms)
        if score:
            positions = [haystack.find(term) for term in terms if term in haystack]
            start = max(0, min(positions) - 100)
            matches.append(
                (
                    score,
                    entry.id,
                    {
                        "id": entry.id,
                        "title": entry.title,
                        "status": entry.status,
                        "sha256": entry.sha256,
                        "excerpt": entry.text[start : start + 500],
                        "source_path": entry.source_path,
                    },
                )
            )
    matches.sort(key=lambda item: (-item[0], item[1]))
    selected = [record for _, _, record in matches[offset : offset + 5]]
    result = json.loads(_knowledge_result(ctx, "search_knowledge", selected, offset))
    result["remaining"] = max(0, len(matches) - offset - len(result["items"]))
    result["next_offset"] = offset + len(result["items"]) if result["remaining"] else None
    return json.dumps(result)


@function_tool(failure_error_function=None)
def get_knowledge_entries(
    ctx: RunContextWrapper[EvidenceContext],
    ids: Annotated[list[str], Field(min_length=1, max_length=4)],
    start_character: int = 0,
) -> str:
    """Read selected guidance by exact ID, up to four entries and 4000 characters per entry.

    Follow next_character for remaining text, including limits. Guidance never supplies
    normative design requirements, signal values, executable permissions or approval.
    """
    if not 1 <= len(ids) <= 4 or len(set(ids)) != len(ids) or start_character < 0:
        raise ValueError("Request 1-4 distinct knowledge IDs and a nonnegative character offset")
    records = {entry.id: entry for entry in _knowledge(ctx).entries}
    if set(ids) - records.keys():
        raise ValueError("Unknown knowledge ID in the bound snapshot")
    result = []
    for identifier in ids:
        entry = records[identifier]
        if start_character >= len(entry.text):
            raise ValueError("Knowledge character offset exceeds the entry")
        result.append(
            {
                "id": entry.id,
                "title": entry.title,
                "status": entry.status,
                "reviewer": entry.reviewer,
                "source_path": entry.source_path,
                "sha256": entry.sha256,
                "text": entry.text[start_character : start_character + 4000],
                "start_character": start_character,
                "next_character": start_character + 4000
                if len(entry.text) > start_character + 4000
                else None,
            }
        )
    return _knowledge_result(ctx, "get_knowledge_entries", result, start_character)
