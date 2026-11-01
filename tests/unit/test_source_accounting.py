from hashlib import sha256

import pytest
from pydantic import ValidationError

from soc_verifier.domain.accounting import (
    AccountingDraft,
    SourceAccounting,
    SourceDisposition,
    SourceQuote,
    UnitAccountingDraft,
    bound_accounting_schema,
    compile_accounting,
    compile_unit_accounting,
    source_units,
)


def test_structured_facts_survive_projection(specification, accounting_draft):
    obligation = accounting_draft.obligations[0].model_copy(
        update={
            "constraints": ["Eight interrupt bits; level-sensitive"],
            "exceptions": ["Wake state is retained"],
        }
    )
    draft = accounting_draft.model_copy(update={"obligations": [obligation]})
    analysis, facts, missing = compile_accounting(draft, specification)
    text = analysis.requirements[0].statement
    assert all(
        value in text
        for value in obligation.conditions + obligation.constraints + obligation.exceptions
    )
    assert facts[0].constraints == obligation.constraints
    assert missing == []
    # This is lossless projection, not proof that the model's added claims are supported.


def test_unicode_occurrences_and_unaccounted_text_are_exact(specification, accounting_draft):
    text = "ß🙂\tRESET\r\nRESET; pending clears."
    spec = specification.model_copy(
        update={"blocks": [specification.blocks[0].model_copy(update={"text": text})]}
    )
    draft = accounting_draft.model_copy(
        update={
            "obligations": [
                accounting_draft.obligations[0].model_copy(
                    update={
                        "evidence": [SourceQuote(block_id="P00001", quote="RESET", occurrence=1)]
                    }
                )
            ]
        }
    )
    analysis, facts, missing = compile_accounting(draft, spec)
    span = facts[0].evidence[0]
    assert (span.start, span.end) == (10, 15)
    assert span.text_sha256 == sha256(text.encode()).hexdigest()
    assert [text[s.start : s.end] for s in missing] == ["ß🙂\tRESET\r\n", "; pending clears."]
    assert "unaccounted" in analysis.gaps[0]


@pytest.mark.parametrize(
    "reference",
    [
        SourceQuote(block_id="made-up", quote="reset", occurrence=0),
        SourceQuote(block_id="P00001", quote="fabricated text", occurrence=0),
        SourceQuote(block_id="P00001", quote="System reset", occurrence=1),
        SourceQuote(block_id="P00001", quote=" ", occurrence=0),
    ],
)
def test_invalid_evidence_fails(specification, accounting_draft, reference):
    draft = accounting_draft.model_copy(
        update={
            "obligations": [
                accounting_draft.obligations[0].model_copy(update={"evidence": [reference]})
            ]
        }
    )
    with pytest.raises(ValueError):
        compile_accounting(draft, specification)


@pytest.mark.parametrize(
    "dispositions",
    [
        [SourceDisposition(source_ids=["made-up"], status="unresolved", reason="unknown")],
        [SourceDisposition(source_ids=["P00001"], status="non_normative", reason="header")],
        [SourceDisposition(source_ids=["P00001", "P00001"], status="unresolved", reason="unknown")],
    ],
)
def test_inconsistent_dispositions_fail(specification, accounting_draft, dispositions):
    with pytest.raises(ValueError):
        compile_accounting(
            accounting_draft.model_copy(update={"dispositions": dispositions}), specification
        )


def test_unquoted_and_unresolved_blocks_cannot_disappear(specification, accounting_draft):
    other = specification.blocks[0].model_copy(update={"id": "P00002", "text": "Timing TBD."})
    spec = specification.model_copy(update={"blocks": [*specification.blocks, other]})
    analysis, _, missing = compile_accounting(accounting_draft, spec)
    assert [span.block_id for span in missing] == ["P00002"]
    assert "P00002" in analysis.gaps[0]
    declared = accounting_draft.model_copy(
        update={
            "dispositions": [
                SourceDisposition(
                    source_ids=["P00002"], status="unresolved", reason="Timing not defined"
                )
            ]
        }
    )
    analysis, _, missing = compile_accounting(declared, spec)
    assert not missing
    assert "Timing not defined" in analysis.gaps[0]


def test_duplicate_obligations_and_unknown_formats_fail(accounting_draft):
    data = accounting_draft.model_dump()
    data["obligations"] *= 2
    with pytest.raises(ValidationError, match="Duplicate"):
        AccountingDraft.model_validate(data)
    data = accounting_draft.model_dump()
    data["format"] = "source-accounting-draft-v999"
    with pytest.raises(ValidationError):
        AccountingDraft.model_validate(data)
    with pytest.raises(ValidationError):
        SourceAccounting.model_validate({"format": "source-accounting-v999"})


def test_source_unit_selection_copies_unicode_and_repeated_text_exactly(
    specification, unit_accounting_draft
):
    text = "DM\u2019s reset → output.\r\nDM\u2019s reset → output.\nThe width is 8."
    spec = specification.model_copy(
        update={"blocks": [specification.blocks[0].model_copy(update={"text": text})]}
    )
    units = source_units(spec)
    assert [u.text for u in units] == [
        "DM\u2019s reset → output.",
        "DM\u2019s reset → output.",
        "The width is 8.",
    ]
    chosen = units[1]
    draft = unit_accounting_draft.model_copy(
        update={
            "obligations": [
                unit_accounting_draft.obligations[0].model_copy(
                    update={"evidence_ids": [chosen.id]}
                )
            ]
        }
    )
    analysis, facts, missing = compile_unit_accounting(draft, spec)
    span = facts[0].evidence[0]
    assert (span.start, span.end) == (chosen.start, chosen.end)
    assert text[span.start : span.end] == chosen.text
    assert [text[s.start : s.end] for s in missing] == [
        "DM\u2019s reset → output.\r\n",
        "\nThe width is 8.",
    ]
    assert analysis.gaps


def test_bound_schema_restricts_evidence_to_actual_source_units(
    specification, unit_accounting_draft
):
    schema = bound_accounting_schema(specification)
    parsed = schema.model_validate(unit_accounting_draft.model_dump())
    compile_unit_accounting(parsed, specification)
    data = unit_accounting_draft.model_dump()
    data["obligations"][0]["evidence_ids"] = ["P00001:U99999"]
    with pytest.raises(ValidationError):
        schema.model_validate(data)
    with pytest.raises(ValueError, match="unknown source unit"):
        compile_unit_accounting(UnitAccountingDraft.model_validate(data), specification)
    data["obligations"][0]["evidence_ids"] = [source_units(specification)[0].id] * 2
    with pytest.raises(ValueError, match="Repeated"):
        compile_unit_accounting(UnitAccountingDraft.model_validate(data), specification)


def test_table_rows_remain_whole_source_units(specification):
    text = "Port | Width | Meaning\nreq_i | 8 | Request. Must remain stable."
    spec = specification.model_copy(
        update={
            "blocks": [
                specification.blocks[0].model_copy(update={"kind": "table_row", "text": text})
            ]
        }
    )
    units = source_units(spec)
    assert len(units) == 1 and units[0].text == text


def test_v1_accounting_still_reads_without_migration(tmp_path, specification, accounting_draft):
    from soc_verifier.storage.artifacts import ArtifactStore
    from soc_verifier.workflows.spec_to_plan.accounting import project_accounting, read_accounting

    artifacts = ArtifactStore(tmp_path)
    artifacts.write("specification.json", specification)
    artifacts.write("obligations.r000.json", accounting_draft)
    analysis, report = project_accounting(artifacts, "obligations.r000.json", "analysis.json")
    artifacts.write("analysis.json", analysis)
    artifacts.write("source-accounting.r000.json", report)
    assert (
        read_accounting(artifacts, "source-accounting.r000.json").format == "source-accounting-v1"
    )
