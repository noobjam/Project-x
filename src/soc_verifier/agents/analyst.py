"""Requirements analyst: extract grounded requirements and inspect source evidence."""

from agents import Agent, Model
from pydantic import BaseModel

from soc_verifier.agents.tools import EvidenceContext, get_source_blocks, search_spec


def create_analyst(
    model: Model, instruction: str, output_type: type[BaseModel]
) -> Agent[EvidenceContext]:
    return Agent(
        name="Requirements analyst",
        instructions=instruction,
        model=model,
        output_type=output_type,
        tools=[search_spec, get_source_blocks],
    )
