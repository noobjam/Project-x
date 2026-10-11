"""Bounded planning/review graph with independent traceability checks."""

import json
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from soc_verifier.domain.models import (
    PlanReview,
    SpecAnalysis,
    Specification,
    VerificationPlan,
    validate_sources,
    validate_traceability,
)
from soc_verifier.llm.base import StructuredLLM
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan import prompts


class PlanState(TypedDict, total=False):
    specification: dict[str, Any]
    analysis: dict[str, Any]
    plan: dict[str, Any]
    review: dict[str, Any]
    revision: int
    status: Literal["draft_ready", "needs_review"]


def build_graph(
    llm: StructuredLLM,
    artifacts: ArtifactStore,
    checkpointer: BaseCheckpointSaver[Any],
    *,
    max_revisions: int,
) -> CompiledStateGraph[PlanState, None, PlanState, PlanState]:
    if not 0 <= max_revisions <= 5:
        raise ValueError("max_revisions must be between 0 and 5")

    def analyze(state: PlanState) -> dict[str, Any]:
        spec = Specification.model_validate(state["specification"])
        if artifacts.exists("analysis.json"):
            analysis = SpecAnalysis.model_validate(artifacts.read("analysis.json"))
        else:
            analysis = llm.generate(
                instruction=prompts.ANALYZE, context=spec.model_dump_json(), schema=SpecAnalysis
            )
        validate_sources(analysis, spec)
        artifacts.write("analysis.json", analysis)
        return {"analysis": analysis.model_dump(mode="json")}

    def plan(state: PlanState) -> dict[str, Any]:
        revision = state.get("revision", -1) + 1
        name = f"plan.r{revision:03d}.json"
        if artifacts.exists(name):
            result = VerificationPlan.model_validate(artifacts.read(name))
        else:
            context = {
                "specification": state["specification"],
                "analysis": state["analysis"],
                "previous_plan": state.get("plan"),
                "review": state.get("review"),
            }
            result = llm.generate(
                instruction=prompts.PLAN, context=json.dumps(context), schema=VerificationPlan
            )
        validate_traceability(result, SpecAnalysis.model_validate(state["analysis"]))
        artifacts.write(name, result)
        return {"plan": result.model_dump(mode="json"), "revision": revision}

    def review(state: PlanState) -> dict[str, Any]:
        name = f"review.r{state['revision']:03d}.json"
        if artifacts.exists(name):
            result = PlanReview.model_validate(artifacts.read(name))
        else:
            result = llm.generate(
                instruction=prompts.REVIEW,
                context=json.dumps(
                    {
                        "specification": state["specification"],
                        "analysis": state["analysis"],
                        "plan": state["plan"],
                    }
                ),
                schema=PlanReview,
            )
        known = {item.id for item in VerificationPlan.model_validate(state["plan"]).items}
        for finding in result.findings:
            if set(finding.item_ids) - known:
                raise ValueError("Review references unknown verification item IDs")
        artifacts.write(name, result)
        return {"review": result.model_dump(mode="json")}

    def route(state: PlanState) -> Literal["plan", "finish"]:
        review_result = PlanReview.model_validate(state["review"])
        if review_result.needs_revision and state["revision"] < max_revisions:
            return "plan"
        return "finish"

    def finish(state: PlanState) -> dict[str, Any]:
        review_result = PlanReview.model_validate(state["review"])
        analysis = SpecAnalysis.model_validate(state["analysis"])
        spec = Specification.model_validate(state["specification"])
        plan_result = VerificationPlan.model_validate(state["plan"])
        unresolved = (
            bool(review_result.findings or analysis.gaps or spec.extraction_warnings)
            or any(item.open_questions for item in plan_result.items)
            or any(item.open_questions for item in analysis.requirements)
        )
        status = "needs_review" if unresolved else "draft_ready"
        artifacts.write(
            "result.json",
            {
                "schema_version": "1.0",
                "status": status,
                "revision": state["revision"],
                "human_approved": False,
                "revision_limit_reached": review_result.needs_revision,
                "plan_artifact": f"plan.r{state['revision']:03d}.json",
                "review_artifact": f"review.r{state['revision']:03d}.json",
            },
        )
        return {"status": status}

    graph = StateGraph(PlanState)
    graph.add_node("analyze", analyze)
    graph.add_node("plan", plan)
    graph.add_node("review", review)
    graph.add_node("finish", finish)
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "plan")
    graph.add_edge("plan", "review")
    graph.add_conditional_edges("review", route)
    graph.add_edge("finish", END)
    return graph.compile(checkpointer=checkpointer)
