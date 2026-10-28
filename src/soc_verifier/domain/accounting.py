"""Source accounting is inspectable extraction evidence, not semantic approval."""

import re
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Any, Literal, Self

from pydantic import Field, create_model, model_validator

from soc_verifier.domain.models import Contract, NonEmpty, Requirement, SpecAnalysis, Specification

Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class SourceQuote(Contract):
    block_id: NonEmpty
    quote: Annotated[str, Field(min_length=1, max_length=4000)]
    occurrence: int = Field(ge=0)


class SourceSpan(Contract):
    block_id: NonEmpty
    text_sha256: Digest
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class ObligationFacts(Contract):
    id: NonEmpty
    statement: NonEmpty
    feature: NonEmpty
    basis: Literal["explicit", "derived"]
    conditions: list[NonEmpty]
    constraints: list[NonEmpty]
    exceptions: list[NonEmpty]
    rationale: str
    open_questions: list[str]


class DraftObligation(ObligationFacts):
    evidence: Annotated[list[SourceQuote], Field(min_length=1, max_length=12)]


class AccountedObligation(ObligationFacts):
    evidence: Annotated[list[SourceSpan], Field(min_length=1)]


class SourceDisposition(Contract):
    source_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    status: Literal["non_normative", "unresolved"]
    reason: NonEmpty


class AccountingDraft(Contract):
    format: Literal["source-accounting-draft-v1"] = "source-accounting-draft-v1"
    obligations: Annotated[list[DraftObligation], Field(min_length=1)]
    dispositions: list[SourceDisposition]
    gaps: list[str]

    @model_validator(mode="after")
    def unique_ids(self) -> Self:
        if len({r.id for r in self.obligations}) != len(self.obligations):
            raise ValueError("Duplicate obligation IDs")
        return self


class SourceAccounting(Contract):
    format: Literal["source-accounting-v1", "source-accounting-v2"] = "source-accounting-v1"
    specification_sha256: Digest
    analysis_artifact: NonEmpty
    analysis_sha256: Digest
    extraction_artifact: NonEmpty
    extraction_sha256: Digest
    obligations: list[AccountedObligation]
    dispositions: list[SourceDisposition]
    unaccounted: list[SourceSpan]
    semantic_acceptance: Literal["unreviewed"] = "unreviewed"


class SourceUnit(Contract):
    id: NonEmpty
    block_id: NonEmpty
    text: NonEmpty
    start: int
    end: int


class UnitObligation(ObligationFacts):
    evidence_ids: Annotated[list[NonEmpty], Field(min_length=1, max_length=12)]


class UnitAccountingDraft(Contract):
    format: Literal["source-accounting-draft-v2"] = "source-accounting-draft-v2"
    obligations: Annotated[list[UnitObligation], Field(min_length=1)]
    dispositions: list[SourceDisposition]
    gaps: list[str]

    @model_validator(mode="after")
    def unique_ids(self) -> Self:
        if len({r.id for r in self.obligations}) != len(self.obligations):
            raise ValueError("Duplicate obligation IDs")
        return self


def source_units(spec: Specification) -> list[SourceUnit]:
    """Mechanical sentence/line boundaries, never a normative or semantic classifier."""
    units = []
    for block in spec.blocks:
        ends = (
            [match.end() for match in re.finditer(r"(?:[.!?](?=\s)|\r\n|\r|\n)", block.text)]
            if block.kind == "paragraph"
            else []
        )
        start = 0
        for end in sorted({*ends, len(block.text)}):
            if block.text[start:end].strip():
                units.append(
                    SourceUnit(
                        id=f"{block.id}:U{start:05d}",
                        block_id=block.id,
                        text=block.text[start:end],
                        start=start,
                        end=end,
                    )
                )
            start = end
    return units


def bound_accounting_schema(spec: Specification) -> type[UnitAccountingDraft]:
    """Constrain model choices to actual passages; source text is copied by Python."""
    # Dynamic source-specific classes cannot be expressed as static Python type aliases.
    enum_factory: Any = StrEnum
    identifiers: Any = enum_factory(
        "SourceUnitID", {f"U{i}": u.id for i, u in enumerate(source_units(spec))}
    )
    obligation: Any = create_model(
        "BoundObligation",
        __base__=UnitObligation,
        evidence_ids=(list[identifiers], Field(min_length=1, max_length=12)),
    )
    return create_model(
        "UnitAccountingDraft",
        __base__=UnitAccountingDraft,
        obligations=(list[obligation], Field(min_length=1)),
    )


def compile_unit_accounting(
    draft: UnitAccountingDraft, spec: Specification
) -> tuple[SpecAnalysis, list[AccountedObligation], list[SourceSpan]]:
    units = {unit.id: unit for unit in source_units(spec)}
    blocks = {block.id: block for block in spec.blocks}
    obligations = []
    for obligation in draft.obligations:
        references = []
        if len(set(obligation.evidence_ids)) != len(obligation.evidence_ids):
            raise ValueError("Repeated source unit in obligation evidence")
        for identifier in obligation.evidence_ids:
            if identifier not in units:
                raise ValueError("Accounting cites an unknown source unit")
            unit = units[identifier]
            # Preserve exact occurrence even when identical sentences repeat.
            text = blocks[unit.block_id].text
            position = text.find(unit.text)
            occurrence = 0
            while position < unit.start:
                position = text.find(unit.text, position + 1)
                occurrence += 1
            references.append(
                SourceQuote(block_id=unit.block_id, quote=unit.text, occurrence=occurrence)
            )
        obligations.append(
            DraftObligation(**obligation.model_dump(exclude={"evidence_ids"}), evidence=references)
        )
    return compile_accounting(
        AccountingDraft(obligations=obligations, dispositions=draft.dispositions, gaps=draft.gaps),
        spec,
    )


def compile_accounting(
    draft: AccountingDraft, spec: Specification
) -> tuple[SpecAnalysis, list[AccountedObligation], list[SourceSpan]]:
    """Resolve exact quotations; preserve all structured facts without another model."""
    blocks = {block.id: block for block in spec.blocks}
    spans: dict[str, list[tuple[int, int]]] = {key: [] for key in blocks}
    obligations = []
    requirements = []
    for obligation in draft.obligations:
        evidence = []
        for reference in obligation.evidence:
            if reference.block_id not in blocks:
                raise ValueError("Accounting cites an unknown source block")
            text = blocks[reference.block_id].text
            start = -1
            for _ in range(reference.occurrence + 1):
                start = text.find(reference.quote, start + 1)
                if start < 0:
                    raise ValueError("Accounting quotation does not match exact source text")
            if not reference.quote.strip():
                raise ValueError("Accounting quotation contains only whitespace")
            end = start + len(reference.quote)
            evidence.append(
                SourceSpan(
                    block_id=reference.block_id,
                    text_sha256=sha256(text.encode()).hexdigest(),
                    start=start,
                    end=end,
                )
            )
            spans[reference.block_id].append((start, end))
        facts = obligation.model_dump(exclude={"evidence"})
        obligations.append(AccountedObligation(**facts, evidence=evidence))
        statement = [obligation.statement]
        for label, values in (
            ("Conditions", obligation.conditions),
            ("Constraints", obligation.constraints),
            ("Exceptions", obligation.exceptions),
        ):
            if values:
                statement.append(f"{label}: " + "; ".join(values))
        requirements.append(
            Requirement(
                id=obligation.id,
                statement="\n".join(statement),
                feature=obligation.feature,
                basis=obligation.basis,
                source_ids=list(dict.fromkeys(s.block_id for s in evidence)),
                rationale=obligation.rationale,
                open_questions=obligation.open_questions,
            )
        )
    disposed: set[str] = set()
    gaps = list(draft.gaps)
    for disposition in draft.dispositions:
        for identifier in disposition.source_ids:
            if identifier not in blocks or identifier in disposed:
                raise ValueError("Unknown or repeated source disposition")
            if disposition.status == "non_normative" and spans[identifier]:
                raise ValueError("Non-normative disposition overlaps obligation evidence")
            disposed.add(identifier)
        if disposition.status == "unresolved":
            gaps.append(
                f"Source accounting unresolved ({', '.join(disposition.source_ids)}): "
                + disposition.reason
            )
    unaccounted = []
    for block in spec.blocks:
        if block.id in disposed:
            continue
        cursor = 0
        for start, end in [*sorted(spans[block.id]), (len(block.text), len(block.text))]:
            if cursor < start and block.text[cursor:start].strip():
                unaccounted.append(
                    SourceSpan(
                        block_id=block.id,
                        text_sha256=sha256(block.text.encode()).hexdigest(),
                        start=cursor,
                        end=start,
                    )
                )
            cursor = max(cursor, end)
    if unaccounted:
        gaps.append(
            "Source accounting has unaccounted text in: "
            + ", ".join(dict.fromkeys(span.block_id for span in unaccounted))
            + ". No completeness claim is established."
        )
    return SpecAnalysis(requirements=requirements, gaps=gaps), obligations, unaccounted
