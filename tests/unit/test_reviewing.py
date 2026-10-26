import json
from unittest.mock import Mock

import pytest

from soc_verifier.domain.models import PlanReview, ReviewFinding
from soc_verifier.workflows.spec_to_plan.reviewing import generate_review


def finding(ids):
    return PlanReview(
        findings=[
            ReviewFinding(
                severity="warning",
                target="specification",
                item_ids=ids,
                description="Register map is missing.",
            )
        ]
    )


def test_review_correction_keeps_evidence_and_requests_complete_findings():
    llm = Mock()
    llm.generate.side_effect = [finding(["REQ-001"]), finding([])]
    context = {"specification": "original source", "plan": [{"id": "PLAN-001"}]}
    result = generate_review(llm, instruction="review", context=context, known_items={"PLAN-001"})
    assert result.findings[0].description == "Register map is missing."
    assert result.findings[0].item_ids == []
    second = json.loads(llm.generate.call_args_list[1].kwargs["context"])
    assert second["specification"] == context["specification"]
    assert second["plan"] == context["plan"]
    assert second["validation_feedback"]["unknown_item_ids"] == ["REQ-001"]
    assert second["validation_feedback"]["allowed_plan_item_ids"] == ["PLAN-001"]
    assert "validation_feedback" not in context


def test_second_invalid_review_stops_after_two_budgeted_calls():
    llm = Mock()
    llm.generate.side_effect = [finding(["REQ-001"]), finding(["invented"])]
    with pytest.raises(ValueError, match="after one correction"):
        generate_review(llm, instruction="review", context={}, known_items={"PLAN-001"})
    assert llm.generate.call_count == 2


def test_transport_failure_during_review_is_not_retried():
    llm = Mock()
    llm.generate.side_effect = RuntimeError("transport failed")
    with pytest.raises(RuntimeError, match="transport failed"):
        generate_review(llm, instruction="review", context={}, known_items=set())
    assert llm.generate.call_count == 1
