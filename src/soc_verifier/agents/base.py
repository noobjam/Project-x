"""A narrow interface: workflow stages never construct provider requests."""

from typing import Literal, Protocol

from pydantic import BaseModel


class ModelResponseError(RuntimeError):
    """The provider did not return a complete usable artifact."""


class OutputLimitError(ModelResponseError):
    """Generation was truncated; callers may partition work, never accept partial JSON."""


AgentRole = Literal["analyst", "planner", "reviewer"]


class AgentExecutor(Protocol):
    def run[T: BaseModel](
        self, *, role: AgentRole, instruction: str, context: str, schema: type[T]
    ) -> T:
        """Return a validated artifact or raise; never return partial output."""
        ...
