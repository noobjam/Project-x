"""Durable agent workflow; immutable artifacts checkpoint completed work."""

import json
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from pydantic import BaseModel

from soc_verifier.agents import instructions as prompts
from soc_verifier.agents.base import AgentExecutor
from soc_verifier.agents.tasks import (
    ArtifactReference,
    Task,
    TaskInputs,
    fingerprint,
    runtime_versions,
)
from soc_verifier.domain.models import (
    PlanReview,
    SpecAnalysis,
    Specification,
    VerificationPlan,
    validate_sources,
    validate_traceability,
)
from soc_verifier.domain.passage_accounting import passage_accounting_schema
from soc_verifier.domain.source_audit import SourceAudit
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.accounting import (
    extract_with_feedback,
    project_accounting,
    source_context,
)
from soc_verifier.workflows.spec_to_plan.batched_roles import (
    analyze_batches,
    plan_batches,
    review_batches,
)
from soc_verifier.workflows.spec_to_plan.batching import split_specification
from soc_verifier.workflows.spec_to_plan.reviewing import generate_review, validate_review
from soc_verifier.workflows.spec_to_plan.source_audit import execute_source_audit


class PlanState(TypedDict, total=False):
    specification: dict[str, Any]
    analysis: dict[str, Any]
    analysis_revision: int
    plan: dict[str, Any]
    review: dict[str, Any]
    review_revision: int
    revision: int
    status: Literal["draft_ready", "needs_review", "analysis_ready"]
    source_accounting_artifact: str
    source_audit_artifact: str
    source_audit: dict[str, Any]


@dataclass
class PlanningWorkflow:
    agents: AgentExecutor
    artifacts: ArtifactStore
    max_revisions: int
    chunk_max_characters: int = 24_000
    plan_batch_size: int = 8
    batch_workers: int = 1
    source_accounting: bool = False

    def run(
        self, specification: Specification | None = None, *, analysis_only: bool = False
    ) -> PlanState:
        if analysis_only and not self.source_accounting:
            raise ValueError("Analysis-only execution requires source accounting")
        if specification is None:
            specification = Specification.model_validate(self.artifacts.read("specification.json"))
        self.artifacts.write("specification.json", specification)
        if (
            self.source_accounting
            and len(split_specification(specification, self.chunk_max_characters)) > 1
        ):
            raise ValueError("Source accounting trial requires one bounded source chunk")
        execution = {
            "format": "task-execution-v1",
            "versions": runtime_versions(),
            "configuration": self.agents.configuration,
            "source": ArtifactReference.capture(self.artifacts, "specification.json").model_dump(),
            "document_sha256": specification.sha256,
            "max_revisions": self.max_revisions,
            "chunk_max_characters": self.chunk_max_characters,
            "plan_batch_size": self.plan_batch_size,
            "source_accounting": self.source_accounting,
        }
        if self.artifacts.exists("knowledge.json"):
            execution["knowledge"] = ArtifactReference.capture(
                self.artifacts, "knowledge.json"
            ).model_dump()
        if self.artifacts.exists("execution.json"):
            if self.artifacts.read("execution.json") != execution:
                raise ValueError("Run inputs or versions changed; start a new run")
        elif self.artifacts.exists("analysis.json"):
            raise ValueError("Legacy run has no task bindings; export or start a new run")
        self.artifacts.write("execution.json", execution)
        return _run_workflow(
            self.agents,
            self.artifacts,
            specification,
            max_revisions=self.max_revisions,
            chunk_max_characters=self.chunk_max_characters,
            plan_batch_size=self.plan_batch_size,
            batch_workers=self.batch_workers,
            source_accounting=self.source_accounting,
            analysis_only=analysis_only,
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
    source_accounting: bool,
    analysis_only: bool,
) -> PlanState:
    if not 0 <= max_revisions <= 5:
        raise ValueError("max_revisions must be between 0 and 5")
    if chunk_max_characters < 1000 or plan_batch_size < 1 or batch_workers < 1:
        raise ValueError("Invalid batching configuration")

    execution = artifacts.read("execution.json")

    def bind(
        name: str,
        state: PlanState,
        role: Literal["analyst", "planner", "reviewer"],
        instruction: str,
        schema: type[BaseModel],
        assigned_ids: list[str],
    ) -> Task:
        names = {"source": "specification.json"}
        if "knowledge" in execution:
            names["knowledge"] = "knowledge.json"
        if "analysis" in state:
            names["analysis"] = _analysis_artifact(state["analysis_revision"])
        if "source_accounting_artifact" in state:
            names["source_accounting"] = state["source_accounting_artifact"]
        if "source_audit_artifact" in state:
            names["source_audit"] = state["source_audit_artifact"]
        if "plan" in state:
            names["plan"] = f"plan.r{state['revision']:03d}.json"
        if "review" in state:
            names["review"] = f"review.r{state['review_revision']:03d}.json"
        return Task.bind(
            artifacts,
            name,
            TaskInputs(
                role=role,
                stage=name.removesuffix(".json"),
                assigned_ids=assigned_ids,
                evidence={
                    key: ArtifactReference.capture(artifacts, path) for key, path in names.items()
                },
                input_sha256=fingerprint(state),
                instruction_sha256=fingerprint(instruction),
                schema_sha256=fingerprint(schema.model_json_schema()),
                versions=execution["versions"],
                configuration=execution,
            ),
        )

    def analyze(state: PlanState) -> PlanState:
        spec = Specification.model_validate(state["specification"])
        revision = state.get("analysis_revision", -1) + 1
        name = _analysis_artifact(revision)
        if source_accounting:
            extraction_name = f"obligations.r{revision:03d}.json"
            schema = passage_accounting_schema(spec)
            extraction_task = bind(
                extraction_name,
                state,
                "analyst",
                prompts.ANALYZE_ACCOUNTED,
                schema,
                [b.id for b in spec.blocks],
            )
            extract_with_feedback(
                agents,
                extraction_task,
                spec,
                schema,
                {
                    "specification": source_context(spec),
                    "previous_analysis": state.get("analysis"),
                    "review": state.get("review"),
                },
            )
            analysis, accounting = project_accounting(artifacts, extraction_name, name)
            artifacts.write(name, analysis)
            accounting_name = f"source-accounting.r{revision:03d}.json"
            artifacts.write(accounting_name, accounting)
            return {
                "analysis": analysis.model_dump(mode="json"),
                "analysis_revision": revision,
                "source_accounting_artifact": accounting_name,
            }
        task = bind(
            name, state, "analyst", prompts.ANALYZE, SpecAnalysis, [b.id for b in spec.blocks]
        )
        cached = task.load(SpecAnalysis)
        if cached is not None:
            analysis = cached
        elif len(split_specification(spec, chunk_max_characters)) > 1:
            analysis = analyze_batches(
                agents,
                artifacts,
                spec,
                revision=revision,
                chunk_characters=chunk_max_characters,
                workers=batch_workers,
                review=state.get("review"),
                task=task,
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
                role="analyst",
                instruction=prompts.ANALYZE,
                context=context,
                schema=SpecAnalysis,
                task=task.envelope,
            )
        validate_sources(analysis, spec)
        task.save(analysis)
        return {"analysis": analysis.model_dump(mode="json"), "analysis_revision": revision}

    def audit_source(state: PlanState) -> PlanState:
        if not source_accounting:
            return {}
        name = f"source-audit.r{state['analysis_revision']:03d}.json"
        task = bind(
            name,
            state,
            "reviewer",
            prompts.AUDIT_SOURCE,
            SourceAudit,
            [r["id"] for r in state["analysis"]["requirements"]],
        )
        audit = execute_source_audit(agents, task)
        return {"source_audit_artifact": name, "source_audit": audit.model_dump(mode="json")}

    def plan(state: PlanState) -> PlanState:
        revision = state.get("revision", -1) + 1
        name = f"plan.r{revision:03d}.json"
        instruction = prompts.PLAN + (
            prompts.SOURCE_AUDIT_GUIDANCE if "source_audit" in state else ""
        )
        task = bind(
            name,
            state,
            "planner",
            instruction,
            VerificationPlan,
            [r.id for r in SpecAnalysis.model_validate(state["analysis"]).requirements],
        )
        cached = task.load(VerificationPlan)
        if cached is not None:
            result = cached
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
                task=task,
            )
        else:
            context = {
                "specification": state["specification"],
                "analysis": state["analysis"],
                "previous_plan": state.get("plan"),
                "review": state.get("review"),
                **({"source_audit": state["source_audit"]} if "source_audit" in state else {}),
            }
            result = agents.run(
                role="planner",
                instruction=instruction,
                context=json.dumps(context),
                schema=VerificationPlan,
                task=task.envelope,
            )
        validate_traceability(result, SpecAnalysis.model_validate(state["analysis"]))
        task.save(result)
        return {"plan": result.model_dump(mode="json"), "revision": revision}

    def review(state: PlanState) -> PlanState:
        name = f"review.r{state['revision']:03d}.json"
        known = {item.id for item in VerificationPlan.model_validate(state["plan"]).items}
        task = bind(name, state, "reviewer", prompts.REVIEW, PlanReview, sorted(known))
        cached = task.load(PlanReview)
        if cached is not None:
            result = cached
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
                task=task,
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
                task=task.envelope,
            )
        validate_review(result, known)
        task.save(result)
        return {"review": result.model_dump(mode="json"), "review_revision": state["revision"]}

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
            or bool(state.get("source_audit", {}).get("findings"))
            or any(
                a["assessment"] == "uncertain"
                for a in state.get("source_audit", {}).get("knowledge_applications", [])
            )
        )
        status: Literal["needs_review", "draft_ready"] = (
            "needs_review" if unresolved else "draft_ready"
        )
        artifacts.write(
            "result.json",
            {
                "schema_version": "2.0",
                "status": status,
                "revision": state["revision"],
                "human_approved": False,
                "revision_limit_reached": review_result.needs_revision,
                "analysis_artifact": _analysis_artifact(state["analysis_revision"]),
                **(
                    {"source_accounting_artifact": state["source_accounting_artifact"]}
                    if "source_accounting_artifact" in state
                    else {}
                ),
                **(
                    {"source_audit_artifact": state["source_audit_artifact"]}
                    if "source_audit_artifact" in state
                    else {}
                ),
                "plan_artifact": f"plan.r{state['revision']:03d}.json",
                "review_artifact": f"review.r{state['revision']:03d}.json",
            },
        )
        return {"status": status}

    # Replay deterministic stage decisions from immutable artifacts. Completed
    # batches and revisions are validated and reused; only unfinished work runs.
    state: PlanState = {"specification": specification.model_dump(mode="json")}
    state.update(analyze(state))
    state.update(audit_source(state))
    if analysis_only:
        return {**state, "status": "analysis_ready"}
    while True:
        state.update(plan(state))
        state.update(review(state))
        next_stage = route(state)
        if next_stage == "finish":
            state.update(finish(state))
            return state
        if next_stage == "analyze":
            state.update(analyze(state))
            state.update(audit_source(state))


def _analysis_artifact(revision: int) -> str:
    return "analysis.json" if revision == 0 else f"analysis.r{revision:03d}.json"
