"""Declared hardware configuration and immutable, readable RTL evidence."""

import hashlib
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from soc_verifier.domain.models import Contract, NonEmpty
from soc_verifier.domain.testbench import Identifier, ObservationProbe, Port, Value, validate_probes


class HardwareTarget(Contract):
    format: Literal["hardware-target-v1", "hardware-target-v2"] = "hardware-target-v1"
    top_module: Identifier
    parameters: dict[Identifier, Value]
    ports: Annotated[list[Port], Field(min_length=2, max_length=128)]
    probes: Annotated[list[ObservationProbe], Field(max_length=64)] = Field(default_factory=list)
    clock: Identifier

    @model_validator(mode="after")
    def validate_ports(self) -> Self:
        if self.format == "hardware-target-v1" and self.probes:
            raise ValueError("Internal probes require hardware-target-v2")
        validate_probes(self.probes, self.ports)
        ports = {p.name: p for p in self.ports}
        clock = ports.get(self.clock)
        if len(ports) != len(self.ports):
            raise ValueError("Duplicate hardware ports")
        if clock is None or clock.direction != "input" or clock.width != 1:
            raise ValueError("Hardware clock must be a one-bit input")
        if self.top_module == "soc_verifier_tb":
            raise ValueError("Reserved testbench module name")
        return self


class RTLSource(Contract):
    id: NonEmpty
    suffix: Literal[".v", ".sv"]
    text: Annotated[str, Field(min_length=1, max_length=1_000_000)]
    sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]

    @model_validator(mode="after")
    def check_hash(self) -> Self:
        if hashlib.sha256(self.text.encode()).hexdigest() != self.sha256:
            raise ValueError("RTL snapshot hash does not match its text")
        return self


class HardwareSnapshot(Contract):
    format: Literal["hardware-snapshot-v1"] = "hardware-snapshot-v1"
    target: HardwareTarget
    sources: Annotated[list[RTLSource], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        if len({s.id for s in self.sources}) != len(self.sources):
            raise ValueError("Duplicate RTL source IDs")
        return self

    @classmethod
    def capture(cls, target: HardwareTarget, paths: list[Path]) -> Self:
        sources = []
        for index, path in enumerate(paths):
            if path.suffix not in {".v", ".sv"}:
                raise ValueError("Expected standalone Verilog/SystemVerilog RTL")
            data = path.read_bytes()
            sources.append(
                RTLSource.model_validate(
                    {
                        "id": f"rtl-{index}",
                        "suffix": path.suffix,
                        "text": data.decode("utf-8"),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                )
            )
        return cls(target=target, sources=sources)
