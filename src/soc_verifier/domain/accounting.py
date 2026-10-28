"""Source accounting is inspectable extraction evidence, not semantic approval."""

from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

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
    format: Literal["source-accounting-v1"] = "source-accounting-v1"
    specification_sha256: Digest
    analysis_artifact: NonEmpty
    analysis_sha256: Digest
    extraction_artifact: NonEmpty
    extraction_sha256: Digest
    obligations: list[AccountedObligation]
    dispositions: list[SourceDisposition]
    unaccounted: list[SourceSpan]
    semantic_acceptance: Literal["unreviewed"] = "unreviewed"


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
