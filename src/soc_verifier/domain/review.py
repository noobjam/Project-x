"""Versioned review impact; legacy empty references never acquire a guessed scope."""

from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from soc_verifier.domain.models import (
    Contract,
    NonEmpty,
    PlanReview,
    SpecAnalysis,
    Specification,
    VerificationPlan,
)


class ReviewEvidence(Contract):
    source_id: NonEmpty
    quote: Annotated[str, Field(min_length=1, max_length=6_000)]


class LocalScope(Contract):
    rationale: NonEmpty
    evidence: Annotated[list[ReviewEvidence], Field(min_length=1)]


class ItemScope(LocalScope):
    kind: Literal["items"]
    item_ids: Annotated[list[NonEmpty], Field(min_length=1)]


class RequirementScope(LocalScope):
    kind: Literal["requirements"]
    requirement_ids: Annotated[list[NonEmpty], Field(min_length=1)]


class SourceScope(LocalScope):
    kind: Literal["sources"]
    source_ids: Annotated[list[NonEmpty], Field(min_length=1)]


class GlobalScope(Contract):
    kind: Literal["global"]
    rationale: NonEmpty
    evidence: list[ReviewEvidence]


class UnknownScope(Contract):
    kind: Literal["unknown"]
    rationale: NonEmpty
    evidence: list[ReviewEvidence]


class ScopedReviewFinding(Contract):
    severity: Literal["error", "warning"]
    target: Literal["analysis", "plan", "specification"]
    kind: Literal[
        "omission",
        "timing",
        "unsupported_behavior",
        "weak_check",
        "missing_interaction",
        "source_conflict",
        "execution_binding",
        "ambiguity",
        "other",
    ]
    description: NonEmpty
    scope: ItemScope | RequirementScope | SourceScope | GlobalScope | UnknownScope
    recommended_action: NonEmpty

    @model_validator(mode="after")
    def appropriate_scope(self) -> Self:
        if self.scope.kind == "items" and self.target != "plan":
            raise ValueError(
                "Analysis/specification findings must identify requirement or source scope"
            )
        return self

    @property
    def item_ids(self) -> list[str]:
        return self.scope.item_ids if isinstance(self.scope, ItemScope) else []

    @property
    def requirement_ids(self) -> list[str]:
        return self.scope.requirement_ids if isinstance(self.scope, RequirementScope) else []

    @property
    def source_ids(self) -> list[str]:
        ids = [e.source_id for e in self.scope.evidence]
        if isinstance(self.scope, SourceScope):
            ids.extend(self.scope.source_ids)
        return list(dict.fromkeys(ids))


class ScopedPlanReview(Contract):
    schema_version: Literal["2.0"] = "2.0"
    judgment_state: Literal["agent_proposed"] = "agent_proposed"
    findings: list[ScopedReviewFinding]

    @property
    def needs_revision(self) -> bool:
        return any(
            finding.severity == "error" and finding.target != "specification"
            for finding in self.findings
        )


type Review = PlanReview | ScopedPlanReview


def read_review(data: Any) -> Review:
    """Read both formats without migrating or clearing historical blockers."""
    if isinstance(data, (PlanReview, ScopedPlanReview)):
        return data
    if isinstance(data, dict) and data.get("schema_version", "1.0") == "1.0":
        return PlanReview.model_validate(data)
    return ScopedPlanReview.model_validate(data)


def validate_review_context(
    review: Review, spec: Specification, analysis: SpecAnalysis, plan: VerificationPlan
) -> None:
    sources = {block.id: block.text for block in spec.blocks}
    requirements = {requirement.id for requirement in analysis.requirements}
    items = {item.id for item in plan.items}
    for finding in review.findings:
        if set(finding.item_ids) - items:
            raise ValueError("Review references unknown verification item IDs")
        if not isinstance(finding, ScopedReviewFinding):
            continue
        if set(finding.requirement_ids) - requirements:
            raise ValueError("Review references unknown requirement IDs")
        if set(finding.source_ids) - sources.keys():
            raise ValueError("Review references unknown source IDs")
        for evidence in finding.scope.evidence:
            if evidence.quote not in sources[evidence.source_id]:
                raise ValueError("Review evidence must quote an existing source block exactly")
        if isinstance(finding.scope, SourceScope) and not set(finding.scope.source_ids) <= {
            e.source_id for e in finding.scope.evidence
        }:
            raise ValueError("Every affected source requires supporting evidence")


def review_impact(
    finding: ScopedReviewFinding, analysis: SpecAnalysis, plan: VerificationPlan
) -> tuple[list[str], Literal["mapped", "global", "unknown"]]:
    scope = finding.scope
    if isinstance(scope, ItemScope):
        return list(dict.fromkeys(scope.item_ids)), "mapped"
    if isinstance(scope, (GlobalScope, UnknownScope)):
        return [], scope.kind
    if isinstance(scope, RequirementScope):
        affected = set(scope.requirement_ids)
    else:
        affected = {
            r.id for r in analysis.requirements if set(r.source_ids) & set(scope.source_ids)
        }
        # An omitted obligation can have no requirement yet. No match is not clearance.
        mapped_sources = {source for r in analysis.requirements for source in r.source_ids}
        if set(scope.source_ids) - mapped_sources:
            return [], "unknown"
    targets = [item.id for item in plan.items if set(item.requirement_ids) & affected]
    return (targets, "mapped") if targets else ([], "unknown")
