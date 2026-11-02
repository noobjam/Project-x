"""Strict model output; the host supplies the fixed hardware and provenance."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from soc_verifier.domain.hardware import HardwareSnapshot
from soc_verifier.domain.models import Contract, NonEmpty, Specification, VerificationItem
from soc_verifier.domain.readiness import (
    ExecutionIssue,
    GapEvidence,
    permits_experimental_attempt,
)
from soc_verifier.domain.testbench import (
    CycleStep,
    ExpectedValue,
    Identifier,
    TestbenchBinding,
    Value,
)


class InputValue(Contract):
    signal: Identifier
    value: Value


class ProposedCheck(ExpectedValue):
    source_ids: Annotated[list[NonEmpty], Field(min_length=1)]


class ProposedStep(Contract):
    description: NonEmpty
    inputs: list[InputValue]
    cycles: Annotated[int, Field(ge=1, le=10_000)]
    checks: Annotated[list[ProposedCheck], Field(max_length=128)]


def input_values(values: list[InputValue]) -> dict[str, int]:
    result = {v.signal: v.value for v in values}
    if len(result) != len(values):
        raise ValueError("Duplicate input assignments")
    return result


class _Proposal(Contract):
    plan_item_id: NonEmpty
    status: Literal["ready", "needs_input"]
    rationale: NonEmpty
    initial_inputs: list[InputValue]
    steps: Annotated[list[ProposedStep], Field(max_length=1_000)]
    rtl_source_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    open_questions: list[NonEmpty]

    @model_validator(mode="after")
    def readiness(self) -> Self:
        if isinstance(self, TestbenchProposal) and any(
            check.phase != "post_edge" for step in self.steps for check in step.checks
        ):
            raise ValueError("Pre-edge checks require testbench-proposal-v2")
        if self.status == "ready" and (self.open_questions or not self.steps):
            raise ValueError("Ready proposals need steps and no unresolved questions")
        if self.status == "needs_input" and (
            not self.open_questions or self.steps or self.initial_inputs
        ):
            raise ValueError("Blocked proposals must report questions without executable steps")
        return self

    def validate_evidence(
        self,
        item: VerificationItem,
        spec: Specification,
        hardware: HardwareSnapshot,
    ) -> None:
        if self.plan_item_id != item.id:
            raise ValueError("Testbench proposal targets a different plan item")
        if set(self.rtl_source_ids) - {source.id for source in hardware.sources}:
            raise ValueError("Testbench proposal cites unknown RTL")
        known_sources = {block.id for block in spec.blocks}
        if any(
            set(check.source_ids) - known_sources for step in self.steps for check in step.checks
        ):
            raise ValueError("Testbench check cites unknown specification evidence")

    def bind(
        self,
        item: VerificationItem,
        hardware: HardwareSnapshot,
        *,
        proposal_sha256: str,
        task_id: str,
    ) -> TestbenchBinding:
        if self.status != "ready":
            raise ValueError("Testbench proposal needs design input")
        binding = TestbenchBinding(
            format="directed-testbench-v3"
            if isinstance(self, (ObservedTestbenchProposal, ExperimentalTestbenchProposal))
            else "directed-testbench-v2",
            origin="agent",
            author="Testbench agent",
            proposal_sha256=proposal_sha256,
            agent_task_id=task_id,
            plan_item_id=self.plan_item_id,
            top_module=hardware.target.top_module,
            parameters=hardware.target.parameters,
            ports=hardware.target.ports,
            probes=hardware.target.probes
            if isinstance(self, (ObservedTestbenchProposal, ExperimentalTestbenchProposal))
            else [],
            clock=hardware.target.clock,
            initial_inputs=input_values(self.initial_inputs),
            steps=[
                CycleStep(
                    description=step.description,
                    inputs=input_values(step.inputs),
                    cycles=step.cycles,
                    checks=[
                        ExpectedValue(**c.model_dump(exclude={"source_ids"})) for c in step.checks
                    ],
                )
                for step in self.steps
            ],
            question_resolutions={},
            unresolved_questions=[],
        )
        binding.validate_item(item)
        if {c.expected_result_index for s in binding.steps for c in s.checks} != set(
            range(len(item.expected_results))
        ):
            raise ValueError("Agent binding omits a planned expected result")
        return binding


class TestbenchProposal(_Proposal):
    """Historical output-only proposal; no inferred new observation capabilities."""

    format: Literal["testbench-proposal-v1"] = "testbench-proposal-v1"


class ObservedTestbenchProposal(_Proposal):
    format: Literal["testbench-proposal-v2"] = "testbench-proposal-v2"


class CaseIssueAssessment(Contract):
    issue_id: NonEmpty
    disposition: Literal["independent", "needs_input"]
    rationale: NonEmpty
    evidence: list[GapEvidence]

    @model_validator(mode="after")
    def justification(self) -> Self:
        if self.disposition == "independent" and not self.evidence:
            raise ValueError("Case independence requires source quotations")
        if any(not quote.quote.strip() for quote in self.evidence):
            raise ValueError("Case evidence must contain source text")
        return self


class ExperimentalTestbenchProposal(_Proposal):
    """A proposed case assessment never rewrites the review or confers acceptance."""

    format: Literal["testbench-proposal-v3"] = "testbench-proposal-v3"
    judgment_state: Literal["agent_proposed"] = "agent_proposed"
    issue_assessments: list[CaseIssueAssessment]

    @model_validator(mode="after")
    def unresolved_issues(self) -> Self:
        if self.status == "ready" and any(
            issue.disposition == "needs_input" for issue in self.issue_assessments
        ):
            raise ValueError("Unresolved case issues cannot produce an executable proposal")
        return self

    def validate_issues(self, issues: list[ExecutionIssue], spec: Specification) -> None:
        if not permits_experimental_attempt(issues):
            raise ValueError("Experimental proposals cannot bypass explicit execution blockers")
        identifiers = [assessment.issue_id for assessment in self.issue_assessments]
        if sorted(identifiers) != sorted(issue.id for issue in issues):
            raise ValueError("Assess every case issue exactly once")
        sources = {block.id: block.text for block in spec.blocks}
        for assessment in self.issue_assessments:
            for quote in assessment.evidence:
                if quote.source_id not in sources or quote.quote not in sources[quote.source_id]:
                    raise ValueError("Case assessment must quote specification evidence exactly")
