"""Frozen auditor calibration with a shared ledger and no reference-answer access."""

import json
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from soc_verifier.agents import instructions as prompts
from soc_verifier.agents.base import AgentExecutor
from soc_verifier.agents.tasks import (
    ArtifactReference,
    Task,
    TaskInputs,
    fingerprint,
    runtime_versions,
)
from soc_verifier.domain.knowledge import KnowledgeSnapshot
from soc_verifier.domain.models import Contract, SpecAnalysis, Specification
from soc_verifier.domain.source_audit import bound_audit_schema
from soc_verifier.evaluation.baseline import Digest
from soc_verifier.evaluation.packets import require_ignored
from soc_verifier.providers.budget import BudgetExceeded, read_spending
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.accounting import read_accounting
from soc_verifier.workflows.spec_to_plan.source_audit import (
    SOURCE_FIRST,
    execute_source_audit,
    read_source_audit,
)

INPUT_FILES = {
    "source": "specification.json",
    "analysis": "analysis.json",
    "source_accounting": "source-accounting.r000.json",
    "extraction": "obligations.r000.json",
}
ControlID = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]


class ControlInput(Contract):
    id: ControlID
    input_directory: str
    files: dict[str, Digest]

    @model_validator(mode="after")
    def confined(self) -> Self:
        if self.input_directory != f"inputs/{self.id}" or set(self.files) != set(
            INPUT_FILES.values()
        ):
            raise ValueError("Control inputs must use the four allowed files in inputs/<id>")
        return self


class AuditCase(Contract):
    id: ControlID
    inputs: dict[str, ArtifactReference]

    @model_validator(mode="after")
    def bound_names(self) -> Self:
        if set(self.inputs) != set(INPUT_FILES) or any(
            self.inputs[key].name != f"{self.id}.{name}" for key, name in INPUT_FILES.items()
        ):
            raise ValueError("Invalid case input bindings")
        return self


class AuditEvaluation(Contract):
    format: Literal["source-audit-evaluation-v1"] = "source-audit-evaluation-v1"
    input_manifest_sha256: Digest
    cases: Annotated[list[AuditCase], Field(min_length=1)]
    knowledge: ArtifactReference
    versions: dict[str, str]
    configuration: dict[str, Any]

    @model_validator(mode="after")
    def unique_cases(self) -> Self:
        if (
            len({c.id for c in self.cases}) != len(self.cases)
            or self.knowledge.name != "knowledge.json"
        ):
            raise ValueError("Duplicate cases or invalid knowledge binding")
        return self


class CaseOutcome(Contract):
    format: Literal["source-audit-case-result-v1"] = "source-audit-case-result-v1"
    id: ControlID
    task_id: str
    status: Literal["completed", "failed", "interrupted", "budget_exhausted", "not_run"]
    audit: ArtifactReference | None = None
    error_type: str | None = None

    @model_validator(mode="after")
    def completed_output(self) -> Self:
        if (self.status == "completed") != (self.audit is not None):
            raise ValueError("Completed cases require an audit artifact")
        return self


def prepare_audits(
    bundle: Path,
    manifest_sha256: str,
    knowledge_snapshot: Path,
    output: Path,
    settings: Settings,
) -> AuditEvaluation:
    """Validate every candidate before creating a fresh, reference-free snapshot."""
    output = require_ignored(output)
    if output.exists():
        raise FileExistsError("Calibration output already exists")
    content = (bundle / "manifest.json").read_bytes()
    if sha256(content).hexdigest() != manifest_sha256:
        raise ValueError("Control manifest changed")
    manifest = json.loads(content)
    if manifest.get("format") != "source-audit-control-pack-v1":
        raise ValueError("Unknown control pack format")
    controls = [ControlInput.model_validate(c) for c in manifest["controls"]]
    if not controls or len({c.id for c in controls}) != len(controls):
        raise ValueError("Empty or duplicate control inventory")
    # Deliberately do not read manifest['reference'] or any reference/ file.
    snapshots: dict[str, bytes] = {}
    for control in controls:
        root = bundle / control.input_directory
        if root.resolve() != bundle.resolve() / control.input_directory:
            raise ValueError("Control directory escapes its declared input location")
        for name, digest in control.files.items():
            path = root / name
            if path.is_symlink():
                raise ValueError("Control inputs cannot be symlinks")
            value = path.read_bytes()
            if sha256(value).hexdigest() != digest:
                raise ValueError("Control input changed")
            snapshots[f"{control.id}.{name}"] = value
        read_accounting(ArtifactStore(root), "source-accounting.r000.json")
    knowledge = knowledge_snapshot.read_bytes()
    KnowledgeSnapshot.model_validate_json(knowledge)
    snapshots["knowledge.json"] = knowledge
    artifacts = ArtifactStore(output)
    for name, value in snapshots.items():
        with artifacts.path(name).open("xb") as stream:
            stream.write(value)
    reference = ArtifactReference.capture(artifacts, "knowledge.json")
    evaluation = AuditEvaluation(
        input_manifest_sha256=manifest_sha256,
        cases=[
            AuditCase(
                id=c.id,
                inputs={
                    key: ArtifactReference.capture(artifacts, f"{c.id}.{name}")
                    for key, name in INPUT_FILES.items()
                },
            )
            for c in controls
        ],
        knowledge=reference,
        versions=runtime_versions(),
        configuration={
            **settings.agent_configuration(),
            "knowledge": reference.model_dump(),
            "knowledge_consultation": "required-search-read-v1",
        },
    )
    artifacts.write("evaluation.json", evaluation)
    artifacts.write("evaluation.ref.json", ArtifactReference.capture(artifacts, "evaluation.json"))
    return evaluation


def load_audit_evaluation(artifacts: ArtifactStore) -> AuditEvaluation:
    binding = ArtifactReference.model_validate(artifacts.read("evaluation.ref.json"))
    if binding.name != "evaluation.json":
        raise ValueError("Invalid evaluation binding")
    evaluation = AuditEvaluation.model_validate(binding.read(artifacts))
    KnowledgeSnapshot.model_validate(evaluation.knowledge.read(artifacts))
    for case in evaluation.cases:
        for reference in case.inputs.values():
            reference.read(artifacts)
    return evaluation


def run_audits(agents: AgentExecutor, artifacts: ArtifactStore) -> dict[str, Any]:
    """Execute once per frozen case; stop on failure and retain the full denominator."""
    evaluation = load_audit_evaluation(artifacts)
    if (
        evaluation.versions != runtime_versions()
        or evaluation.configuration != agents.configuration
    ):
        raise ValueError("Evaluation runtime or configuration changed; prepare a new condition")
    tasks = []
    cached_outcomes = {}
    for case in evaluation.cases:
        analysis = SpecAnalysis.model_validate(case.inputs["analysis"].read(artifacts))
        spec = Specification.model_validate(case.inputs["source"].read(artifacts))
        task = Task.bind(
            artifacts,
            f"{case.id}.source-audit.json",
            TaskInputs(
                role="reviewer",
                stage=f"audit-control.{case.id}",
                assigned_ids=[r.id for r in analysis.requirements],
                evidence={**case.inputs, "knowledge": evaluation.knowledge},
                input_sha256=fingerprint(case),
                instruction_sha256=fingerprint(prompts.AUDIT_SOURCE),
                schema_sha256=fingerprint(bound_audit_schema(spec, analysis).model_json_schema()),
                versions=evaluation.versions,
                configuration={
                    "configuration": evaluation.configuration,
                    "source_audit_mode": SOURCE_FIRST,
                },
            ),
        )
        # Validate all cached results before any unfinished case can incur cost.
        if task.completion() is not None:
            read_source_audit(artifacts, task.envelope.output_artifact)
        started = f"{case.id}.started.json"
        if artifacts.exists(started) and artifacts.read(started) != {
            "task_id": task.envelope.task_id
        }:
            raise ValueError("Case start binding changed")
        finished = f"{case.id}.result.json"
        if artifacts.exists(finished):
            outcome = CaseOutcome.model_validate(artifacts.read(finished))
            if outcome.id != case.id or outcome.task_id != task.envelope.task_id:
                raise ValueError("Case outcome task binding changed")
            if outcome.audit is not None:
                receipt = task.completion()
                if receipt is None or outcome.audit != receipt.output:
                    raise ValueError("Case outcome lacks its completed audit")
            cached_outcomes[case.id] = outcome
        tasks.append(task)
    if artifacts.exists("evaluation.result.json"):
        saved = artifacts.read("evaluation.result.json")
        expected = [
            cached_outcomes.get(
                case.id,
                CaseOutcome(id=case.id, task_id=task.envelope.task_id, status="not_run"),
            ).model_dump(mode="json")
            for case, task in zip(evaluation.cases, tasks, strict=True)
        ]
        if (
            saved.get("format") != "source-audit-evaluation-result-v1"
            or saved.get("semantic_acceptance") != "unreviewed"
            or saved.get("cases") != expected
            or saved.get("evaluation")
            != ArtifactReference.capture(artifacts, "evaluation.json").model_dump()
            or saved.get("status")
            != ("completed" if all(c["status"] == "completed" for c in expected) else "incomplete")
        ):
            raise ValueError("Evaluation result disagrees with its case outcomes")
        # Never launch more work from a finalized condition. Spending is historical;
        # audit-status reports the current ledger after any later settlement.
        return saved
    outcomes = []
    stopped = False
    for case, task in zip(evaluation.cases, tasks, strict=True):
        started, finished = f"{case.id}.started.json", f"{case.id}.result.json"
        if stopped:
            outcomes.append(
                CaseOutcome(id=case.id, task_id=task.envelope.task_id, status="not_run").model_dump(
                    mode="json"
                )
            )
            continue
        if case.id in cached_outcomes:
            outcome = cached_outcomes[case.id]
        elif artifacts.exists(started) and task.completion() is None:
            # A killed process may have been billed. Never repeat the case implicitly.
            outcome = CaseOutcome(id=case.id, task_id=task.envelope.task_id, status="interrupted")
            artifacts.write(finished, outcome)
        else:
            artifacts.write(started, {"task_id": task.envelope.task_id})
            try:
                execute_source_audit(agents, task)
            except (Exception, KeyboardInterrupt) as error:
                status: Literal["budget_exhausted", "interrupted", "failed"] = (
                    "budget_exhausted"
                    if isinstance(error, BudgetExceeded)
                    else "interrupted"
                    if isinstance(error, KeyboardInterrupt)
                    else "failed"
                )
                outcome = CaseOutcome(
                    id=case.id,
                    task_id=task.envelope.task_id,
                    status=status,
                    error_type=type(error).__name__,
                )
            else:
                outcome = CaseOutcome(
                    id=case.id,
                    task_id=task.envelope.task_id,
                    status="completed",
                    audit=ArtifactReference.capture(artifacts, task.envelope.output_artifact),
                )
            artifacts.write(finished, outcome)
        outcomes.append(outcome.model_dump(mode="json"))
        stopped = outcome.status != "completed"
    spending = read_spending(artifacts)
    report = {
        "format": "source-audit-evaluation-result-v1",
        "evaluation": ArtifactReference.capture(artifacts, "evaluation.json").model_dump(),
        "status": "incomplete" if stopped else "completed",
        "semantic_acceptance": "unreviewed",
        "cases": outcomes,
        "spending_at_completion": {
            "model_calls": spending.attempts,
            "reported_usd": str(spending.reported),
            "reserved_usd": str(spending.reserved),
            "unsettled_calls": spending.unsettled_calls,
        },
    }
    artifacts.write("evaluation.result.json", report)
    return report
