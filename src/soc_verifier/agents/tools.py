"""Bounded read-only evidence tools. No arbitrary files, shell or network access."""

import json
import logging
from dataclasses import dataclass
from typing import Any

from agents import RunContextWrapper, function_tool

from soc_verifier.agents.attempts import current_invocation
from soc_verifier.domain.models import SpecAnalysis, Specification, VerificationPlan

logger = logging.getLogger(__name__)
MAX_RESULTS = 12
MAX_RESULT_CHARACTERS = 24_000


@dataclass(frozen=True)
class EvidenceContext:
    specification: Specification
    analysis: SpecAnalysis | None = None
    plan: VerificationPlan | None = None


def _result(name: str, records: list[dict[str, Any]]) -> str:
    output: list[dict[str, Any]] = []
    for record in records[:MAX_RESULTS]:
        candidate = {"items": [*output, record], "remaining": len(records) - len(output) - 1}
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
    return json.dumps({"items": output, "remaining": len(records) - len(output)})


@function_tool(failure_error_function=None)
def search_spec(ctx: RunContextWrapper[EvidenceContext], query: str) -> str:
    """Search source text by words. Returns bounded matching blocks with source IDs.

    Args:
        query: Words or signal names to find in the specification.
    """
    terms = query.casefold().split()
    if not terms or len(query) > 256:
        raise ValueError("Search query must contain 1 to 256 characters")
    matches = []
    for block in ctx.context.specification.blocks:
        text = f"{block.section} {block.text}".casefold()
        score = sum(term in text for term in terms)
        if score:
            matches.append(
                (
                    score,
                    {
                        "id": block.id,
                        "section": block.section,
                        "text": block.text[:1000],
                        "truncated": len(block.text) > 1000,
                    },
                )
            )
    matches.sort(key=lambda item: item[0], reverse=True)
    return _result("search_spec", [record for _, record in matches])


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
            "next_character": start_character + 1500
            if len(block.text) > start_character + 1500
            else None,
        }
        for block in ctx.context.specification.blocks
    }
    return _result("get_source_blocks", _select(ids, records))


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
