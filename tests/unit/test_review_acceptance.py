"""Acceptance caveats must survive without being confused with executable defects."""

import pytest

from soc_verifier.domain.readiness import assess_readiness, permits_experimental_attempt
from soc_verifier.domain.review import read_review


@pytest.fixture
def specification(specification):
    block = specification.blocks[0]
    return specification.model_copy(
        update={
            "blocks": [
                block.model_copy(update={"text": block.text + " Engineering sign-off is pending."})
            ]
        }
    )


def note(specification):
    return {
        "kind": "pending_engineering_review",
        "description": "Engineering sign-off is pending.",
        "rationale": "This limits acceptance, without identifying an undefined test condition.",
        "evidence": [
            {"source_id": specification.blocks[0].id, "quote": "Engineering sign-off is pending."}
        ],
    }


def warning(specification):
    return {
        "severity": "warning",
        "target": "specification",
        "kind": "timing",
        "description": "The reset sampling edge is undefined.",
        "recommended_action": "Resolve the sampling edge with the owner.",
        "scope": {
            "kind": "global",
            "rationale": "Every scenario depends on this reset setup.",
            "evidence": note(specification)["evidence"],
        },
    }


def test_acceptance_note_is_preserved_without_blocking_binding(
    specification, analysis, verification_plan
):
    review = read_review(
        {"schema_version": "3.0", "findings": [], "acceptance_notes": [note(specification)]}
    )
    result = assess_readiness(specification, analysis, verification_plan, review)
    assert result.format == "execution-readiness-v3"
    assert result.items[0].status == "eligible"
    assert result.items[0].issue_ids == []
    assert result.human_approved is False
    assert len(result.issues) == 1
    assert result.issues[0].kind == "acceptance_note"
    assert result.issues[0].description == note(specification)["description"]
    assert result.issues[0].blocking is False
    assert read_review(review.model_dump()).model_dump() == review.model_dump()


@pytest.mark.parametrize("version", ["2.0", "3.0"])
def test_acceptance_note_never_waives_a_global_warning(
    specification, analysis, verification_plan, version
):
    data = {"schema_version": version, "findings": [warning(specification)]}
    if version == "3.0":
        data["acceptance_notes"] = [note(specification)]
    review = read_review(data)
    result = assess_readiness(specification, analysis, verification_plan, review)
    assert result.items[0].status == "blocked"
    blockers = [i for i in result.issues if i.blocking]
    assert len(blockers) == 1
    assert blockers[0].id == "review:0"
    assert not permits_experimental_attempt(blockers)
    if version == "2.0":
        assert "acceptance_notes" not in review.model_dump()


def test_acceptance_note_never_clears_explicit_questions(
    specification, analysis, verification_plan
):
    plan = verification_plan.model_copy(
        update={
            "items": [
                verification_plan.items[0].model_copy(
                    update={"open_questions": ["Which reset edge is specified?"]}
                )
            ]
        }
    )
    review = read_review(
        {"schema_version": "3.0", "findings": [], "acceptance_notes": [note(specification)]}
    )
    result = assess_readiness(specification, analysis, plan, review)
    assert result.items[0].status == "blocked"
    assert result.items[0].issue_ids == [f"item:{plan.items[0].id}:0"]


@pytest.mark.parametrize("field,value", [("source_id", "invented"), ("quote", "fabricated")])
def test_acceptance_note_requires_real_source_evidence(
    specification, analysis, verification_plan, field, value
):
    row = note(specification)
    row["evidence"][0][field] = value
    review = read_review({"schema_version": "3.0", "findings": [], "acceptance_notes": [row]})
    with pytest.raises(ValueError, match="Acceptance note evidence"):
        assess_readiness(specification, analysis, verification_plan, review)


@pytest.mark.parametrize("kind", ["timing", "source_conflict", "execution_binding"])
def test_executable_defect_is_not_an_acceptance_note_kind(specification, kind):
    row = note(specification)
    row["kind"] = kind
    with pytest.raises(ValueError):
        read_review({"schema_version": "3.0", "findings": [], "acceptance_notes": [row]})


def test_legacy_review_cannot_acquire_a_nonblocking_channel(specification):
    with pytest.raises(ValueError):
        read_review(
            {"schema_version": "2.0", "findings": [], "acceptance_notes": [note(specification)]}
        )


def test_acceptance_note_constraints_reach_the_provider_schema(specification):
    import jsonschema
    from agents.agent_output import AgentOutputSchema

    from soc_verifier.domain.review import ScopedPlanReview

    review = ScopedPlanReview.model_validate(
        {"findings": [], "acceptance_notes": [note(specification)]}
    )
    schema = AgentOutputSchema(ScopedPlanReview).json_schema()
    value = review.model_dump()
    jsonschema.validate(value, schema)
    value["acceptance_notes"][0]["evidence"] = []
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(value, schema)
