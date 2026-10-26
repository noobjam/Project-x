"""Verification reviewer: investigate evidence, requirement coverage and scenarios."""

from agents import Agent, Model
from pydantic import BaseModel

from soc_verifier.agents.tools import (
    EvidenceContext,
    get_plan_items,
    get_requirements,
    get_source_blocks,
    search_spec,
)


def create_reviewer(
    model: Model, instruction: str, output_type: type[BaseModel]
) -> Agent[EvidenceContext]:
    return Agent(
        name="Verification reviewer",
        instructions=instruction,
        model=model,
        output_type=output_type,
        tools=[search_spec, get_source_blocks, get_requirements, get_plan_items],
    )
