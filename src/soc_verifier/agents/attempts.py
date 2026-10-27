"""Invocation-local attribution, propagated by asyncio into transport worker threads."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from soc_verifier.agents.tasks import TaskEnvelope


@dataclass
class Invocation:
    task: TaskEnvelope
    invocation_id: str
    calls: int = 0
    # Ordered tool-call messages, including empty reasoning entries. IDs may repeat
    # across turns or workers; never use a shared dictionary keyed only by tool ID.
    reasoning_history: list[dict[str, Any]] = field(default_factory=list)

    def attribution(self) -> dict[str, Any]:
        return {
            "task_id": self.task.task_id,
            "input_fingerprint": self.task.input_fingerprint,
            "role": self.task.inputs.role,
            "stage": self.task.inputs.stage,
            "invocation_id": self.invocation_id,
        }


current_invocation: ContextVar[Invocation | None] = ContextVar("agent_invocation", default=None)
