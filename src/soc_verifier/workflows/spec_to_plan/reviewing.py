"""Validate review references and allow one explicit, budgeted correction."""

import json
import logging
from typing import Any

from soc_verifier.agents.base import AgentExecutor
from soc_verifier.domain.models import PlanReview

logger = logging.getLogger(__name__)


def validate_review(review: PlanReview, known: set[str]) -> None:
    if any(set(finding.item_ids) - known for finding in review.findings):
        raise ValueError("Review references unknown verification item IDs")


def generate_review(
    agents: AgentExecutor,
    *,
    instruction: str,
    context: dict[str, Any],
    known_items: set[str],
) -> PlanReview:
    for correction in range(2):
        result = agents.run(
            role="reviewer", instruction=instruction, context=json.dumps(context), schema=PlanReview
        )
        unknown = {
            identifier for finding in result.findings for identifier in finding.item_ids
        } - known_items
        if not unknown:
            return result
        if correction:
            raise ValueError("Review references unknown verification item IDs after one correction")
        logger.warning("stage=review citation_correction=1 unknown=%s", sorted(unknown))
        context = {
            **context,
            "rejected_review": result.model_dump(mode="json"),
            "validation_feedback": {
                "unknown_item_ids": sorted(unknown),
                "allowed_plan_item_ids": sorted(known_items),
                "instruction": (
                    "Return the complete corrected review. item_ids may contain only supplied "
                    "plan item IDs, never requirement or source IDs. Use an empty list for "
                    "findings with no associated plan item. Preserve supported findings; do "
                    "not invent IDs or drop findings solely to pass validation."
                ),
            },
        }
    raise AssertionError("Unreachable review correction state")
