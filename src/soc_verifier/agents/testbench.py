"""Testbench specialist: grounded executable proposals, with read-only evidence tools."""

from agents import Agent, Model
from pydantic import BaseModel

from soc_verifier.agents.tools import (
    EvidenceContext,
    get_plan_items,
    get_requirements,
    get_source_blocks,
    read_rtl,
    search_spec,
)


def create_testbench(
    model: Model, instruction: str, output_type: type[BaseModel]
) -> Agent[EvidenceContext]:
    return Agent(
        name="Testbench agent",
        instructions=instruction,
        model=model,
        output_type=output_type,
        tools=[search_spec, get_source_blocks, get_requirements, get_plan_items, read_rtl],
    )
