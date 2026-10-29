"""Evidence-bound, provisional extraction findings; no automated semantic approval."""

from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import Field, create_model, model_validator

from soc_verifier.domain.accounting import source_units
from soc_verifier.domain.models import Contract, NonEmpty, SpecAnalysis, Specification


class ConflictComparison(Contract):
    subject: NonEmpty
    conditions: NonEmpty
    left_evidence_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    right_evidence_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    incompatibility: NonEmpty


class SourceFinding(Contract):
    id: NonEmpty
    kind: Literal[
        "omission", "lost_qualifier", "unsupported_claim", "source_conflict", "unresolved_context"
    ]
    requirement_ids: list[NonEmpty]
    evidence_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    description: NonEmpty
    recommended_action: NonEmpty
    conflict: ConflictComparison | None

    @model_validator(mode="after")
    def finding_scope(self) -> Self:
        if (self.kind == "source_conflict") != (self.conflict is not None):
            raise ValueError("Only source conflicts require a two-sided comparison")
        if self.kind in {"lost_qualifier", "unsupported_claim"} and not self.requirement_ids:
            raise ValueError("A claim defect must identify affected requirements")
        return self


class KnowledgeApplication(Contract):
    entry_id: NonEmpty
    requirement_ids: list[NonEmpty]
    evidence_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    assessment: Literal["applicable", "not_applicable", "uncertain"]
    rationale: NonEmpty


class SourceAudit(Contract):
    format: Literal["source-audit-v1"] = "source-audit-v1"
    judgment_state: Literal["agent_proposed"] = "agent_proposed"
    findings: list[SourceFinding]
    knowledge_applications: list[KnowledgeApplication]


def bound_audit_schema(spec: Specification, analysis: SpecAnalysis) -> type[SourceAudit]:
    """Prevent block IDs and invented targets in every model-selected reference."""
    units = source_units(spec)
    if not units:
        raise ValueError("Source audit requires non-whitespace passages")
    factory: Any = StrEnum
    passage: Any = factory("AuditPassageID", {f"P{i}": u.id for i, u in enumerate(units)})
    requirement: Any = factory(
        "AuditRequirementID", {f"R{i}": r.id for i, r in enumerate(analysis.requirements)}
    )
    comparison: Any = create_model(
        "BoundConflictComparison",
        __base__=ConflictComparison,
        left_evidence_ids=(list[passage], Field(min_length=1)),
        right_evidence_ids=(list[passage], Field(min_length=1)),
    )
    finding: Any = create_model(
        "BoundSourceFinding",
        __base__=SourceFinding,
        requirement_ids=(list[requirement], ...),
        evidence_ids=(list[passage], Field(min_length=1)),
        conflict=(comparison | None, ...),
    )
    application: Any = create_model(
        "BoundKnowledgeApplication",
        __base__=KnowledgeApplication,
        requirement_ids=(list[requirement], ...),
        evidence_ids=(list[passage], Field(min_length=1)),
    )
    return create_model(
        "SourceAudit",
        __base__=SourceAudit,
        findings=(list[finding], ...),
        knowledge_applications=(list[application], ...),
    )


def validate_source_audit(
    audit: SourceAudit,
    spec: Specification,
    analysis: SpecAnalysis,
    *,
    known_knowledge: set[str],
    read_knowledge: set[str],
) -> None:
    units = {u.id for u in source_units(spec)}
    requirements = {r.id for r in analysis.requirements}
    if len({f.id for f in audit.findings}) != len(audit.findings):
        raise ValueError("Duplicate source audit finding IDs")
    if len({a.entry_id for a in audit.knowledge_applications}) != len(audit.knowledge_applications):
        raise ValueError("Duplicate knowledge application IDs")
    rows: list[SourceFinding | KnowledgeApplication] = [
        *audit.findings,
        *audit.knowledge_applications,
    ]
    for row in rows:
        if not set(row.requirement_ids) <= requirements or not set(row.evidence_ids) <= units:
            raise ValueError("Source audit cites unknown requirements or passages")
    for finding in audit.findings:
        comparison = finding.conflict
        if comparison is not None:
            left, right = set(comparison.left_evidence_ids), set(comparison.right_evidence_ids)
            if not (left | right) <= set(finding.evidence_ids) or left & right:
                raise ValueError("Conflict requires two distinct cited source passages")
    if not {a.entry_id for a in audit.knowledge_applications} <= known_knowledge & read_knowledge:
        raise ValueError(
            "Knowledge applications must cite entries actually read by this audit task"
        )
