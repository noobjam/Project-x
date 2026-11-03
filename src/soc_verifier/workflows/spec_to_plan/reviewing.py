"""Validate review references and allow one explicit, budgeted correction."""

import json
import logging
from typing import Any

from soc_verifier.agents.base import AgentExecutor
from soc_verifier.agents.tasks import TaskEnvelope
from soc_verifier.domain.models import SpecAnalysis, Specification, VerificationPlan
from soc_verifier.domain.review import Review, ScopedPlanReview, validate_review_context

logger = logging.getLogger(__name__)


def validate_review(review: Review, known: set[str]) -> None:
    if any(set(finding.item_ids) - known for finding in review.findings):
        raise ValueError("Review references unknown verification item IDs")


def generate_review(
    agents: AgentExecutor,
    *,
    instruction: str,
    context: dict[str, Any],
    known_items: set[str],
    specification: Specification,
    analysis: SpecAnalysis,
    plan: VerificationPlan,
    task: TaskEnvelope | None = None,
) -> ScopedPlanReview:
    context = {
        **context,
        "review_scope_directory": {
            "source_ids": [b.id for b in specification.blocks],
            "requirements": [
                {"id": r.id, "source_ids": r.source_ids} for r in analysis.requirements
            ],
            "plan_items": [
                {"id": i.id, "requirement_ids": i.requirement_ids}
                for i in plan.items
                if i.id in known_items
            ],
        },
    }
    for correction in range(2):
        result = agents.run(
            role="reviewer",
            instruction=instruction,
            context=json.dumps(context),
            schema=ScopedPlanReview,
            task=task,
        )
        try:
            validate_review(result, known_items)
            validate_review_context(result, specification, analysis, plan)
        except ValueError as error:
            validation_error = str(error)
        else:
            return result
        if correction:
            raise ValueError(f"Invalid review after one correction: {validation_error}")
        logger.warning("stage=review citation_correction=1")
        context = {
            **context,
            "rejected_review": result.model_dump(mode="json"),
            "validation_feedback": {
                "error": validation_error,
                "allowed_plan_item_ids": sorted(known_items),
                "instruction": (
                    "Return the complete corrected review with explicit scope. Use IDs from "
                    "review_scope_directory and exact quotes from bound specification evidence. "
                    "An omitted requirement may use source scope without invented IDs. Use "
                    "unknown scope if impact cannot be established; never silently promote it "
                    "to global or drop findings solely to pass validation. A global claim must "
                    "account for every plan item with an exact plan-field quote and source "
                    "evidence indices. Do not invent dependencies to complete that accounting."
                ),
            },
        }
    raise AssertionError("Unreachable review correction state")
