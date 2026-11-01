"""An independent source reading, never a proof of semantic completeness."""

from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import Field, create_model, model_validator

from soc_verifier.domain.accounting import source_units
from soc_verifier.domain.models import Contract, NonEmpty, Specification


class PassageReading(Contract):
    evidence_id: NonEmpty
    classification: Literal["behavior", "context", "unresolved"]
    facts: list[NonEmpty]
    reason: NonEmpty

    @model_validator(mode="after")
    def classification_matches_facts(self) -> Self:
        if self.classification == "behavior" and not self.facts:
            raise ValueError("Behavior passages require explicit facts")
        if self.classification == "context" and self.facts:
            raise ValueError("Context passages cannot hide extracted behavior")
        return self


class SourceInventory(Contract):
    format: Literal["source-inventory-v1"] = "source-inventory-v1"
    readings: list[PassageReading]


# Generation-only alternatives expose the existing host validator's rules.
# Persisted v1 readings and historical readers keep the same fields/meaning.
class _BehaviorReading(PassageReading):
    classification: Literal["behavior"]
    facts: list[NonEmpty] = Field(min_length=1)


class _ContextReading(PassageReading):
    classification: Literal["context"]
    facts: list[NonEmpty] = Field(max_length=0)


class _UnresolvedReading(PassageReading):
    classification: Literal["unresolved"]


def inventory_schema(spec: Specification) -> type[SourceInventory]:
    units = source_units(spec)
    if not units:
        raise ValueError("Source inventory requires non-whitespace passages")
    factory: Any = StrEnum
    passage: Any = factory("InventoryPassageID", {f"P{i}": u.id for i, u in enumerate(units)})
    behavior: Any = create_model(
        "BoundBehaviorReading", __base__=_BehaviorReading, evidence_id=(passage, ...)
    )
    context: Any = create_model(
        "BoundContextReading", __base__=_ContextReading, evidence_id=(passage, ...)
    )
    unresolved: Any = create_model(
        "BoundUnresolvedReading", __base__=_UnresolvedReading, evidence_id=(passage, ...)
    )
    constrained: Any = behavior | context | unresolved
    return create_model(
        "SourceInventory",
        __base__=SourceInventory,
        readings=(list[constrained], Field(min_length=len(units), max_length=len(units))),
    )


def validate_inventory(inventory: SourceInventory, spec: Specification) -> None:
    expected = {u.id for u in source_units(spec)}
    actual = [row.evidence_id for row in inventory.readings]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError("Source inventory must classify every supplied passage exactly once")
