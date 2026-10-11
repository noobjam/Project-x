"""A narrow interface: workflow nodes never construct provider requests."""

from typing import Protocol

from pydantic import BaseModel


class StructuredLLM(Protocol):
    def generate[T: BaseModel](self, *, instruction: str, context: str, schema: type[T]) -> T:
        """Return a validated artifact or raise; never return partial output."""
        ...
