"""Connect planning, a testbench specialist and execution under one run and budget."""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from soc_verifier.agents.base import AgentExecutor
from soc_verifier.agents.instructions import BUILD_EXPERIMENTAL_TESTBENCH, BUILD_TESTBENCH
from soc_verifier.agents.tasks import (
    ArtifactReference,
    Task,
    TaskInputs,
    fingerprint,
    runtime_versions,
)
from soc_verifier.domain.hardware import HardwareSnapshot
from soc_verifier.domain.models import (
    SpecAnalysis,
    Specification,
    VerificationItem,
    VerificationPlan,
)
from soc_verifier.domain.readiness import (
    ExecutionIssue,
    ExecutionReadiness,
    assess_readiness,
    permits_experimental_attempt,
)
from soc_verifier.domain.review import read_review
from soc_verifier.domain.source_audit import SourceAudit
from soc_verifier.domain.testbench_proposal import (
    ExperimentalTestbenchProposal,
    ObservedTestbenchProposal,
)
from soc_verifier.providers.budget import read_spending
from soc_verifier.simulation.iverilog import tools
from soc_verifier.storage.artifacts import ArtifactStore, artifact_content
from soc_verifier.workflows.execution_readiness import scope_execution_gaps
from soc_verifier.workflows.plan_to_simulation.workflow import prepare_testbench, simulate_testbench
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class VerificationWorkflow:
    planning: PlanningWorkflow
    hardware: HardwareSnapshot
    timeout: float = 10
    experimental: bool = False

    @property
    def artifacts(self) -> ArtifactStore:
        return self.planning.artifacts

    @property
    def agents(self) -> AgentExecutor:
        return self.planning.agents

    def run(self, specification: Specification) -> dict[str, Any]:
        # Reject infrastructure/configuration errors before any paid planning call.
        tools()
        if not 0 < self.timeout <= 120:
            raise ValueError("Invalid simulation timeout")
        minimum = 6 if self.artifacts.exists("knowledge.json") else 4
        configuration = self.agents.configuration
        turns = configuration.get("agent_max_turns", 4)
        if not isinstance(turns, int) or turns < minimum:
            raise ValueError("Testbench agent turn limit cannot cover required evidence reads")
        self.artifacts.write("hardware.json", self.hardware)
        self.artifacts.write("specification.json", specification)
        execution = {
            "format": "verification-pipeline-v3"
            if self.experimental
            else "verification-pipeline-v2",
            "versions": runtime_versions(),
            "configuration": configuration,
            "timeout_seconds": self.timeout,
            "hardware": ArtifactReference.capture(self.artifacts, "hardware.json").model_dump(),
            "source": ArtifactReference.capture(self.artifacts, "specification.json").model_dump(),
        }
        if self.experimental:
            execution["execution_mode"] = "experimental"
        self.artifacts.write("pipeline-execution.json", execution)
        state = self.planning.run(specification)
        plan = VerificationPlan.model_validate(state["plan"])
        analysis = SpecAnalysis.model_validate(state["analysis"])
        planning_result = self.artifacts.read("result.json")
        names = {
            "source": "specification.json",
            "hardware": "hardware.json",
            "analysis": planning_result["analysis_artifact"],
            "plan": planning_result["plan_artifact"],
            "review": planning_result["review_artifact"],
        }
        for key in ("source_audit", "source_accounting"):
            if f"{key}_artifact" in planning_result:
                names[key] = planning_result[f"{key}_artifact"]
        if self.artifacts.exists("knowledge.json"):
            names["knowledge"] = "knowledge.json"
        evidence = {
            key: ArtifactReference.capture(self.artifacts, name) for key, name in names.items()
        }
        review = read_review(evidence["review"].read(self.artifacts))
        source_audit = (
            SourceAudit.model_validate(evidence["source_audit"].read(self.artifacts))
            if "source_audit" in evidence
            else None
        )
        readiness = assess_readiness(
            specification, analysis, plan, review, source_audit=source_audit
        )
        # Do not spend on classifying notes if known hard blockers already prevent every
        # simulation item. Unclassified gaps conservatively retain global scope.
        issues = {issue.id: issue for issue in readiness.issues}
        can_classify = any(
            item.status != "unsupported"
            and all(issues[identifier].kind == "analysis_gap" for identifier in item.issue_ids)
            for item in readiness.items
        )
        if analysis.gaps and can_classify and not self.experimental:
            assessment = scope_execution_gaps(
                self.agents, self.artifacts, specification, analysis, plan, evidence
            )
            readiness = assess_readiness(
                specification,
                analysis,
                plan,
                review,
                gap_assessment=assessment,
                source_audit=source_audit,
            )
            evidence["gap_assessment"] = ArtifactReference.capture(
                self.artifacts, "execution-gaps.json"
            )
        self.artifacts.write(
            "readiness-inputs.json",
            {
                "format": "execution-readiness-inputs-v1",
                "versions": runtime_versions(),
                "evidence": {key: ref.model_dump() for key, ref in evidence.items()},
            },
        )
        self.artifacts.write("readiness.json", readiness)
        eligible = {item.plan_item_id for item in readiness.items if item.status == "eligible"}
        unsupported = [
            item.plan_item_id for item in readiness.items if item.status == "unsupported"
        ]
        blocked = [item.plan_item_id for item in readiness.items if item.status == "blocked"]
        cases = []
        issues = {issue.id: issue for issue in readiness.issues}
        for index, item in enumerate(plan.items):
            item_issues = [
                issues[identifier]
                for decision in readiness.items
                if decision.plan_item_id == item.id
                for identifier in decision.issue_ids
            ]
            attempt = (
                self.experimental
                and item.method == "simulation"
                and permits_experimental_attempt(item_issues)
            )
            if item.id not in eligible and not attempt:
                continue
            cases.append(
                self._case(index, item, specification, analysis, planning_result, item_issues)
            )
        blocked = list(
            dict.fromkeys(
                [*blocked, *(c["plan_item_id"] for c in cases if c["status"] == "needs_input")]
            )
        )
        status = (
            "failed"
            if any(case["status"] not in {"passed", "needs_input"} for case in cases)
            else "blocked"
            if blocked and not any(case["status"] == "passed" for case in cases)
            else "partial"
            if blocked or unsupported or not cases
            else "passed"
        )
        return self._finish(status, cases, unsupported, blocked, plan, readiness)

    def _case(
        self,
        index: int,
        item: VerificationItem,
        specification: Specification,
        analysis: SpecAnalysis,
        planning_result: dict[str, Any],
        issues: list[ExecutionIssue],
    ) -> dict[str, Any]:
        context = {
            "plan_item": item.model_dump(),
            "requirements": [
                r.model_dump() for r in analysis.requirements if r.id in item.requirement_ids
            ],
            "source_directory": [{"id": b.id, "section": b.section} for b in specification.blocks],
        }
        if self.experimental:
            review = read_review(self.artifacts.read(planning_result["review_artifact"]))
            context.update(
                execution_mode="experimental",
                execution_issues=[issue.model_dump() for issue in issues],
                review_findings={
                    issue.id: review.findings[int(issue.id.split(":")[1])].model_dump()
                    for issue in issues
                    if issue.kind == "review"
                },
            )
        schema = ExperimentalTestbenchProposal if self.experimental else ObservedTestbenchProposal
        instruction = BUILD_EXPERIMENTAL_TESTBENCH if self.experimental else BUILD_TESTBENCH
        names = {
            "source": "specification.json",
            "hardware": "hardware.json",
            "analysis": planning_result["analysis_artifact"],
            "plan": planning_result["plan_artifact"],
            "review": planning_result["review_artifact"],
            "readiness": "readiness.json",
            "readiness_inputs": "readiness-inputs.json",
            "execution": "pipeline-execution.json",
        }
        if self.artifacts.exists("knowledge.json"):
            names["knowledge"] = "knowledge.json"
        task = Task.bind(
            self.artifacts,
            f"testbench.{index:03d}.json",
            TaskInputs(
                role="testbench",
                stage="testbench",
                assigned_ids=[item.id],
                evidence={
                    key: ArtifactReference.capture(self.artifacts, name)
                    for key, name in names.items()
                },
                input_sha256=fingerprint(context),
                instruction_sha256=fingerprint(instruction),
                schema_sha256=fingerprint(schema.model_json_schema()),
                versions=runtime_versions(),
                configuration={"configuration": self.agents.configuration},
            ),
        )
        proposal = task.load(schema)
        if proposal is None:
            proposal = self.agents.run(
                role="testbench",
                instruction=instruction,
                context=json.dumps(context),
                schema=schema,
                task=task.envelope,
            )
        proposal.validate_evidence(item, specification, self.hardware)
        if isinstance(proposal, ExperimentalTestbenchProposal):
            proposal.validate_issues(issues, specification)
        proposal_hash = hashlib.sha256(artifact_content(proposal).encode()).hexdigest()
        binding = (
            proposal.bind(
                item, self.hardware, proposal_sha256=proposal_hash, task_id=task.envelope.task_id
            )
            if proposal.status == "ready"
            else None
        )
        # Publish a completed proposal only after host contract and evidence validation.
        task.save(proposal)
        base = {
            "plan_item_id": item.id,
            "requirement_ids": item.requirement_ids,
            "proposal": ArtifactReference.capture(
                self.artifacts, task.envelope.output_artifact
            ).model_dump(),
        }
        if self.experimental:
            base.update(execution_mode="experimental", engineering_acceptance="pending")
        if binding is None:
            return {**base, "status": "needs_input", "open_questions": proposal.open_questions}
        binding_path = self.artifacts.write(f"binding.{index:03d}.json", binding)
        source_paths = []
        for source_index, source in enumerate(self.hardware.sources):
            path = self.artifacts.path(f"rtl.{source_index:03d}{source.suffix}")
            if path.exists():
                if _hash(path) != source.sha256:
                    raise ValueError("Pinned RTL execution source changed")
            else:
                with path.open("xb") as output:
                    output.write(source.text.encode())
            source_paths.append(path)
        bundle = self.artifacts.root / f"testbench-{index:03d}"
        prepare_testbench(
            self.artifacts.path("specification.json"),
            self.artifacts.path(planning_result["analysis_artifact"]),
            self.artifacts.path(planning_result["plan_artifact"]),
            binding_path,
            source_paths,
            bundle,
            reuse=True,
        )
        receipt_name = f"simulation.{index:03d}.json"
        if self.artifacts.exists(receipt_name):
            receipt = self.artifacts.read(receipt_name)
            expected = {
                **base,
                "binding": ArtifactReference.capture(
                    self.artifacts, binding_path.name
                ).model_dump(),
            }
            receipt_format = "pipeline-case-v2" if self.experimental else "pipeline-case-v1"
            if receipt.get("format") != receipt_format or any(
                receipt.get(key) != value for key, value in expected.items()
            ):
                raise ValueError("Simulation receipt no longer matches its agent inputs")
            result_name = receipt.get("result", "")
            if (
                not re.fullmatch(rf"simulation-{index:03d}-[0-9]+/result\.json", result_name)
                or result_name not in receipt["run_hashes"]
            ):
                raise ValueError("Simulation receipt has no valid result binding")
            for relative, expected_hash in receipt["run_hashes"].items():
                path = self.artifacts.root / relative
                if not path.resolve().is_relative_to(self.artifacts.root.resolve()):
                    raise ValueError("Simulation receipt leaves its run directory")
                if _hash(path) != expected_hash:
                    raise ValueError("Completed simulation evidence changed")
            saved_result = json.loads((self.artifacts.root / result_name).read_text())
            if (
                saved_result["plan_item_id"] != item.id
                or saved_result["status"] != receipt["status"]
                or saved_result["bundle_sha256"] != _hash(bundle / "manifest.json")
            ):
                raise ValueError("Simulation result no longer matches its case receipt")
            if receipt.get("checks_observed") != sum(
                check["status"] != "not_run" for check in saved_result["checks"]
            ):
                raise ValueError("Simulation receipt misstates which checks ran")
            return receipt
        # An interrupted simulator has no completion receipt. Keep its files and
        # retry local execution in a fresh directory, reusing completed agent tasks.
        attempt = 0
        while (run := self.artifacts.root / f"simulation-{index:03d}-{attempt:03d}").exists():
            attempt += 1
        result = simulate_testbench(bundle, run, timeout=self.timeout)
        receipt = {
            "format": "pipeline-case-v2" if self.experimental else "pipeline-case-v1",
            **base,
            "binding": ArtifactReference.capture(self.artifacts, binding_path.name).model_dump(),
            "status": result["status"],
            "checks_observed": sum(check["status"] != "not_run" for check in result["checks"]),
            "result": f"{run.name}/result.json",
            "run_hashes": {
                str(p.relative_to(self.artifacts.root)): _hash(p)
                for p in sorted(run.iterdir())
                if p.is_file()
            },
        }
        self.artifacts.write(receipt_name, receipt)
        return receipt

    def _finish(
        self,
        status: str,
        cases: list[dict[str, Any]],
        unsupported: list[str],
        blocked: list[str],
        plan: VerificationPlan,
        readiness: ExecutionReadiness,
    ) -> dict[str, Any]:
        spending = read_spending(self.artifacts)
        result: dict[str, Any] = {
            "format": "verification-pipeline-result-v3"
            if self.experimental
            else "verification-pipeline-result-v2",
            "status": status,
            "planning_result": ArtifactReference.capture(
                self.artifacts, "result.json"
            ).model_dump(),
            "execution": ArtifactReference.capture(
                self.artifacts, "pipeline-execution.json"
            ).model_dump(),
            "cases": cases,
            "readiness": ArtifactReference.capture(self.artifacts, "readiness.json").model_dump(),
            "readiness_inputs": ArtifactReference.capture(
                self.artifacts, "readiness-inputs.json"
            ).model_dump(),
            "blocked_item_ids": blocked,
            "unsupported_item_ids": unsupported,
            "unexecuted_item_ids": [
                item.id
                for item in plan.items
                if not any(
                    c["plan_item_id"] == item.id and c.get("checks_observed", 0) > 0 for c in cases
                )
            ],
            "blocked_reason": "No simulation case could complete without unresolved issues"
            if status == "blocked"
            else None,
            "human_approved": False,
            "functional_coverage": "not_measured",
            "reported_usd": str(spending.reported),
            "reserved_usd": str(spending.reserved),
            "model_calls": spending.attempts,
        }
        if self.experimental:
            result.update(execution_mode="experimental", engineering_acceptance="pending")
        self.artifacts.write("pipeline-result.json", result)
        self.artifacts.path("pipeline-summary.txt").write_text(
            "Specification -> analyst -> planner -> reviewer -> testbench agent -> simulator\n"
            f"Status: {status}\nPlan items: {len(plan.items)}; "
            f"execution attempts: {sum('result' in case for case in cases)}\n"
            f"Unexecuted items: {len(result['unexecuted_item_ids'])}\n"
            f"Blocked items: {len(blocked)}; unsupported methods: {len(unsupported)}\n"
            + "".join(
                f"  {item.plan_item_id}: {item.status}"
                f"{': ' + ', '.join(item.issue_ids) if item.issue_ids else ''}\n"
                for item in readiness.items
                if item.status != "eligible"
            )
            + "".join(
                f"  {case['plan_item_id']}: {case['status']}"
                + (
                    f" — {'; '.join(case['open_questions'])}"
                    if case["status"] == "needs_input"
                    else f" — {case['result']}"
                )
                + "\n"
                for case in cases
            )
            + "".join(
                f"  {issue.id} ({'blocker' if issue.blocking else 'note'}"
                f"{', scope=' + issue.scope_basis if issue.scope_basis else ''}): "
                f"{issue.description}\n"
                for issue in readiness.issues
            )
            + (
                "Experimental execution; review/readiness blockers remain unresolved.\n"
                if self.experimental
                else ""
            )
            + "Results cover generated directed checks; engineering acceptance remains separate.\n",
            encoding="utf-8",
        )
        return result
