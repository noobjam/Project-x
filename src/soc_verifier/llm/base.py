"""A narrow interface: workflow nodes never construct provider requests."""

from typing import Protocol

from pydantic import BaseModel


class ModelResponseError(RuntimeError):
    """The provider did not return a complete usable artifact."""


class OutputLimitError(ModelResponseError):
    """Generation was truncated; callers may partition work, never accept partial JSON."""


class StructuredLLM(Protocol):
    def generate[T: BaseModel](self, *, instruction: str, context: str, schema: type[T]) -> T:
        """Return a validated artifact or raise; never return partial output."""
        ...
