"""Durable agent workflow; immutable artifacts checkpoint completed work."""

import json
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from soc_verifier.agents import instructions as prompts
from soc_verifier.agents.base import AgentExecutor
from soc_verifier.domain.models import (
    PlanReview,
    SpecAnalysis,
    Specification,
    VerificationPlan,
    validate_sources,
    validate_traceability,
)
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.batched_roles import (
    analyze_batches,
    plan_batches,
    review_batches,
)
from soc_verifier.workflows.spec_to_plan.batching import split_specification
from soc_verifier.workflows.spec_to_plan.reviewing import generate_review, validate_review


class PlanState(TypedDict, total=False):
    specification: dict[str, Any]
    analysis: dict[str, Any]
    analysis_revision: int
    plan: dict[str, Any]
    review: dict[str, Any]
    revision: int
    status: Literal["draft_ready", "needs_review"]


@dataclass
class PlanningWorkflow:
    agents: AgentExecutor
    artifacts: ArtifactStore
    max_revisions: int
    chunk_max_characters: int = 24_000
    plan_batch_size: int = 8
    batch_workers: int = 1

    def run(self, specification: Specification | None = None) -> PlanState:
        if specification is None:
            specification = Specification.model_validate(self.artifacts.read("specification.json"))
        self.artifacts.write("specification.json", specification)
        return _run_workflow(
            self.agents,
            self.artifacts,
            specification,
            max_revisions=self.max_revisions,
            chunk_max_characters=self.chunk_max_characters,
            plan_batch_size=self.plan_batch_size,
            batch_workers=self.batch_workers,
        )


def _run_workflow(
    agents: AgentExecutor,
    artifacts: ArtifactStore,
    specification: Specification,
    *,
    max_revisions: int,
    chunk_max_characters: int,
    plan_batch_size: int,
    batch_workers: int,
) -> PlanState:
    if not 0 <= max_revisions <= 5:
        raise ValueError("max_revisions must be between 0 and 5")
    if chunk_max_characters < 1000 or plan_batch_size < 1 or batch_workers < 1:
        raise ValueError("Invalid batching configuration")

    def analyze(state: PlanState) -> PlanState:
        spec = Specification.model_validate(state["specification"])
        revision = state.get("analysis_revision", -1) + 1
        name = _analysis_artifact(revision)
        if artifacts.exists(name):
            analysis = SpecAnalysis.model_validate(artifacts.read(name))
        elif len(split_specification(spec, chunk_max_characters)) > 1:
            analysis = analyze_batches(
                agents,
                artifacts,
                spec,
                revision=revision,
                chunk_characters=chunk_max_characters,
                workers=batch_workers,
                review=state.get("review"),
            )
        else:
            context = (
                spec.model_dump_json()
                if revision == 0
                else json.dumps(
                    {
                        "specification": state["specification"],
                        "previous_analysis": state["analysis"],
                        "review": state["review"],
                    }
                )
            )
            analysis = agents.run(
                role="analyst", instruction=prompts.ANALYZE, context=context, schema=SpecAnalysis
            )
        validate_sources(analysis, spec)
        artifacts.write(name, analysis)
        return {"analysis": analysis.model_dump(mode="json"), "analysis_revision": revision}

    def plan(state: PlanState) -> PlanState:
        revision = state.get("revision", -1) + 1
        name = f"plan.r{revision:03d}.json"
        if artifacts.exists(name):
            result = VerificationPlan.model_validate(artifacts.read(name))
        elif _batched(state):
            result = plan_batches(
                agents,
                artifacts,
                Specification.model_validate(state["specification"]),
                SpecAnalysis.model_validate(state["analysis"]),
                revision=revision,
                batch_size=plan_batch_size,
                workers=batch_workers,
                review=state.get("review"),
            )
        else:
            context = {
                "specification": state["specification"],
                "analysis": state["analysis"],
                "previous_plan": state.get("plan"),
                "review": state.get("review"),
            }
            result = agents.run(
                role="planner",
                instruction=prompts.PLAN,
                context=json.dumps(context),
                schema=VerificationPlan,
            )
        validate_traceability(result, SpecAnalysis.model_validate(state["analysis"]))
        artifacts.write(name, result)
        return {"plan": result.model_dump(mode="json"), "revision": revision}

    def review(state: PlanState) -> PlanState:
        name = f"review.r{state['revision']:03d}.json"
        known = {item.id for item in VerificationPlan.model_validate(state["plan"]).items}
        if artifacts.exists(name):
            result = PlanReview.model_validate(artifacts.read(name))
        elif _batched(state):
            result = review_batches(
                agents,
                artifacts,
                Specification.model_validate(state["specification"]),
                SpecAnalysis.model_validate(state["analysis"]),
                VerificationPlan.model_validate(state["plan"]),
                revision=state["revision"],
                chunk_characters=chunk_max_characters,
                workers=batch_workers,
            )
        else:
            result = generate_review(
                agents,
                instruction=prompts.REVIEW,
                context={
                    "specification": state["specification"],
                    "analysis": state["analysis"],
                    "plan": state["plan"],
                },
                known_items=known,
            )
        validate_review(result, known)
        artifacts.write(name, result)
        return {"review": result.model_dump(mode="json")}

    def route(state: PlanState) -> Literal["analyze", "plan", "finish"]:
        review_result = PlanReview.model_validate(state["review"])
        if review_result.needs_revision and state["revision"] < max_revisions:
            if any(
                item.severity == "error" and item.target == "analysis"
                for item in review_result.findings
            ):
                return "analyze"
            return "plan"
        return "finish"

    def _batched(state: PlanState) -> bool:
        spec = Specification.model_validate(state["specification"])
        analysis = SpecAnalysis.model_validate(state["analysis"])
        return (
            len(split_specification(spec, chunk_max_characters)) > 1
            or len(analysis.requirements) > plan_batch_size
        )

    def finish(state: PlanState) -> PlanState:
        review_result = PlanReview.model_validate(state["review"])
        analysis = SpecAnalysis.model_validate(state["analysis"])
        spec = Specification.model_validate(state["specification"])
        plan_result = VerificationPlan.model_validate(state["plan"])
        unresolved = (
            bool(review_result.findings or analysis.gaps or spec.extraction_warnings)
            or any(item.open_questions for item in plan_result.items)
            or any(item.open_questions for item in analysis.requirements)
        )
        status: Literal["needs_review", "draft_ready"] = (
            "needs_review" if unresolved else "draft_ready"
        )
        artifacts.write(
            "result.json",
            {
                "schema_version": "1.0",
                "status": status,
                "revision": state["revision"],
                "human_approved": False,
                "revision_limit_reached": review_result.needs_revision,
                "analysis_artifact": _analysis_artifact(state["analysis_revision"]),
                "plan_artifact": f"plan.r{state['revision']:03d}.json",
                "review_artifact": f"review.r{state['revision']:03d}.json",
            },
        )
        return {"status": status}

    # Replay deterministic stage decisions from immutable artifacts. Completed
    # batches and revisions are validated and reused; only unfinished work runs.
    state: PlanState = {"specification": specification.model_dump(mode="json")}
    state.update(analyze(state))
    while True:
        state.update(plan(state))
        state.update(review(state))
        next_stage = route(state)
        if next_stage == "finish":
            state.update(finish(state))
            return state
        if next_stage == "analyze":
            state.update(analyze(state))


def _analysis_artifact(revision: int) -> str:
    return "analysis.json" if revision == 0 else f"analysis.r{revision:03d}.json"
