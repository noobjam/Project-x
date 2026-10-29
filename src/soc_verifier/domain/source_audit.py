"""Evidence-bound, provisional extraction findings; no automated semantic approval."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

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
