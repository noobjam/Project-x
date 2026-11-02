"""Synthetic scope controls; these measure routing, not live reviewer accuracy."""

import pytest

from soc_verifier.domain.readiness import assess_readiness
from soc_verifier.domain.review import ScopedPlanReview, read_review


def finding(spec, kind="requirements", **scope):
    return {
        "severity": "warning",
        "target": "specification",
        "kind": "timing",
        "description": "Data output settling is unspecified.",
        "recommended_action": "Resolve data observation timing with the design owner.",
        "scope": {
            "kind": kind,
            "rationale": "Only data comparisons depend on data settling.",
            "evidence": [{"source_id": spec.blocks[0].id, "quote": spec.blocks[0].text}],
            **scope,
        },
    }


@pytest.fixture
def data_and_flags(specification, analysis, verification_plan):
    spec = specification.model_copy(
        update={
            "blocks": [
                specification.blocks[0].model_copy(
                    update={"text": "Data is valid once settled. Fill reports stored word count."}
                )
            ]
        }
    )
    data = analysis.requirements[0].model_copy(
        update={"id": "DATA", "statement": "Data is valid once settled."}
    )
    flags = data.model_copy(update={"id": "FILL", "statement": "Fill reports stored word count."})
    analysis = analysis.model_copy(update={"requirements": [data, flags]})
    first = verification_plan.items[0].model_copy(
        update={
            "id": "data",
            "requirement_ids": ["DATA"],
            "objective": "Compare data after a write",
            "preconditions": ["Queue is empty"],
            "stimulus": ["Write 7"],
            "expected_results": ["Data reads 7 once settled"],
            "coverage_intent": ["Stored value"],
            "environment_needs": ["Output observation"],
        }
    )
    plan = verification_plan.model_copy(
        update={
            "items": [
                first,
                first.model_copy(update={"id": "data-again"}),
                first.model_copy(
                    update={
                        "id": "fill",
                        "requirement_ids": ["FILL"],
                        "objective": "Count accepted words without comparing data",
                        "stimulus": ["Write 7"],
                        "expected_results": ["Fill increases from zero to one"],
                        "coverage_intent": ["Occupancy transition"],
                    }
                ),
            ]
        }
    )
    return spec, analysis, plan


def test_requirement_finding_without_item_ids_leaves_flag_checks_eligible(data_and_flags):
    spec, analysis, plan = data_and_flags
    review = ScopedPlanReview(findings=[finding(spec, requirement_ids=["DATA"])])
    result = assess_readiness(spec, analysis, plan, review)
    assert [i.status for i in result.items] == ["blocked", "blocked", "eligible"]
    assert result.issues[0].scope_basis == "mapped"
    assert not result.issues[0].global_scope


@pytest.mark.parametrize("kind", ["global", "unknown"])
def test_global_and_unknown_remain_blocked_and_distinguishable(data_and_flags, kind):
    spec, analysis, plan = data_and_flags
    review = ScopedPlanReview(findings=[finding(spec, kind)])
    result = assess_readiness(spec, analysis, plan, review)
    assert all(i.status == "blocked" for i in result.items)
    assert result.issues[0].scope_basis == kind


def test_legacy_empty_item_ids_are_not_reinterpreted_as_narrow_scope(data_and_flags):
    spec, analysis, plan = data_and_flags
    review = read_review(
        {
            "schema_version": "1.0",
            "findings": [
                {
                    "severity": "warning",
                    "target": "specification",
                    "item_ids": [],
                    "description": "Data settling unknown",
                }
            ],
        }
    )
    result = assess_readiness(spec, analysis, plan, review)
    assert all(i.status == "blocked" for i in result.items)
    assert result.issues[0].scope_basis == "unknown"


@pytest.mark.parametrize(
    "change",
    [
        lambda f: f["scope"].update(requirement_ids=["made-up"]),
        lambda f: f["scope"]["evidence"][0].update(source_id="made-up"),
        lambda f: f["scope"]["evidence"][0].update(quote="Not in this specification"),
        lambda f: f["scope"].update(requirement_ids=[]),
        lambda f: f["scope"].update(evidence=[]),
        lambda f: f["scope"].update(item_ids=["fill"]),
    ],
)
def test_invalid_scope_cannot_make_a_test_eligible(data_and_flags, change):
    spec, analysis, plan = data_and_flags
    row = finding(spec, requirement_ids=["DATA"])
    change(row)
    with pytest.raises(ValueError):
        review = ScopedPlanReview(findings=[row])
        assess_readiness(spec, analysis, plan, review)


def test_source_only_omission_does_not_require_an_invented_requirement(data_and_flags):
    spec, analysis, plan = data_and_flags
    row = finding(spec, "sources", source_ids=[spec.blocks[0].id])
    row.update(kind="omission", target="analysis", severity="error")
    review = ScopedPlanReview(findings=[row])
    assert review.needs_revision
    assert all(i.status == "blocked" for i in assess_readiness(spec, analysis, plan, review).items)
    # An entirely unrepresented source must not disappear through an empty mapping.
    missing = spec.blocks[0].model_copy(update={"id": "OMITTED", "text": "Reset is mandatory."})
    spec = spec.model_copy(update={"blocks": [*spec.blocks, missing]})
    row["scope"].update(
        source_ids=[missing.id], evidence=[{"source_id": missing.id, "quote": missing.text}]
    )
    review = ScopedPlanReview(findings=[row])
    result = assess_readiness(spec, analysis, plan, review)
    assert all(i.status == "blocked" for i in result.items)
    assert result.issues[0].scope_basis == "unknown"


def test_narrow_review_does_not_clear_independent_questions(data_and_flags):
    spec, analysis, plan = data_and_flags
    plan = plan.model_copy(
        update={
            "items": [
                *plan.items[:2],
                plan.items[2].model_copy(update={"open_questions": ["Clock unavailable"]}),
            ]
        }
    )
    review = ScopedPlanReview(findings=[finding(spec, requirement_ids=["DATA"])])
    assert all(i.status == "blocked" for i in assess_readiness(spec, analysis, plan, review).items)


def test_new_scope_constraints_survive_sdk_schema_transformation(data_and_flags):
    import jsonschema
    from agents.agent_output import AgentOutputSchema

    spec, _, _ = data_and_flags
    schema = AgentOutputSchema(ScopedPlanReview).json_schema()
    value = ScopedPlanReview(findings=[finding(spec, requirement_ids=["DATA"])]).model_dump()
    jsonschema.validate(value, schema)
    for key in ("requirement_ids", "evidence"):
        original = value["findings"][0]["scope"][key]
        value["findings"][0]["scope"][key] = []
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(value, schema)
        value["findings"][0]["scope"][key] = original


def test_unknown_review_version_is_rejected():
    with pytest.raises(ValueError):
        read_review({"schema_version": "99.0", "findings": []})
