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


class GlobalPlanDependency(Contract):
    plan_item_id: NonEmpty
    plan_field: Literal[
        "objective", "preconditions", "stimulus", "expected_results", "environment_needs"
    ]
    plan_quote: Annotated[str, Field(min_length=1, max_length=6_000)]
    evidence_indices: Annotated[list[Annotated[int, Field(strict=True, ge=0)]], Field(min_length=1)]
    rationale: NonEmpty


class AccountedGlobalScope(GlobalScope):
    evidence: Annotated[list[ReviewEvidence], Field(min_length=1)]
    dependencies: Annotated[list[GlobalPlanDependency], Field(min_length=1)]

    @model_validator(mode="after")
    def evidence_references(self) -> Self:
        for dependency in self.dependencies:
            indexes = dependency.evidence_indices
            if len(indexes) != len(set(indexes)):
                raise ValueError("Duplicate global dependency evidence indices")
            if any(index >= len(self.evidence) for index in indexes):
                raise ValueError("Global dependency references an unknown evidence index")
        return self


class AttributedReviewFinding(ScopedReviewFinding):
    scope: ItemScope | RequirementScope | SourceScope | AccountedGlobalScope | UnknownScope


class ScopedPlanReviewV2(Contract):
    schema_version: Literal["2.0"] = "2.0"
    judgment_state: Literal["agent_proposed"] = "agent_proposed"
    findings: list[ScopedReviewFinding]

    @property
    def needs_revision(self) -> bool:
        return any(
            finding.severity == "error" and finding.target != "specification"
            for finding in self.findings
        )


class AcceptanceNote(Contract):
    """A source-backed limit on acceptance, not an unresolved executable obligation."""

    kind: Literal["source_provenance", "pending_engineering_review"]
    description: NonEmpty
    rationale: NonEmpty
    evidence: Annotated[list[ReviewEvidence], Field(min_length=1)]


class ScopedPlanReviewV3(Contract):
    schema_version: Literal["3.0"] = "3.0"
    judgment_state: Literal["agent_proposed"] = "agent_proposed"
    findings: list[ScopedReviewFinding]
    acceptance_notes: list[AcceptanceNote] = Field(default_factory=list)

    @property
    def needs_revision(self) -> bool:
        return any(
            finding.severity == "error" and finding.target != "specification"
            for finding in self.findings
        )


class ScopedPlanReview(Contract):
    schema_version: Literal["4.0"] = "4.0"
    judgment_state: Literal["agent_proposed"] = "agent_proposed"
    findings: list[AttributedReviewFinding]
    acceptance_notes: list[AcceptanceNote] = Field(default_factory=list)

    @property
    def needs_revision(self) -> bool:
        return any(
            finding.severity == "error" and finding.target != "specification"
            for finding in self.findings
        )


type Review = PlanReview | ScopedPlanReviewV2 | ScopedPlanReviewV3 | ScopedPlanReview


def acceptance_notes(review: Review) -> list[AcceptanceNote]:
    return (
        review.acceptance_notes
        if isinstance(review, (ScopedPlanReviewV3, ScopedPlanReview))
        else []
    )


def read_review(data: Any) -> Review:
    """Read all formats without migrating or clearing historical blockers."""
    if isinstance(data, (PlanReview, ScopedPlanReviewV2, ScopedPlanReviewV3, ScopedPlanReview)):
        return data
    if isinstance(data, dict) and data.get("schema_version", "1.0") == "1.0":
        return PlanReview.model_validate(data)
    if isinstance(data, dict) and data.get("schema_version") == "2.0":
        return ScopedPlanReviewV2.model_validate(data)
    if isinstance(data, dict) and data.get("schema_version") == "3.0":
        return ScopedPlanReviewV3.model_validate(data)
    return ScopedPlanReview.model_validate(data)


def validate_review_context(
    review: Review, spec: Specification, analysis: SpecAnalysis, plan: VerificationPlan
) -> None:
    sources = {block.id: block.text for block in spec.blocks}
    requirements = {requirement.id for requirement in analysis.requirements}
    items = {item.id: item for item in plan.items}
    for note in acceptance_notes(review):
        for evidence in note.evidence:
            if (
                evidence.source_id not in sources
                or evidence.quote not in sources[evidence.source_id]
            ):
                raise ValueError(
                    "Acceptance note evidence must quote an existing source block exactly"
                )
    for finding in review.findings:
        if set(finding.item_ids) - items.keys():
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
        if isinstance(finding.scope, AccountedGlobalScope):
            ids = [dependency.plan_item_id for dependency in finding.scope.dependencies]
            if len(ids) != len(set(ids)):
                raise ValueError("Global dependencies must identify each plan item exactly once")
            if set(ids) != items.keys():
                raise ValueError(
                    "Global dependencies must cover every plan item; "
                    f"missing={sorted(items.keys() - set(ids))}, "
                    f"unknown={sorted(set(ids) - items.keys())}"
                )
            for dependency in finding.scope.dependencies:
                value = getattr(items[dependency.plan_item_id], dependency.plan_field)
                fields = [value] if isinstance(value, str) else value
                if not any(dependency.plan_quote in text for text in fields):
                    raise ValueError("Global dependency must quote its declared plan field exactly")


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
