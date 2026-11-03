"""Global execution claims need complete, inspectable scenario dependencies."""

import copy

import pytest

from soc_verifier.domain.readiness import assess_readiness, permits_experimental_attempt
from soc_verifier.domain.review import ScopedPlanReview, read_review, validate_review_context


@pytest.fixture
def two_items(verification_plan):
    first = verification_plan.items[0]
    return verification_plan.model_copy(
        update={"items": [first, first.model_copy(update={"id": "SECOND"})]}
    )


def global_finding(specification, plan, *, accounted=True):
    scope = {
        "kind": "global",
        "rationale": "Every scenario exercises reset before observing pending interrupts.",
        "evidence": [{"source_id": "P00001", "quote": specification.blocks[0].text}],
    }
    if accounted:
        scope["dependencies"] = [
            {
                "plan_item_id": item.id,
                "plan_field": "stimulus",
                "plan_quote": item.stimulus[0],
                "evidence_indices": [0],
                "rationale": "This reset stimulus depends on the unresolved reset definition.",
            }
            for item in plan.items
        ]
    return {
        "severity": "warning",
        "target": "specification",
        "kind": "timing",
        "description": "The reset sampling definition needs clarification.",
        "recommended_action": "Resolve reset timing with the owner.",
        "scope": scope,
    }


def test_unaccounted_global_label_is_not_a_valid_new_review(specification, two_items):
    # The old free-form label accepted this explicitly local explanation as global.
    row = global_finding(specification, two_items, accounted=False)
    row["scope"]["rationale"] = (
        "Only SECOND needs this observation; the first scenario is independent."
    )
    with pytest.raises(ValueError, match="dependencies"):
        ScopedPlanReview(findings=[row])


def test_partial_accounting_cannot_block_every_scenario(specification, analysis, two_items):
    row = global_finding(specification, two_items)
    row["scope"]["dependencies"] = row["scope"]["dependencies"][1:]
    review = ScopedPlanReview(findings=[row])
    with pytest.raises(ValueError, match="Global dependencies must cover every plan item"):
        assess_readiness(specification, analysis, two_items, review)


@pytest.mark.parametrize(
    "change,match",
    [
        (lambda d: d.update(plan_item_id="invented"), "every plan item"),
        (lambda d: d.update(plan_item_id="SECOND"), "exactly once"),
        (lambda d: d.update(plan_quote="A fabricated reset step"), "plan field"),
        (lambda d: d.update(plan_field="expected_results"), "plan field"),
        (lambda d: d.update(evidence_indices=[99]), "evidence index"),
        (lambda d: d.update(evidence_indices=[]), "evidence_indices"),
        (lambda d: d.update(evidence_indices=[0, 0]), "Duplicate"),
    ],
)
def test_fabricated_dependency_cannot_authorize_global_scope(
    specification, analysis, two_items, change, match
):
    row = global_finding(specification, two_items)
    change(row["scope"]["dependencies"][0])
    with pytest.raises(ValueError, match=match):
        review = ScopedPlanReview(findings=[row])
        assess_readiness(specification, analysis, two_items, review)


def test_accounted_shared_setup_still_blocks_every_scenario(specification, analysis, two_items):
    review = ScopedPlanReview(findings=[global_finding(specification, two_items)])
    result = assess_readiness(specification, analysis, two_items, review)
    assert review.schema_version == "4.0"
    assert all(item.status == "blocked" for item in result.items)
    assert result.issues[0].scope_basis == "global"
    assert not permits_experimental_attempt(result.issues)
    assert not result.human_approved


def test_unsupported_local_observation_does_not_block_independent_simulation(
    specification, analysis, two_items
):
    plan = two_items.model_copy(
        update={
            "items": [
                two_items.items[0],
                two_items.items[1].model_copy(update={"method": "inspection"}),
            ]
        }
    )
    row = global_finding(specification, plan, accounted=False)
    row.update(target="plan", kind="execution_binding")
    row["scope"].update(kind="items", item_ids=["SECOND"])
    row["scope"]["rationale"] = "Only the inspection needs an internal observation."
    result = assess_readiness(specification, analysis, plan, ScopedPlanReview(findings=[row]))
    assert [item.status for item in result.items] == ["eligible", "unsupported"]
    assert result.issues[0].item_ids == ["SECOND"]


@pytest.mark.parametrize("version", ["2.0", "3.0"])
def test_historical_global_flags_keep_their_original_decisions(
    specification, analysis, two_items, version
):
    data = {
        "schema_version": version,
        "findings": [global_finding(specification, two_items, accounted=False)],
    }
    if version == "3.0":
        data["acceptance_notes"] = []
    review = read_review(data)
    before = review.model_dump()
    result = assess_readiness(specification, analysis, two_items, review)
    assert all(item.status == "blocked" for item in result.items)
    assert review.model_dump() == before
    assert "dependencies" not in before["findings"][0]["scope"]


def test_global_dependency_contract_reaches_provider_schema(specification, analysis, two_items):
    import jsonschema
    from agents.agent_output import AgentOutputSchema

    from soc_verifier.providers.openrouter import _strict_schema

    schema = _strict_schema(copy.deepcopy(AgentOutputSchema(ScopedPlanReview).json_schema()))
    review = ScopedPlanReview(findings=[global_finding(specification, two_items)])
    valid = review.model_dump()
    jsonschema.validate(valid, schema)
    validate_review_context(review, specification, analysis, two_items)
    for change in (lambda s: s.pop("dependencies"), lambda s: s.update(dependencies=[])):
        value = copy.deepcopy(valid)
        change(value["findings"][0]["scope"])
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(value, schema)
