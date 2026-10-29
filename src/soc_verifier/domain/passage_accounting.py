"""V3 accounts for evidence and dispositions at the same exact passage scope."""

from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Any, Literal

from pydantic import Field, create_model

from soc_verifier.domain.accounting import (
    AccountedObligation,
    AccountingReportBase,
    SourceSpan,
    UnitObligation,
    project_obligation,
    source_units,
)
from soc_verifier.domain.models import Contract, NonEmpty, SpecAnalysis, Specification


class PassageDisposition(Contract):
    evidence_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    status: Literal["non_normative", "unresolved"]
    reason: NonEmpty


class AccountedDisposition(Contract):
    evidence: Annotated[list[SourceSpan], Field(min_length=1)]
    status: Literal["non_normative", "unresolved"]
    reason: NonEmpty


class PassageAccountingDraft(Contract):
    format: Literal["source-accounting-draft-v3"] = "source-accounting-draft-v3"
    obligations: Annotated[list[UnitObligation], Field(min_length=1)]
    dispositions: list[PassageDisposition]
    gaps: list[str]


class PassageAccounting(AccountingReportBase):
    format: Literal["source-accounting-v3"] = "source-accounting-v3"
    dispositions: list[AccountedDisposition]


class AccountingIssue(Contract):
    code: Literal[
        "unknown_unit",
        "duplicate_obligation",
        "duplicate_evidence",
        "duplicate_disposition",
        "non_normative_evidence",
    ]
    location: str
    ids: list[str]
    description: str


class AccountingValidationError(ValueError):
    def __init__(self, issues: list[AccountingIssue]):
        self.issues = issues
        super().__init__(
            "Source accounting validation failed: " + ", ".join(i.code for i in issues)
        )

    @property
    def repairable(self) -> bool:
        return all(
            i.code in {"duplicate_disposition", "non_normative_evidence"} for i in self.issues
        )


def passage_accounting_schema(spec: Specification) -> type[PassageAccountingDraft]:
    units = source_units(spec)
    if not units:
        raise ValueError("Source accounting requires non-whitespace source passages")
    # Runtime source-specific enum types cannot be expressed as static aliases.
    enum_factory: Any = StrEnum
    identifiers: Any = enum_factory("SourceUnitID", {f"U{i}": u.id for i, u in enumerate(units)})
    obligation: Any = create_model(
        "PassageObligation",
        __base__=UnitObligation,
        evidence_ids=(list[identifiers], Field(min_length=1, max_length=12)),
    )
    disposition: Any = create_model(
        "BoundDisposition",
        __base__=PassageDisposition,
        evidence_ids=(list[identifiers], Field(min_length=1)),
    )
    return create_model(
        "PassageAccountingDraft",
        __base__=PassageAccountingDraft,
        obligations=(list[obligation], Field(min_length=1)),
        dispositions=(list[disposition], ...),
    )


def compile_passage_accounting(
    draft: PassageAccountingDraft, spec: Specification
) -> tuple[SpecAnalysis, list[AccountedObligation], list[AccountedDisposition], list[SourceSpan]]:
    units = {u.id: u for u in source_units(spec)}
    issues: list[AccountingIssue] = []

    def issue(code: Any, location: str, ids: list[str], description: str) -> None:
        issues.append(
            AccountingIssue(code=code, location=location, ids=ids, description=description)
        )

    used: set[str] = set()
    known_obligations: set[str] = set()
    for index, obligation in enumerate(draft.obligations):
        location = f"obligations[{index}]"
        if obligation.id in known_obligations:
            issue(
                "duplicate_obligation", location, [obligation.id], "Obligation IDs must be unique."
            )
        known_obligations.add(obligation.id)
        for identifier in obligation.evidence_ids:
            if identifier not in units:
                issue("unknown_unit", location, [identifier], "Use only supplied passage IDs.")
        if len(set(obligation.evidence_ids)) != len(obligation.evidence_ids):
            issue(
                "duplicate_evidence", location, obligation.evidence_ids, "Do not repeat evidence."
            )
        used.update(obligation.evidence_ids)
    disposed: set[str] = set()
    for index, disposition in enumerate(draft.dispositions):
        location = f"dispositions[{index}]"
        for identifier in disposition.evidence_ids:
            if identifier not in units:
                issue("unknown_unit", location, [identifier], "Use only supplied passage IDs.")
            if identifier in disposed:
                issue(
                    "duplicate_disposition",
                    location,
                    [identifier],
                    "Assign at most one disposition per passage.",
                )
            if disposition.status == "non_normative" and identifier in used:
                issue(
                    "non_normative_evidence",
                    location,
                    [identifier],
                    "An evidence passage cannot also be discarded as non-normative.",
                )
            disposed.add(identifier)
    if issues:
        raise AccountingValidationError(issues)
    blocks = {b.id: b for b in spec.blocks}
    spans = {
        key: SourceSpan(
            block_id=u.block_id,
            text_sha256=sha256(blocks[u.block_id].text.encode()).hexdigest(),
            start=u.start,
            end=u.end,
        )
        for key, u in units.items()
    }
    obligations = [
        AccountedObligation(
            **o.model_dump(exclude={"evidence_ids"}), evidence=[spans[k] for k in o.evidence_ids]
        )
        for o in draft.obligations
    ]
    dispositions = [
        AccountedDisposition(
            evidence=[spans[k] for k in d.evidence_ids], status=d.status, reason=d.reason
        )
        for d in draft.dispositions
    ]
    missing = [span for key, span in spans.items() if key not in used | disposed]
    gaps = list(draft.gaps)
    for disposition in draft.dispositions:
        if disposition.status == "unresolved":
            gaps.append(
                f"Source accounting unresolved ({', '.join(disposition.evidence_ids)}): "
                + disposition.reason
            )
    if missing:
        gaps.append(
            "Source accounting has unaccounted text in: "
            + ", ".join(dict.fromkeys(s.block_id for s in missing))
            + ". No completeness claim is established."
        )
    return (
        SpecAnalysis(requirements=[project_obligation(o) for o in obligations], gaps=gaps),
        obligations,
        dispositions,
        missing,
    )
