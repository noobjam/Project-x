"""Explicit execution bindings; existing planning contracts are unchanged."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from soc_verifier.domain.models import Contract, NonEmpty, VerificationItem

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")]
Value = Annotated[int, Field(strict=True, ge=0, le=2**64 - 1)]

CLOCK_HALF_PERIOD_NS = 5
CHECK_DELAY_NS = 1
PRE_EDGE_OFFSET_NS = 1


def directed_execution_profile(probes: list["ObservationProbe"] | None = None) -> dict[str, object]:
    """Describe the fixed renderer contract to every specialist in a hardware run."""
    return {
        "format": "directed-execution-v2",
        "generator": "directed-sv-v2",
        "clock_period_ns": 2 * CLOCK_HALF_PERIOD_NS,
        "sample_after_rising_edge_ns": CHECK_DELAY_NS,
        "sample_before_rising_edge_ns": PRE_EDGE_OFFSET_NS,
        "timing_basis": "testbench scheduling, not a DUT timing requirement",
        "stimulus": "literal input values driven while clock is low; omitted inputs hold",
        "observation": "declared output ports and explicitly configured read-only internal probes",
        "checks": "unsigned literal equality before/after the final rising edge of each step",
        "pre_edge_checks": True,
        "internal_signal_checks": bool(probes),
        "internal_probes": [p.model_dump() for p in probes or []],
        "limitations": (
            "single-clock functional RTL; no physical timing guarantees or memory indexing"
        ),
        "multiple_clocks": False,
    }


class Port(Contract):
    name: Identifier
    direction: Literal["input", "output"]
    width: Annotated[int, Field(strict=True, ge=1, le=64)]


class ObservationProbe(Contract):
    """Host-declared path relative to the DUT; no expressions or generated paths."""

    name: Identifier
    path: Annotated[
        str,
        Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}(\.[a-zA-Z_][a-zA-Z0-9_]{0,63}){0,7}$"),
    ]
    width: Annotated[int, Field(strict=True, ge=1, le=64)]


def validate_probes(probes: list[ObservationProbe], ports: list[Port]) -> None:
    names = [p.name for p in probes]
    paths = [p.path for p in probes]
    if len(set(names)) != len(names) or len(set(paths)) != len(paths):
        raise ValueError("Internal probes must have unique names and paths")
    if set(names) & {p.name for p in ports}:
        raise ValueError("Internal probe names must not shadow ports")
    if any(p.path in {port.name for port in ports} for p in probes):
        raise ValueError("Use the declared port name instead of probing a port")


class ExpectedValue(Contract):
    signal: Identifier
    value: Value
    expected_result_index: Annotated[int, Field(strict=True, ge=0)]
    phase: Literal["pre_edge", "post_edge"] = "post_edge"


class CycleStep(Contract):
    """Drive while clock is low; checks select a phase around the last rising edge."""

    description: NonEmpty
    inputs: dict[Identifier, Value]
    cycles: Annotated[int, Field(strict=True, ge=1, le=10_000)] = 1
    checks: Annotated[list[ExpectedValue], Field(max_length=128)]


class TestbenchBinding(Contract):
    format: Literal["directed-testbench-v1", "directed-testbench-v2", "directed-testbench-v3"] = (
        "directed-testbench-v1"
    )
    plan_item_id: NonEmpty
    author: NonEmpty
    origin: Literal["authored", "agent"] = "authored"
    proposal_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")] | None = None
    agent_task_id: NonEmpty | None = None
    top_module: Identifier
    parameters: dict[Identifier, Value]
    ports: Annotated[list[Port], Field(min_length=2, max_length=128)]
    probes: Annotated[list[ObservationProbe], Field(max_length=64)] = Field(default_factory=list)
    clock: Identifier
    initial_inputs: dict[Identifier, Value]
    steps: Annotated[list[CycleStep], Field(min_length=1, max_length=1_000)]
    # Exact plan-question text -> supplied decision; this is not engineering signoff.
    question_resolutions: dict[NonEmpty, NonEmpty]
    unresolved_questions: list[NonEmpty]

    @model_validator(mode="after")
    def validate_signals(self) -> Self:
        if self.format == "directed-testbench-v1":
            if self.origin != "authored" or self.proposal_sha256 or self.agent_task_id:
                raise ValueError("V1 bindings are authored; agent bindings require V2 lineage")
        elif self.format == "directed-testbench-v2" and self.origin != "agent":
            raise ValueError("V2 bindings require agent provenance")
        if self.origin == "agent" and (not self.proposal_sha256 or not self.agent_task_id):
            raise ValueError("Agent bindings require a task and proposal hash")
        if self.origin == "authored" and (self.proposal_sha256 or self.agent_task_id):
            raise ValueError("Authored bindings cannot claim agent provenance")
        if self.format != "directed-testbench-v3" and (
            self.probes or any(c.phase != "post_edge" for s in self.steps for c in s.checks)
        ):
            raise ValueError("Internal and pre-edge observations require a V3 binding")
        validate_probes(self.probes, self.ports)
        probes = {p.name: p for p in self.probes}
        ports = {port.name: port for port in self.ports}
        if len(ports) != len(self.ports):
            raise ValueError("Duplicate port names")
        if self.top_module == "soc_verifier_tb":
            raise ValueError("The testbench module name is reserved")
        clock = ports.get(self.clock)
        if clock is None or clock.direction != "input" or clock.width != 1:
            raise ValueError("Clock must name a one-bit input")
        inputs = {name for name, port in ports.items() if port.direction == "input"}
        inputs.remove(self.clock)
        if set(self.initial_inputs) != inputs:
            raise ValueError("Initialize every non-clock input exactly once")

        def check_value(name: str, value: int, direction: str) -> None:
            port = ports.get(name)
            if port is None or port.direction != direction or name == self.clock:
                raise ValueError("Binding references an invalid signal or direction")
            if value >= 2**port.width:
                raise ValueError("Binding value exceeds the port width")

        for name, value in self.initial_inputs.items():
            check_value(name, value, "input")
        for step in self.steps:
            for name, value in step.inputs.items():
                check_value(name, value, "input")
            for check in step.checks:
                if check.signal in probes:
                    if check.value >= 2 ** probes[check.signal].width:
                        raise ValueError("Binding value exceeds the internal probe width")
                else:
                    check_value(check.signal, check.value, "output")
        if not any(step.checks for step in self.steps):
            raise ValueError("A testbench must contain at least one observable check")
        if sum(step.cycles for step in self.steps) > 100_000:
            raise ValueError("Testbench exceeds the cycle limit")
        return self

    def validate_item(self, item: VerificationItem) -> None:
        if item.id != self.plan_item_id or item.method != "simulation":
            raise ValueError("Binding must target an existing simulation plan item")
        if self.unresolved_questions or set(self.question_resolutions) != set(item.open_questions):
            raise ValueError("Resolve selected plan and binding questions before execution")
        if any(
            check.expected_result_index >= len(item.expected_results)
            for step in self.steps
            for check in step.checks
        ):
            raise ValueError("A check references an unknown expected result")


class TestbenchManifest(Contract):
    format: Literal["testbench-bundle-v1"] = "testbench-bundle-v1"
    generator: Literal["directed-sv-v1", "directed-sv-v2"] = "directed-sv-v1"
    rtl_files: Annotated[list[str], Field(min_length=1, max_length=100)]
    hashes: dict[str, Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]]

    @model_validator(mode="after")
    def validate_files(self) -> Self:
        import re

        if len(set(self.rtl_files)) != len(self.rtl_files) or any(
            re.fullmatch(r"rtl-[0-9]+\.(v|sv)", name) is None for name in self.rtl_files
        ):
            raise ValueError("Invalid RTL snapshot names")
        if set(self.hashes) != {
            "specification.json",
            "analysis.json",
            "plan.json",
            "binding.json",
            "testbench.sv",
            *self.rtl_files,
        }:
            raise ValueError("Bundle must hash exactly its declared input snapshots and testbench")
        return self
