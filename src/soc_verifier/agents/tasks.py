"""Versioned task inputs and immutable, content-bound checkpoints."""

import hashlib
import json
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from platform import python_version
from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from soc_verifier.agents.instructions import PROMPT_VERSION
from soc_verifier.domain.models import Contract
from soc_verifier.storage.artifacts import ArtifactStore, artifact_content

ENGINE_VERSION = "openai-agents-v2"
SOURCE_PROCESSING_VERSION = "docx-v1"


def fingerprint(value: Any) -> str:
    def encode(item: Any) -> Any:
        if isinstance(item, BaseModel):
            return item.model_dump(mode="json")
        raise TypeError("Fingerprint inputs must be JSON values or contracts")

    content = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
        default=encode,
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def runtime_versions() -> dict[str, str]:
    # Hash installed source, not HEAD: documentation-only commits do not change behavior,
    # and editable, uncommitted code cannot masquerade as the last Git revision.
    root = Path(__file__).resolve().parents[1]
    code = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*.py"))
    }
    return {
        "engine": ENGINE_VERSION,
        "code_sha256": fingerprint(code),
        "prompt": PROMPT_VERSION,
        "source_processing": SOURCE_PROCESSING_VERSION,
        "tools": "3",
        "reasoning_replay": "openrouter-v1",
        "openai": version("openai"),
        "openai-agents": version("openai-agents"),
        "pydantic": version("pydantic"),
        "httpx": version("httpx"),
        "python": python_version(),
    }


class ArtifactReference(Contract):
    name: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @classmethod
    def capture(cls, artifacts: ArtifactStore, name: str) -> Self:
        return cls(name=name, sha256=hashlib.sha256(artifacts.path(name).read_bytes()).hexdigest())

    def read(self, artifacts: ArtifactStore) -> dict[str, Any]:
        content = artifacts.path(self.name).read_bytes()
        if hashlib.sha256(content).hexdigest() != self.sha256:
            raise ValueError("Task input artifact changed; start a new run")
        value: dict[str, Any] = json.loads(content)
        return value


class TaskInputs(Contract):
    role: Literal["analyst", "planner", "reviewer"]
    stage: str
    assigned_ids: list[str]
    evidence: dict[str, ArtifactReference]
    input_sha256: str
    instruction_sha256: str
    schema_sha256: str
    versions: dict[str, str]
    configuration: dict[str, Any]
    parent_fingerprint: str | None = None


class TaskEnvelope(Contract):
    format: Literal["agent-task-v1"] = "agent-task-v1"
    task_id: str
    output_artifact: str
    inputs: TaskInputs
    input_fingerprint: str

    @model_validator(mode="after")
    def check_fingerprint(self) -> Self:
        if fingerprint(self.inputs) != self.input_fingerprint:
            raise ValueError("Invalid task input fingerprint")
        return self


class TaskCompletion(Contract):
    format: Literal["task-completion-v1"] = "task-completion-v1"
    task_id: str
    input_fingerprint: str
    output: ArtifactReference
    value: dict[str, Any]


@dataclass(frozen=True)
class Task:
    artifacts: ArtifactStore
    envelope: TaskEnvelope

    @classmethod
    def bind(
        cls,
        artifacts: ArtifactStore,
        name: str,
        inputs: TaskInputs,
    ) -> "Task":
        artifacts.path(name)
        metadata = f"{name.removesuffix('.json')}.task.json"
        expected = fingerprint(inputs)
        if artifacts.exists(metadata):
            envelope = TaskEnvelope.model_validate(artifacts.read(metadata))
            if envelope.input_fingerprint != expected or envelope.output_artifact != name:
                raise ValueError("Task inputs or versions changed; start a new run")
        else:
            if artifacts.exists(name):
                raise ValueError("Legacy checkpoint has no task binding; start a new run")
            envelope = TaskEnvelope(
                task_id=str(uuid4()),
                output_artifact=name,
                inputs=inputs,
                input_fingerprint=expected,
            )
            artifacts.write(metadata, envelope)
        task = cls(artifacts, envelope)
        task.validate_inputs()
        return task

    def validate_inputs(self) -> None:
        for reference in self.envelope.inputs.evidence.values():
            reference.read(self.artifacts)

    def child(
        self,
        name: str,
        *,
        stage: str,
        assigned_ids: list[str],
        data: Any,
        instruction: str,
        schema: type[BaseModel],
        extra_inputs: tuple[str, ...] | list[str] = (),
    ) -> "Task":
        parent = self.envelope.inputs
        references = dict(parent.evidence)
        references.update(
            {
                f"extra:{name}": ArtifactReference.capture(self.artifacts, name)
                for name in extra_inputs
            }
        )
        return Task.bind(
            self.artifacts,
            name,
            TaskInputs(
                role=parent.role,
                stage=stage,
                assigned_ids=assigned_ids,
                evidence=references,
                input_sha256=fingerprint(data),
                instruction_sha256=fingerprint(instruction),
                schema_sha256=fingerprint(schema.model_json_schema()),
                versions=parent.versions,
                configuration=parent.configuration,
                parent_fingerprint=self.envelope.input_fingerprint,
            ),
        )

    def load[T: BaseModel](self, schema: type[T]) -> T | None:
        self.validate_inputs()
        saved = self.completion()
        if saved is None:
            return None
        value = schema.model_validate(saved.value)
        # The receipt commits both result and binding atomically. Restore a missing
        # export projection after interruption without another model call.
        if not self.artifacts.exists(saved.output.name):
            self.artifacts.write(saved.output.name, value)
        return schema.model_validate(saved.output.read(self.artifacts))

    def completion(self) -> TaskCompletion | None:
        """Validate a completion without inference, input reads or disk writes."""
        name = self.envelope.output_artifact
        receipt = f"{name.removesuffix('.json')}.completed.json"
        if not self.artifacts.exists(receipt):
            if not self.artifacts.exists(name):
                return None
            raise ValueError("Checkpoint has no completion binding; start a new run")
        saved = TaskCompletion.model_validate(self.artifacts.read(receipt))
        if (
            saved.task_id != self.envelope.task_id
            or saved.input_fingerprint != self.envelope.input_fingerprint
        ):
            raise ValueError("Incompatible checkpoint completion binding")
        reference = saved.output
        if (
            reference.name != name
            or reference.sha256
            != hashlib.sha256(artifact_content(saved.value).encode("utf-8")).hexdigest()
        ):
            raise ValueError("Checkpoint output reference mismatch")
        if self.artifacts.exists(name):
            reference.read(self.artifacts)
        return saved

    def save(self, value: BaseModel) -> None:
        self.validate_inputs()
        name = self.envelope.output_artifact
        self.artifacts.write(
            f"{name.removesuffix('.json')}.completed.json",
            TaskCompletion(
                task_id=self.envelope.task_id,
                input_fingerprint=self.envelope.input_fingerprint,
                output=ArtifactReference(
                    name=name,
                    sha256=hashlib.sha256(artifact_content(value).encode("utf-8")).hexdigest(),
                ),
                value=value.model_dump(mode="json"),
            ),
        )
        self.artifacts.write(name, value)
