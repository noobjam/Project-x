"""Readiness follows explicit evidence scope, never keywords or blanket warning suppression."""

import pytest
from agents.agent_output import AgentOutputSchema

from soc_verifier.domain.models import PlanReview
from soc_verifier.domain.readiness import (
    ExecutionIssue,
    GapAssessment,
    assess_readiness,
    permits_experimental_attempt,
)
from soc_verifier.domain.source_audit import SourceAudit


@pytest.fixture
def graph(specification, analysis, verification_plan):
    second = analysis.requirements[0].model_copy(update={"id": "REQ-OTHER"})
    analysis = analysis.model_copy(update={"requirements": [analysis.requirements[0], second]})
    first = verification_plan.items[0]
    plan = verification_plan.model_copy(
        update={
            "items": [
                first,
                first.model_copy(update={"id": "B", "requirement_ids": [second.id]}),
                first.model_copy(update={"id": "C", "requirement_ids": [second.id]}),
            ]
        }
    )
    return specification, analysis, plan


def statuses(readiness):
    return {item.plan_item_id: item.status for item in readiness.items}


def scope(spec, *, disposition="block_requirements", **changes):
    return {
        "gap_index": 0,
        "disposition": disposition,
        "requirement_ids": ["REQ-OTHER"] if disposition == "block_requirements" else [],
        "note_kind": "specified_behavior" if disposition == "note" else None,
        "evidence": [{"source_id": spec.blocks[0].id, "quote": spec.blocks[0].text}],
        "rationale": "Synthetic evidence-scope fixture, not a semantic judgment.",
        **changes,
    }


@pytest.mark.parametrize(
    "target,blocked", [("plan", {"B"}), ("specification", {"B", "C"}), ("analysis", {"B", "C"})]
)
def test_review_scope_propagates_only_to_affected_scenarios(graph, target, blocked):
    spec, analysis, plan = graph
    review = PlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "target": target,
                    "item_ids": ["B"],
                    "description": "Unknown behavior",
                }
            ]
        }
    )
    result = assess_readiness(spec, analysis, plan, review)
    assert {i.plan_item_id for i in result.items if i.status == "blocked"} == blocked


def test_requirement_question_blocks_all_consumers_but_not_unrelated_items(graph):
    spec, analysis, plan = graph
    analysis = analysis.model_copy(
        update={
            "requirements": [
                analysis.requirements[0],
                analysis.requirements[1].model_copy(update={"open_questions": ["Unknown latency"]}),
            ]
        }
    )
    result = assess_readiness(spec, analysis, plan, PlanReview(findings=[]))
    assert statuses(result) == {plan.items[0].id: "eligible", "B": "blocked", "C": "blocked"}


def test_item_question_stays_local(graph):
    spec, analysis, plan = graph
    plan = plan.model_copy(
        update={
            "items": [
                plan.items[0],
                plan.items[1].model_copy(update={"open_questions": ["Missing probe"]}),
                plan.items[2],
            ]
        }
    )
    assert statuses(assess_readiness(spec, analysis, plan, PlanReview(findings=[]))) == {
        plan.items[0].id: "eligible",
        "B": "blocked",
        "C": "eligible",
    }


def test_unscoped_review_and_extraction_warnings_remain_global(graph):
    spec, analysis, plan = graph
    review = PlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "error",
                    "target": "specification",
                    "item_ids": [],
                    "description": "Conflicting clocks",
                }
            ]
        }
    )
    assert set(statuses(assess_readiness(spec, analysis, plan, review)).values()) == {"blocked"}
    spec = spec.model_copy(update={"extraction_warnings": ["Unparsed source table"]})
    assert set(
        statuses(assess_readiness(spec, analysis, plan, PlanReview(findings=[]))).values()
    ) == {"blocked"}


def test_unclassified_gap_is_global_even_if_it_says_out_of_scope(graph):
    spec, analysis, plan = graph
    analysis = analysis.model_copy(update={"gaps": ["Looks out of scope but not assessed"]})
    result = assess_readiness(spec, analysis, plan, PlanReview(findings=[]))
    assert all(i.status == "blocked" for i in result.items)
    assert result.issues[0].global_scope is True


def test_scoped_gap_blocks_every_consumer_and_preserves_original_text(graph):
    spec, analysis, plan = graph
    analysis = analysis.model_copy(update={"gaps": ["Unknown latency in second feature"]})
    assessment = GapAssessment.model_validate({"gaps": [scope(spec)]})
    result = assess_readiness(
        spec, analysis, plan, PlanReview(findings=[]), gap_assessment=assessment
    )
    assert statuses(result) == {plan.items[0].id: "eligible", "B": "blocked", "C": "blocked"}
    assert result.issues[0].description == analysis.gaps[0]


def test_note_does_not_clear_other_blockers(graph):
    spec, analysis, plan = graph
    analysis = analysis.model_copy(update={"gaps": ["A declared observation rule"]})
    assessment = GapAssessment.model_validate({"gaps": [scope(spec, disposition="note")]})
    review = PlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "target": "plan",
                    "item_ids": ["B"],
                    "description": "Missing internal probe",
                }
            ]
        }
    )
    result = assess_readiness(spec, analysis, plan, review, gap_assessment=assessment)
    assert statuses(result) == {plan.items[0].id: "eligible", "B": "blocked", "C": "eligible"}
    assert result.issues[-1].blocking is False
    assert result.issues[-1].description == analysis.gaps[0]
    assert result.human_approved is False


@pytest.mark.parametrize(
    "change",
    [
        lambda rows: rows.clear(),
        lambda rows: rows.append(rows[0]),
        lambda rows: rows[0].update(gap_index=5),
        lambda rows: rows[0].update(requirement_ids=["invented"]),
        lambda rows: rows[0]["evidence"][0].update(source_id="invented"),
        lambda rows: rows[0]["evidence"][0].update(quote="This was never specified"),
        lambda rows: rows[0].update(evidence=[]),
    ],
)
def test_missing_or_fabricated_gap_scopes_cannot_authorize_execution(graph, change):
    spec, analysis, plan = graph
    analysis = analysis.model_copy(update={"gaps": ["Unknown behavior"]})
    rows = [scope(spec)]
    change(rows)
    with pytest.raises(ValueError):
        assessment = GapAssessment.model_validate({"gaps": rows})
        assess_readiness(spec, analysis, plan, PlanReview(findings=[]), gap_assessment=assessment)


def test_unlocalized_gap_can_stay_blocked_without_fabricated_evidence(graph):
    spec, analysis, plan = graph
    analysis = analysis.model_copy(update={"gaps": ["Possible omitted behavior"]})
    assessment = GapAssessment.model_validate(
        {"gaps": [scope(spec, disposition="block_global", evidence=[])]}
    )
    assert all(
        i.status == "blocked"
        for i in assess_readiness(
            spec, analysis, plan, PlanReview(findings=[]), gap_assessment=assessment
        ).items
    )


def test_source_audit_findings_and_uncertain_knowledge_are_not_dropped(graph):
    spec, analysis, plan = graph
    audit = SourceAudit.model_validate(
        {
            "findings": [
                {
                    "id": "F1",
                    "kind": "unsupported_claim",
                    "requirement_ids": ["REQ-OTHER"],
                    "evidence_ids": ["passage-1"],
                    "description": "Unproven behavior",
                    "recommended_action": "Resolve",
                    "conflict": None,
                }
            ],
            "knowledge_applications": [],
        }
    )
    result = assess_readiness(spec, analysis, plan, PlanReview(findings=[]), source_audit=audit)
    assert statuses(result) == {plan.items[0].id: "eligible", "B": "blocked", "C": "blocked"}
    audit = SourceAudit.model_validate(
        {
            "findings": [],
            "knowledge_applications": [
                {
                    "entry_id": "K1",
                    "requirement_ids": [],
                    "evidence_ids": ["passage-1"],
                    "assessment": "uncertain",
                    "rationale": "Unlocalized applicability issue",
                }
            ],
        }
    )
    assert all(
        i.status == "blocked"
        for i in assess_readiness(
            spec, analysis, plan, PlanReview(findings=[]), source_audit=audit
        ).items
    )


def test_unknown_review_reference_is_rejected(graph):
    spec, analysis, plan = graph
    review = PlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "item_ids": ["invented"],
                    "description": "Cannot scope",
                }
            ]
        }
    )
    with pytest.raises(ValueError, match="unknown verification"):
        assess_readiness(spec, analysis, plan, review)


def test_gap_contract_is_accepted_by_actual_sdk():
    assert AgentOutputSchema(GapAssessment).json_schema()["additionalProperties"] is False


@pytest.mark.parametrize(
    "kind,scope,expected",
    [
        ("review", "unknown", True),
        ("analysis_gap", None, True),
        ("review", "mapped", False),
        ("review", "global", False),
        ("review", None, False),
        ("item_question", None, False),
        ("requirement_question", None, False),
        ("extraction_warning", None, False),
        ("source_audit", None, False),
        ("knowledge_uncertainty", None, False),
    ],
)
def test_experimental_attempt_has_an_explicit_narrow_boundary(kind, scope, expected):
    issue = ExecutionIssue.model_validate(
        {
            "id": "issue:0",
            "origin": "issue:0",
            "kind": kind,
            "description": "Synthetic issue",
            "scope_basis": scope,
            "blocking": True,
            "global_scope": True,
            "item_ids": [],
        }
    )
    assert permits_experimental_attempt([issue]) is expected
