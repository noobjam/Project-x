"""Conservative, item-scoped execution decisions without rewriting planning evidence."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from soc_verifier.domain.models import (
    Contract,
    NonEmpty,
    ReviewFinding,
    SpecAnalysis,
    Specification,
    VerificationPlan,
    validate_sources,
    validate_traceability,
)
from soc_verifier.domain.review import (
    Review,
    ScopedReviewFinding,
    review_impact,
    validate_review_context,
)
from soc_verifier.domain.source_audit import SourceAudit


class GapEvidence(Contract):
    source_id: NonEmpty
    quote: Annotated[str, Field(min_length=1, max_length=6_000)]


class GapScope(Contract):
    gap_index: Annotated[int, Field(strict=True, ge=0)]
    disposition: Literal["block_global", "block_requirements", "note"]
    requirement_ids: list[NonEmpty]
    note_kind: Literal["declared_exclusion", "specified_behavior", "execution_convention"] | None
    evidence: list[GapEvidence]
    rationale: NonEmpty

    @model_validator(mode="after")
    def scope(self) -> Self:
        if len(self.requirement_ids) != len(set(self.requirement_ids)):
            raise ValueError("Duplicate gap requirement IDs")
        if (self.disposition == "block_requirements") != bool(self.requirement_ids):
            raise ValueError("Only a requirement-scoped blocker identifies requirements")
        if (self.disposition == "note") != (self.note_kind is not None):
            raise ValueError("Nonblocking gap notes require an explicit note kind")
        if self.disposition != "block_global" and not self.evidence:
            raise ValueError("Narrowing a gap requires source evidence")
        return self


class GapAssessment(Contract):
    format: Literal["execution-gap-assessment-v1"] = "execution-gap-assessment-v1"
    judgment_state: Literal["agent_proposed"] = "agent_proposed"
    gaps: list[GapScope]

    def validate_context(self, spec: Specification, analysis: SpecAnalysis) -> None:
        indexes = [gap.gap_index for gap in self.gaps]
        if sorted(indexes) != list(range(len(analysis.gaps))):
            raise ValueError("Assess every analysis gap exactly once")
        requirements = {r.id for r in analysis.requirements}
        sources = {b.id: b.text for b in spec.blocks}
        for gap in self.gaps:
            if set(gap.requirement_ids) - requirements:
                raise ValueError("Gap scope cites unknown requirement IDs")
            for evidence in gap.evidence:
                if (
                    evidence.source_id not in sources
                    or evidence.quote not in sources[evidence.source_id]
                ):
                    raise ValueError("Gap evidence must quote an existing source block exactly")


class ExecutionIssue(Contract):
    id: NonEmpty
    kind: Literal[
        "review",
        "item_question",
        "requirement_question",
        "analysis_gap",
        "extraction_warning",
        "source_audit",
        "knowledge_uncertainty",
    ]
    description: str
    blocking: bool
    global_scope: bool
    item_ids: list[str]
    origin: NonEmpty
    scope_basis: Literal["mapped", "global", "unknown"] | None = None


class ItemReadiness(Contract):
    plan_item_id: NonEmpty
    status: Literal["eligible", "blocked", "unsupported"]
    issue_ids: list[str]


class ExecutionReadiness(Contract):
    format: Literal["execution-readiness-v1", "execution-readiness-v2"] = "execution-readiness-v2"
    items: list[ItemReadiness]
    issues: list[ExecutionIssue]
    human_approved: Literal[False] = False


def permits_experimental_attempt(issues: list[ExecutionIssue]) -> bool:
    """Permit case-level investigation, without changing any original blocking decision."""
    return all(
        issue.kind == "analysis_gap" or (issue.kind == "review" and issue.scope_basis == "unknown")
        for issue in issues
    )


def assess_readiness(
    spec: Specification,
    analysis: SpecAnalysis,
    plan: VerificationPlan,
    review: Review,
    *,
    gap_assessment: GapAssessment | None = None,
    source_audit: SourceAudit | None = None,
) -> ExecutionReadiness:
    """Eligibility permits binding, not execution without a validated testbench proposal."""
    validate_sources(analysis, spec)
    validate_traceability(plan, analysis)
    validate_review_context(review, spec, analysis, plan)
    items = {item.id: item for item in plan.items}
    requirements = {r.id for r in analysis.requirements}
    issues: list[ExecutionIssue] = []

    def affected(ids: list[str]) -> list[str]:
        if set(ids) - requirements:
            raise ValueError("Execution issue references unknown requirements")
        return [item.id for item in plan.items if set(item.requirement_ids).intersection(ids)]

    def add(
        kind: str,
        origin: str,
        description: str,
        targets: list[str],
        *,
        blocking: bool = True,
        scope_basis: Literal["mapped", "global", "unknown"] | None = None,
    ) -> None:
        issues.append(
            ExecutionIssue.model_validate(
                {
                    "id": origin,
                    "kind": kind,
                    "description": description,
                    "blocking": blocking,
                    "global_scope": blocking and not targets,
                    "item_ids": targets,
                    "origin": origin,
                    "scope_basis": scope_basis,
                }
            )
        )

    for index, warning in enumerate(spec.extraction_warnings):
        add("extraction_warning", f"extraction_warning:{index}", warning, [])
    for index, finding in enumerate(review.findings):
        if isinstance(finding, ScopedReviewFinding):
            targets, scope_basis = review_impact(finding, analysis, plan)
            add("review", f"review:{index}", finding.description, targets, scope_basis=scope_basis)
            continue
        assert isinstance(finding, ReviewFinding)
        targets = list(dict.fromkeys(finding.item_ids))
        if finding.target != "plan" and targets:
            targets = affected(
                [req for item_id in targets for req in items[item_id].requirement_ids]
            )
        add(
            "review",
            f"review:{index}",
            finding.description,
            targets,
            scope_basis="mapped" if targets else "unknown",
        )
    for requirement in analysis.requirements:
        for index, question in enumerate(requirement.open_questions):
            add(
                "requirement_question",
                f"requirement:{requirement.id}:{index}",
                question,
                affected([requirement.id]),
            )
    for item in plan.items:
        for index, question in enumerate(item.open_questions):
            add("item_question", f"item:{item.id}:{index}", question, [item.id])
    if gap_assessment is not None:
        gap_assessment.validate_context(spec, analysis)
    scopes = {g.gap_index: g for g in gap_assessment.gaps} if gap_assessment else {}
    for index, gap in enumerate(analysis.gaps):
        scope = scopes.get(index)
        add(
            "analysis_gap",
            f"analysis_gap:{index}",
            gap,
            affected(scope.requirement_ids) if scope else [],
            blocking=scope is None or scope.disposition != "note",
        )
    if source_audit is not None:
        for index, audit_finding in enumerate(source_audit.findings):
            add(
                "source_audit",
                f"source_audit:{index}",
                audit_finding.description,
                affected(audit_finding.requirement_ids),
            )
        for index, application in enumerate(source_audit.knowledge_applications):
            if application.assessment == "uncertain":
                add(
                    "knowledge_uncertainty",
                    f"knowledge_uncertainty:{index}",
                    application.rationale,
                    affected(application.requirement_ids),
                )
    decisions = []
    for item in plan.items:
        blockers = [
            issue.id
            for issue in issues
            if issue.blocking and (issue.global_scope or item.id in issue.item_ids)
        ]
        decisions.append(
            ItemReadiness(
                plan_item_id=item.id,
                status="unsupported"
                if item.method != "simulation"
                else "blocked"
                if blockers
                else "eligible",
                issue_ids=blockers,
            )
        )
    return ExecutionReadiness(items=decisions, issues=issues)
