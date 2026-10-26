"""Contracts shared by ingestion, planning, export, and future test generation."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmpty = Annotated[str, Field(min_length=1)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceBlock(Contract):
    id: NonEmpty
    kind: Literal["paragraph", "table_row"]
    section: str
    locator: NonEmpty
    text: NonEmpty


class Specification(Contract):
    schema_version: Literal["1.0"] = "1.0"
    document_name: NonEmpty
    sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    blocks: Annotated[list[SourceBlock], Field(min_length=1)]
    extraction_warnings: list[str]

    @model_validator(mode="after")
    def unique_blocks(self) -> Self:
        _unique([block.id for block in self.blocks], "source block")
        return self


class Requirement(Contract):
    id: NonEmpty
    statement: NonEmpty
    feature: NonEmpty
    basis: Literal["explicit", "derived"]
    source_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    rationale: str
    open_questions: list[str]


class SpecAnalysis(Contract):
    schema_version: Literal["1.0"] = "1.0"
    requirements: Annotated[list[Requirement], Field(min_length=1)]
    gaps: list[str]

    @model_validator(mode="after")
    def unique_requirements(self) -> Self:
        _unique([item.id for item in self.requirements], "requirement")
        return self


class VerificationItem(Contract):
    id: NonEmpty
    requirement_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    feature: NonEmpty
    objective: NonEmpty
    method: Literal["simulation", "assertion", "formal", "static", "inspection"]
    preconditions: list[str]
    stimulus: list[str]
    expected_results: Annotated[list[NonEmpty], Field(min_length=1)]
    coverage_intent: list[str]
    environment_needs: list[str]
    priority: Literal["high", "medium", "low"]
    open_questions: list[str]


class VerificationPlan(Contract):
    schema_version: Literal["1.0"] = "1.0"
    items: Annotated[list[VerificationItem], Field(min_length=1)]

    @model_validator(mode="after")
    def unique_items(self) -> Self:
        _unique([item.id for item in self.items], "verification item")
        return self


class ReviewFinding(Contract):
    severity: Literal["error", "warning"]
    target: Literal["analysis", "plan", "specification"] = "plan"
    item_ids: list[str]
    description: NonEmpty


class PlanReview(Contract):
    schema_version: Literal["1.0"] = "1.0"
    findings: list[ReviewFinding]

    @property
    def needs_revision(self) -> bool:
        return any(
            finding.severity == "error" and finding.target != "specification"
            for finding in self.findings
        )


def _unique(ids: list[str], label: str) -> None:
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate {label} IDs")


def validate_sources(analysis: SpecAnalysis, specification: Specification) -> None:
    """Reject fabricated references independently of the LLM review."""
    known = {block.id for block in specification.blocks}
    for requirement in analysis.requirements:
        unknown = set(requirement.source_ids) - known
        if unknown:
            raise ValueError(f"{requirement.id}: unknown source IDs {sorted(unknown)}")


def validate_traceability(plan: VerificationPlan, analysis: SpecAnalysis) -> None:
    known = {requirement.id for requirement in analysis.requirements}
    covered: set[str] = set()
    for item in plan.items:
        unknown = set(item.requirement_ids) - known
        if unknown:
            raise ValueError(f"{item.id}: unknown requirement IDs {sorted(unknown)}")
        covered.update(item.requirement_ids)
    if missing := known - covered:
        raise ValueError(f"Requirements without verification items: {sorted(missing)}")
