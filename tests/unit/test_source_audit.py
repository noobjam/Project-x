import pytest
from pydantic import ValidationError

from soc_verifier.domain.source_audit import (
    ConflictComparison,
    KnowledgeApplication,
    SourceAudit,
    SourceFinding,
    bound_audit_schema,
    validate_source_audit,
)


@pytest.mark.parametrize("bad_field", ["finding", "requirement", "application", "conflict"])
def test_model_schema_constrains_every_reference_to_current_inputs(
    specification, analysis, bad_field
):
    schema = bound_audit_schema(specification, analysis)
    item = finding()
    application = KnowledgeApplication(
        entry_id="K01",
        requirement_ids=[analysis.requirements[0].id],
        evidence_ids=["P00001:U00000"],
        assessment="applicable",
        rationale="Synthetic guidance",
    )
    data = SourceAudit(findings=[item], knowledge_applications=[application]).model_dump()
    assert schema.model_validate(data).model_dump() == data
    if bad_field == "finding":
        data["findings"][0]["evidence_ids"] = ["P00001"]
    elif bad_field == "requirement":
        data["findings"][0]["requirement_ids"] = ["invented"]
    elif bad_field == "application":
        data["knowledge_applications"][0]["evidence_ids"] = ["P00001"]
    else:
        data["findings"][0].update(
            kind="source_conflict",
            conflict={
                "subject": "counter",
                "conditions": "reset",
                "left_evidence_ids": ["P00001:U00000"],
                "right_evidence_ids": ["P00001"],
                "incompatibility": "clear versus retain",
            },
        )
    with pytest.raises(ValidationError):
        schema.model_validate(data)


def finding(**changes):
    return SourceFinding(
        **{
            "id": "F1",
            "kind": "lost_qualifier",
            "requirement_ids": ["REQ-RST-001"],
            "evidence_ids": ["P00001:U00000"],
            "description": "The retained-state exception is absent.",
            "recommended_action": "Retain the source exception.",
            "conflict": None,
            **changes,
        }
    )


def test_omission_can_be_bound_without_inventing_a_requirement(
    specification, analysis, clean_audit
):
    audit = clean_audit.model_copy(
        update={"findings": [finding(kind="omission", requirement_ids=[])]}
    )
    validate_source_audit(
        audit, specification, analysis, known_knowledge=set(), read_knowledge=set()
    )
    assert audit.judgment_state == "agent_proposed"


@pytest.mark.parametrize(
    "change",
    [
        {"requirement_ids": ["made-up"]},
        {"evidence_ids": ["made-up"]},
    ],
)
def test_unknown_audit_targets_are_rejected(specification, analysis, clean_audit, change):
    audit = clean_audit.model_copy(update={"findings": [finding(**change)]})
    with pytest.raises(ValueError, match="unknown"):
        validate_source_audit(
            audit, specification, analysis, known_knowledge=set(), read_knowledge=set()
        )


def test_conflict_requires_two_distinct_cited_sides(specification, analysis, clean_audit):
    with pytest.raises(ValidationError, match="two-sided"):
        finding(kind="source_conflict")
    comparison = ConflictComparison(
        subject="counter",
        conditions="warm reset",
        left_evidence_ids=["P00001:U00000"],
        right_evidence_ids=["P00001:U00000"],
        incompatibility="clear versus retain",
    )
    audit = clean_audit.model_copy(
        update={"findings": [finding(kind="source_conflict", conflict=comparison)]}
    )
    with pytest.raises(ValueError, match="distinct"):
        validate_source_audit(
            audit, specification, analysis, known_knowledge=set(), read_knowledge=set()
        )
    missing_side = comparison.model_copy(update={"right_evidence_ids": ["P00002:U00000"]})
    audit = clean_audit.model_copy(
        update={"findings": [finding(kind="source_conflict", conflict=missing_side)]}
    )
    with pytest.raises(ValueError, match="distinct"):
        validate_source_audit(
            audit, specification, analysis, known_knowledge=set(), read_knowledge=set()
        )


def test_unknown_relationship_is_retained_without_inventing_a_conflict(
    specification, analysis, clean_audit
):
    # The host checks the finding contract, not whether an LLM would recognize this control.
    spec = specification.model_copy(
        update={
            "blocks": [
                specification.blocks[0].model_copy(
                    update={
                        "text": (
                            "Input reset synchronization takes three cycles. "
                            "Output reset delivery takes seven cycles."
                        )
                    }
                )
            ]
        }
    )
    audit = clean_audit.model_copy(
        update={
            "findings": [
                finding(
                    kind="unresolved_context",
                    description="The relationship between the two reset paths is not given.",
                    recommended_action="Ask the owner only if combined latency is needed.",
                )
            ]
        }
    )
    validate_source_audit(audit, spec, analysis, known_knowledge=set(), read_knowledge=set())
    assert audit.findings[0].conflict is None


@pytest.mark.parametrize("known, read", [(set(), {"K01"}), ({"K01"}, set())])
def test_knowledge_application_needs_existing_and_read_entry(
    specification, analysis, clean_audit, known, read
):
    application = KnowledgeApplication(
        entry_id="K01",
        requirement_ids=["REQ-RST-001"],
        evidence_ids=["P00001:U00000"],
        assessment="applicable",
        rationale="Reset exception checklist applies to this reset requirement.",
    )
    audit = clean_audit.model_copy(update={"knowledge_applications": [application]})
    with pytest.raises(ValueError, match="actually read"):
        validate_source_audit(
            audit, specification, analysis, known_knowledge=known, read_knowledge=read
        )
    validate_source_audit(
        audit, specification, analysis, known_knowledge={"K01"}, read_knowledge={"K01"}
    )


def test_duplicate_audit_records_fail(specification, analysis, clean_audit):
    audit = clean_audit.model_copy(update={"findings": [finding(), finding()]})
    with pytest.raises(ValueError, match="Duplicate"):
        validate_source_audit(
            audit, specification, analysis, known_knowledge=set(), read_knowledge=set()
        )
