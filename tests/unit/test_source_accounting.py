from hashlib import sha256

import pytest
from pydantic import ValidationError

from soc_verifier.domain.accounting import (
    AccountingDraft,
    SourceAccounting,
    SourceDisposition,
    SourceQuote,
    compile_accounting,
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
