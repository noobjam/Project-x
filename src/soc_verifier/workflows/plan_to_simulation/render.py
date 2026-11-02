"""Generate a small directed bench from literal values, never free-form HDL."""

from soc_verifier.domain.testbench import (
    CHECK_DELAY_NS,
    CLOCK_HALF_PERIOD_NS,
    PRE_EDGE_OFFSET_NS,
    CycleStep,
    TestbenchBinding,
)


def render_testbench(binding: TestbenchBinding) -> str:
    extended = binding.format == "directed-testbench-v3"
    # Internal aliases avoid conflicts with ports named 'dut', 'step', etc.
    signals = {port.name: f"signal_{index}" for index, port in enumerate(binding.ports)}
    widths = {port.name: port.width for port in binding.ports}
    signals.update({probe.name: f"dut.{probe.path}" for probe in binding.probes})
    widths.update({probe.name: probe.width for probe in binding.probes})
    clock = signals[binding.clock]
    lines = ["`timescale 1ns/1ps", "module soc_verifier_tb;"]
    for port in binding.ports:
        kind = "reg" if port.direction == "input" else "wire"
        lines.append(f"  {kind} [{port.width - 1}:0] {signals[port.name]};")
    parameters = ", ".join(f".{name}(64'd{value})" for name, value in binding.parameters.items())
    parameter_block = f" #({parameters})" if parameters else ""
    ports = ", ".join(f".{port.name}({signals[port.name]})" for port in binding.ports)
    lines.extend(
        [
            f"  {binding.top_module}{parameter_block} dut ({ports});",
            "  initial begin",
            '    $dumpfile("waves.vcd");',
            "    $dumpvars(0, soc_verifier_tb);",
            f"    {clock} = 0;",
        ]
    )
    for probe in binding.probes:
        lines.extend(
            [
                f"    if ($bits(dut.{probe.path}) != {probe.width})",
                f'      $fatal(1, "Internal probe width mismatch: {probe.name}");',
            ]
        )

    def drive(values: dict[str, int]) -> None:
        for name, value in values.items():
            lines.append(f"    {signals[name]} = {widths[name]}'h{value:x};")

    def checks(step: CycleStep, first_index: int, phase: str) -> None:
        for offset, check in enumerate(step.checks):
            if check.phase != phase:
                continue
            signal = signals[check.signal]
            value = f"{widths[check.signal]}'h{check.value:x}"
            index = first_index + offset
            lines.extend(
                [
                    f"        if ({signal} !== {value}) begin",
                    f'          $display("SV_CHECK|{index}|FAIL|%h", {signal});',
                    '          $fatal(1, "Directed check failed");',
                    "        end",
                    f'        $display("SV_CHECK|{index}|PASS|%h", {signal});',
                ]
            )

    drive(binding.initial_inputs)
    check_index = 0
    for step_index, step in enumerate(binding.steps):
        drive(step.inputs)
        lines.append(
            f"    for (integer cycle_{step_index} = 0; cycle_{step_index} < {step.cycles}; "
            f"cycle_{step_index} = cycle_{step_index} + 1) begin"
        )

        if extended:
            lines.extend(
                [
                    f"      #{CLOCK_HALF_PERIOD_NS - PRE_EDGE_OFFSET_NS};",
                    f"      if (cycle_{step_index} == {step.cycles - 1}) begin",
                ]
            )
            checks(step, check_index, "pre_edge")
            lines.extend(["      end", f"      #{PRE_EDGE_OFFSET_NS} {clock} = 1;"])
        else:
            lines.append(f"      #{CLOCK_HALF_PERIOD_NS} {clock} = 1;")
        lines.extend(
            [
                f"      #{CHECK_DELAY_NS};",
                f"      if (cycle_{step_index} == {step.cycles - 1}) begin",
            ]
        )
        checks(step, check_index, "post_edge")
        check_index += len(step.checks)
        lines.extend(
            ["      end", f"      #{CLOCK_HALF_PERIOD_NS - CHECK_DELAY_NS} {clock} = 0;", "    end"]
        )
    lines.extend(['    $display("SV_COMPLETE");', "    $finish;", "  end", "endmodule", ""])
    return "\n".join(lines)
