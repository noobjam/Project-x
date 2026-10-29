import pytest
from pydantic import ValidationError

from soc_verifier.domain.accounting import source_units
from soc_verifier.domain.passage_accounting import (
    AccountingValidationError,
    PassageDisposition,
    compile_passage_accounting,
    passage_accounting_schema,
)
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.accounting import project_accounting, read_accounting


def test_mixed_paragraph_can_keep_behavior_and_dispose_only_reference(
    specification, passage_accounting_draft
):
    text = specification.blocks[0].text + " See the separate bus guide."
    spec = specification.model_copy(
        update={"blocks": [specification.blocks[0].model_copy(update={"text": text})]}
    )
    units = source_units(spec)
    assert len(units) == 2
    draft = passage_accounting_draft.model_copy(
        update={
            "dispositions": [
                PassageDisposition(
                    evidence_ids=[units[1].id], status="non_normative", reason="Reference only"
                )
            ]
        }
    )
    analysis, obligations, dispositions, missing = compile_passage_accounting(draft, spec)
    assert not missing and not analysis.gaps
    assert analysis.requirements[0].source_ids == ["P00001"]
    assert obligations[0].evidence[0].end == len(specification.blocks[0].text)
    span = dispositions[0].evidence[0]
    assert text[span.start : span.end] == " See the separate bus guide."
    # Omitting the disposition leaves precisely that passage visible.
    _, _, _, missing = compile_passage_accounting(passage_accounting_draft, spec)
    assert missing == [span]


@pytest.mark.parametrize("status", ["non_normative", "unresolved"])
def test_disposition_overlap_has_explicit_feedback_or_visible_uncertainty(
    specification, passage_accounting_draft, status
):
    key = source_units(specification)[0].id
    draft = passage_accounting_draft.model_copy(
        update={
            "dispositions": [
                PassageDisposition(
                    evidence_ids=[key], status=status, reason="Missing implementation detail"
                )
            ]
        }
    )
    if status == "non_normative":
        with pytest.raises(AccountingValidationError) as error:
            compile_passage_accounting(draft, specification)
        assert error.value.repairable
        assert error.value.issues[0].ids == [key]
        assert error.value.issues[0].location == "dispositions[0]"
    else:
        analysis, _, _, missing = compile_passage_accounting(draft, specification)
        assert not missing
        assert "Missing implementation detail" in analysis.gaps[0]


def test_unknown_units_and_duplicate_obligations_are_not_disposition_repairs(
    specification, passage_accounting_draft
):
    bad = passage_accounting_draft.model_copy(
        update={
            "dispositions": [
                PassageDisposition(evidence_ids=["invented"], status="unresolved", reason="Unknown")
            ]
        }
    )
    with pytest.raises(AccountingValidationError) as error:
        compile_passage_accounting(bad, specification)
    assert not error.value.repairable
    with pytest.raises(ValidationError):
        passage_accounting_schema(specification).model_validate(bad.model_dump())
    bad = passage_accounting_draft.model_copy(
        update={"obligations": passage_accounting_draft.obligations * 2}
    )
    with pytest.raises(AccountingValidationError) as error:
        compile_passage_accounting(bad, specification)
    assert not error.value.repairable


def test_long_unicode_passage_copied_without_model_quote_limits(
    specification, passage_accounting_draft
):
    text = "🙂→" * 2500
    spec = specification.model_copy(
        update={"blocks": [specification.blocks[0].model_copy(update={"text": text})]}
    )
    _, obligations, _, missing = compile_passage_accounting(passage_accounting_draft, spec)
    span = obligations[0].evidence[0]
    assert text[span.start : span.end] == text and not missing
    empty = spec.model_copy(update={"blocks": [spec.blocks[0].model_copy(update={"text": " \n "})]})
    with pytest.raises(ValueError, match="non-whitespace"):
        passage_accounting_schema(empty)


@pytest.mark.parametrize(
    "fixture, version",
    [
        ("accounting_draft", "v1"),
        ("unit_accounting_draft", "v2"),
        ("passage_accounting_draft", "v3"),
    ],
)
def test_all_accounting_formats_still_project_and_read(
    tmp_path, specification, request, fixture, version
):
    store = ArtifactStore(tmp_path)
    store.write("specification.json", specification)
    store.write("obligations.json", request.getfixturevalue(fixture))
    analysis, report = project_accounting(store, "obligations.json", "analysis.json")
    store.write("analysis.json", analysis)
    store.write("accounting.json", report)
    assert read_accounting(store, "accounting.json").format == f"source-accounting-{version}"
