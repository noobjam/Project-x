import hashlib
import json
import shutil
import sys

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from soc_verifier.cli import app
from soc_verifier.domain.models import SpecAnalysis, Specification, VerificationPlan
from soc_verifier.domain.testbench import TestbenchBinding as Binding
from soc_verifier.simulation.iverilog import run_process
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.plan_to_simulation.render import render_testbench
from soc_verifier.workflows.plan_to_simulation.workflow import (
    _check_results,
    _read_bundle,
    prepare_testbench,
    simulate_testbench,
)

pytestmark = pytest.mark.integration
needs_icarus = pytest.mark.skipif(
    not shutil.which("iverilog") or not shutil.which("vvp"), reason="Icarus is not installed"
)
RTL = """`timescale 1ns/1ps
module sample(input clk, rst, input [7:0] d, output reg [7:0] q);
always @(posedge clk) if (rst) q <= 0; else q <= d;
endmodule
"""


@pytest.fixture
def case(tmp_path):
    store = ArtifactStore(tmp_path / "inputs")
    source = Specification.model_validate(
        {
            "document_name": "synthetic-register",
            "sha256": hashlib.sha256(b"fixture").hexdigest(),
            "blocks": [
                {
                    "id": "S1",
                    "kind": "paragraph",
                    "section": "Register",
                    "locator": "paragraph 1",
                    "text": "Reset clears Q; otherwise sample D.",
                }
            ],
            "extraction_warnings": [],
        }
    )
    analysis = SpecAnalysis.model_validate(
        {
            "requirements": [
                {
                    "id": "R1",
                    "statement": "Reset clears Q; otherwise sample D.",
                    "feature": "register",
                    "basis": "explicit",
                    "source_ids": ["S1"],
                    "rationale": "",
                    "open_questions": [],
                }
            ],
            "gaps": [],
        }
    )
    plan = VerificationPlan.model_validate(
        {
            "items": [
                {
                    "id": "V1",
                    "requirement_ids": ["R1"],
                    "feature": "register",
                    "objective": "Exercise reset and sampling",
                    "method": "simulation",
                    "preconditions": [],
                    "stimulus": ["Reset, then drive 5 and clock"],
                    "expected_results": ["Q is zero during reset", "Q samples the value 5"],
                    "coverage_intent": ["directed reset/sample"],
                    "environment_needs": ["clock"],
                    "priority": "high",
                    "open_questions": [],
                }
            ]
        }
    )
    binding = Binding.model_validate(
        {
            "plan_item_id": "V1",
            "author": "synthetic test fixture",
            "top_module": "sample",
            "parameters": {},
            "ports": [
                {"name": "clk", "direction": "input", "width": 1},
                {"name": "rst", "direction": "input", "width": 1},
                {"name": "d", "direction": "input", "width": 8},
                {"name": "q", "direction": "output", "width": 8},
            ],
            "clock": "clk",
            "initial_inputs": {"rst": 1, "d": 0},
            "question_resolutions": {},
            "unresolved_questions": [],
            "steps": [
                {
                    "description": "Reset",
                    "inputs": {},
                    "checks": [{"signal": "q", "value": 0, "expected_result_index": 0}],
                },
                {
                    "description": "Sample input",
                    "inputs": {"rst": 0, "d": 5},
                    "checks": [{"signal": "q", "value": 5, "expected_result_index": 1}],
                },
            ],
        }
    )
    for name, value in (
        ("specification", source),
        ("analysis", analysis),
        ("plan", plan),
        ("binding", binding),
    ):
        store.write(f"{name}.json", value)
    (store.root / "sample.sv").write_text(RTL)
    return store.root


def prepare(case, output):
    return prepare_testbench(
        case / "specification.json",
        case / "analysis.json",
        case / "plan.json",
        case / "binding.json",
        [case / "sample.sv"],
        output,
    )


@pytest.fixture
def observed_case(case):
    edit(
        case,
        "binding",
        lambda b: b.update(
            format="directed-testbench-v3",
            probes=[{"name": "pointer", "path": "state", "width": 4}],
        ),
    )
    edit(
        case,
        "binding",
        lambda b: b["steps"][0]["checks"].append(
            {"signal": "pointer", "value": 0, "expected_result_index": 0, "phase": "post_edge"}
        ),
    )
    edit(
        case,
        "binding",
        lambda b: b["steps"][1]["checks"].extend(
            [
                {"signal": "q", "value": 0, "expected_result_index": 1, "phase": "pre_edge"},
                {"signal": "pointer", "value": 0, "expected_result_index": 1, "phase": "pre_edge"},
                {"signal": "pointer", "value": 1, "expected_result_index": 1, "phase": "post_edge"},
            ]
        ),
    )
    rtl = RTL.replace(
        "endmodule",
        """reg [3:0] state = 9;
always @(posedge clk) if (rst) state <= 0; else state <= state + 1;
endmodule""",
    )
    (case / "sample.sv").write_text(rtl)
    return case


@needs_icarus
@pytest.mark.parametrize("fault,expected", [(False, "passed"), (True, "check_failed")])
def test_pre_edge_and_declared_internal_checks_run_together(
    observed_case, tmp_path, fault, expected
):
    if fault:
        path = observed_case / "sample.sv"
        path.write_text(path.read_text().replace("if (rst) state <= 0", "if (rst) state <= 1"))
    bundle = prepare(observed_case, tmp_path / "observed-bundle")
    result = simulate_testbench(bundle, tmp_path / "observed-run")
    assert result["status"] == expected
    assert result["format"] == "simulation-result-v2"
    if not fault:
        assert len(result["checks"]) == 6
        assert {r["phase"] for r in result["checks"]} == {"pre_edge", "post_edge"}
        assert all(r["status"] == "passed" for r in result["checks"])
        assert json.loads((bundle / "manifest.json").read_text())["generator"] == "directed-sv-v3"
    else:
        assert any(c["signal"] == "pointer" and c["status"] == "failed" for c in result["checks"])


def edit(case, name, change):
    path = case / f"{name}.json"
    value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value))


@needs_icarus
def test_pre_edge_check_detects_fault_hidden_by_post_edge_samples(observed_case, tmp_path):
    path = observed_case / "sample.sv"
    path.write_text(
        path.read_text().replace(
            "always @(posedge clk) if (rst) q <= 0; else q <= d;",
            "always @(*) if (rst) q = 0; else q = d;",
        )
    )
    result = simulate_testbench(prepare(observed_case, tmp_path / "bundle"), tmp_path / "run")
    assert result["status"] == "check_failed"
    failed = [c for c in result["checks"] if c["status"] == "failed"]
    assert [(c["signal"], c["phase"]) for c in failed] == [("q", "pre_edge")]
    assert any(c["status"] == "not_run" for c in result["checks"])


@needs_icarus
@pytest.mark.parametrize(
    "change",
    [
        lambda b: b["probes"][0].update(width=3),
        lambda b: b["probes"][0].update(path="absent"),
    ],
)
def test_internal_probe_mismatch_cannot_pass_with_truncated_values(observed_case, tmp_path, change):
    edit(observed_case, "binding", change)
    result = simulate_testbench(prepare(observed_case, tmp_path / "bundle"), tmp_path / "run")
    assert result["status"] in {"compile_failed", "runtime_failed"}
    assert all(c["status"] == "not_run" for c in result["checks"])


@needs_icarus
@pytest.mark.parametrize("binding_format", ["directed-testbench-v1", "directed-testbench-v3"])
@pytest.mark.parametrize(
    "width,fault,expected",
    [
        (8, False, "passed"),
        (8, True, "check_failed"),
        (3, True, "runtime_failed"),
        (16, False, "runtime_failed"),
    ],
)
def test_output_width_mismatch_cannot_hide_a_hardware_fault(
    case, tmp_path, binding_format, width, fault, expected
):
    def change(binding):
        binding["format"] = binding_format
        next(p for p in binding["ports"] if p["name"] == "q")["width"] = width

    edit(case, "binding", change)
    if fault:
        (case / "sample.sv").write_text(RTL.replace("q <= d;", "q <= d | 8'h80;"))
    result = simulate_testbench(prepare(case, tmp_path / "bundle"), tmp_path / "run")
    assert result["status"] == expected
    if width != 8:
        assert all(c["status"] == "not_run" for c in result["checks"])
        log = (tmp_path / "run" / "simulation.stdout.log").read_text()
        assert "Port width mismatch: q" in log
        assert "SV_COMPLETE" not in log
    elif fault:
        assert result["checks"][1]["observed_hex"] == "85"


@needs_icarus
@pytest.mark.parametrize("port,width", [("d", 3), ("d", 16), ("rst", 2), ("clk", 2)])
def test_input_and_clock_width_mismatches_stop_before_checks(case, tmp_path, port, width):
    if port == "clk":
        # The binding requires a scalar clock; the actual RTL must match it too.
        (case / "sample.sv").write_text(RTL.replace("input clk, rst", "input [1:0] clk, input rst"))
    else:
        edit(
            case,
            "binding",
            lambda b: next(p for p in b["ports"] if p["name"] == port).update(width=width),
        )
    result = simulate_testbench(prepare(case, tmp_path / "bundle"), tmp_path / "run")
    assert result["status"] == "runtime_failed"
    assert all(c["status"] == "not_run" for c in result["checks"])
    assert (
        f"Port width mismatch: {port}" in (tmp_path / "run" / "simulation.stdout.log").read_text()
    )


@needs_icarus
def test_multicycle_steps_sample_only_around_the_last_edge(observed_case, tmp_path):
    def change(binding):
        step = binding["steps"][1]
        step["cycles"] = 3
        step["checks"][1]["value"] = 5  # Q already sampled on earlier edges.
        step["checks"][2]["value"] = 2  # Internal state before the third edge.
        step["checks"][3]["value"] = 3

    edit(observed_case, "binding", change)
    result = simulate_testbench(prepare(observed_case, tmp_path / "bundle"), tmp_path / "run")
    assert result["status"] == "passed" and len(result["checks"]) == 6


@pytest.mark.parametrize(
    "change",
    [
        lambda b: b.update(format="directed-testbench-v1"),
        lambda b: b["probes"][0].update(path="state; $finish;"),
        lambda b: b["probes"][0].update(path="mem[0]"),
        lambda b: b["probes"].append(b["probes"][0]),
        lambda b: b["probes"][0].update(name="q"),
        lambda b: b["probes"][0].update(path="rst"),
        lambda b: b["steps"][0].update(inputs={"pointer": 1}),
        lambda b: b["steps"][0]["checks"][1].update(value=16),
        lambda b: b["steps"][0]["checks"][1].update(signal="invented"),
        lambda b: b["steps"][1]["checks"][1].update(expected_result_index=20),
    ],
)
def test_invalid_observations_fail_before_compilation(observed_case, tmp_path, change):
    edit(observed_case, "binding", change)
    with pytest.raises(ValueError):
        prepare(observed_case, tmp_path / "bundle")
    assert not (tmp_path / "bundle").exists()


@pytest.mark.parametrize(
    "change",
    [
        lambda b: b.update(plan_item_id="unknown"),
        lambda b: b.update(format="unknown-version"),
        lambda b: b.update(clock="q"),
        lambda b: b.update(initial_inputs={"rst": 0}),
        lambda b: b["steps"][0].update(inputs={"q": 0}),
        lambda b: b["steps"][0].update(inputs={"clk": 0}),
        lambda b: b["steps"][0].update(inputs={"unknown": 0}),
        lambda b: b["steps"][0].update(inputs={"d": 256}),
        lambda b: b["steps"][0].update(inputs={"d": True}),
        lambda b: b["steps"][0]["checks"][0].update(expected_result_index=2),
        lambda b: b["steps"][0]["checks"][0].update(signal="d"),
        lambda b: b.update(unresolved_questions=["Reset polarity is unknown"]),
        lambda b: b.update(steps=[{"description": "No checks", "inputs": {}, "checks": []}]),
        lambda b: b.update(top_module="sample); $finish; //"),
    ],
)
def test_invalid_execution_bindings_fail_before_build(case, tmp_path, change):
    edit(case, "binding", change)
    with pytest.raises((ValueError, ValidationError)):
        prepare(case, tmp_path / "bundle")
    assert not (tmp_path / "bundle").exists()


@pytest.mark.parametrize(
    "name,change",
    [
        ("analysis", lambda a: a["requirements"][0].update(source_ids=["fabricated"])),
        ("plan", lambda p: p["items"][0].update(requirement_ids=["fabricated"])),
        ("plan", lambda p: p["items"][0].update(method="inspection")),
        ("plan", lambda p: p["items"][0].update(open_questions=["Which clock?"])),
    ],
)
def test_unbound_evidence_and_questions_block_execution(case, tmp_path, name, change):
    edit(case, name, change)
    with pytest.raises(ValueError):
        prepare(case, tmp_path / "bundle")


def test_question_resolution_and_input_snapshots_are_preserved(case, tmp_path):
    edit(case, "plan", lambda p: p["items"][0].update(open_questions=["Which clock?"]))
    edit(case, "binding", lambda b: b.update(question_resolutions={"Which clock?": "clk"}))
    bundle = prepare(case, tmp_path / "bundle")
    assert (bundle / "plan.json").read_bytes() == (case / "plan.json").read_bytes()
    assert (bundle / "rtl-0.sv").read_bytes() == (case / "sample.sv").read_bytes()
    with pytest.raises(FileExistsError):
        prepare(case, bundle)


def test_changed_bundle_cannot_execute(case, tmp_path):
    bundle = prepare(case, tmp_path / "bundle")
    (bundle / "rtl-0.sv").write_text("changed")
    with pytest.raises(ValueError, match="snapshot changed"):
        simulate_testbench(bundle, tmp_path / "run")
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize(
    "fixture,generator,expected_hash",
    [
        (
            "case",
            "directed-sv-v1",
            "c9cddf103ff27159d7dbf6fdbd2cc296d229a69ddceb42d8ebbe0720ea04e41a",
        ),
        (
            "observed_case",
            "directed-sv-v2",
            "2ba2ce15248cb1339ce84daa20764b62493b66ce70da795106afe5d7297dcc38",
        ),
    ],
)
def test_legacy_bundles_keep_original_bytes_but_require_regeneration_to_execute(
    request, tmp_path, fixture, generator, expected_hash
):
    case = request.getfixturevalue(fixture)
    binding = Binding.model_validate_json((case / "binding.json").read_bytes())
    # Hashes captured from the published implementation before the width fix.
    original = render_testbench(binding, generator=generator).encode()
    assert hashlib.sha256(original).hexdigest() == expected_hash
    bundle = prepare(case, tmp_path / "legacy")
    (bundle / "testbench.sv").write_bytes(original)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["generator"] = generator
    manifest["hashes"]["testbench.sv"] = expected_hash
    manifest_path.write_text(json.dumps(manifest))
    snapshots = {p.name: p.read_bytes() for p in bundle.iterdir()}
    assert _read_bundle(bundle)[0].generator == generator
    with pytest.raises(ValueError, match="Legacy testbench lacks port-width validation"):
        simulate_testbench(bundle, tmp_path / "run")
    assert not (tmp_path / "run").exists()
    assert snapshots == {p.name: p.read_bytes() for p in bundle.iterdir()}
    replacement = prepare(case, tmp_path / "replacement")
    assert json.loads((replacement / "manifest.json").read_text())["generator"] == "directed-sv-v3"
    assert (replacement / "testbench.sv").read_bytes() != original


@pytest.mark.parametrize("upgrade", [False, True])
def test_generator_relabel_cannot_bypass_saved_testbench_validation(case, tmp_path, upgrade):
    bundle = prepare(case, tmp_path / "bundle")
    if upgrade:
        binding = Binding.model_validate_json((case / "binding.json").read_bytes())
        original = render_testbench(binding, generator="directed-sv-v1").encode()
        (bundle / "testbench.sv").write_bytes(original)
        edit(
            bundle,
            "manifest",
            lambda m: m["hashes"].update({"testbench.sv": hashlib.sha256(original).hexdigest()}),
        )
    else:
        edit(bundle, "manifest", lambda m: m.update(generator="directed-sv-v1"))
    with pytest.raises(ValueError, match="Testbench does not match its declared binding"):
        simulate_testbench(bundle, tmp_path / "run")
    assert not (tmp_path / "run").exists()


def test_legacy_generator_must_match_binding_version(observed_case, tmp_path):
    bundle = prepare(observed_case, tmp_path / "bundle")
    edit(bundle, "manifest", lambda m: m.update(generator="directed-sv-v1"))
    with pytest.raises(ValueError, match="generator does not match its binding version"):
        _read_bundle(bundle)


def test_arbitrary_manifest_paths_are_rejected(case, tmp_path):
    bundle = prepare(case, tmp_path / "bundle")
    manifest = json.loads((bundle / "manifest.json").read_text())
    manifest["rtl_files"] = ["../sample.sv"]
    (bundle / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValidationError):
        simulate_testbench(bundle, tmp_path / "run")


@pytest.mark.parametrize(
    "text",
    [
        "SV_COMPLETE\n",
        "SV_CHECK|0|PASS|00\nSV_COMPLETE\n",
        "SV_CHECK|0|PASS|00\nSV_CHECK|1|PASS|05\n",  # all checks, but incomplete test
        "SV_CHECK|0|PASS|00\nSV_CHECK|1|PASS|06\nSV_COMPLETE\n",
        "SV_CHECK|0|PASS|00\nSV_CHECK|1|PASS|xx\nSV_COMPLETE\n",
        "SV_CHECK|0|PASS|00\nSV_CHECK|0|PASS|00\nSV_CHECK|1|PASS|05\nSV_COMPLETE\n",
        "SV_CHECK|500|PASS|00\nSV_COMPLETE\n",
    ],
)
def test_incomplete_or_inconsistent_evidence_never_passes(case, text):
    binding = Binding.model_validate_json((case / "binding.json").read_bytes())
    _, completed = _check_results(binding, text)
    assert not completed


def test_missing_simulator_has_clear_error_without_creating_run(case, tmp_path, monkeypatch):
    bundle = prepare(case, tmp_path / "bundle")
    monkeypatch.setattr("soc_verifier.simulation.iverilog.shutil.which", lambda _: None)
    with pytest.raises(ValueError, match="Install Icarus"):
        simulate_testbench(bundle, tmp_path / "run")
    assert not (tmp_path / "run").exists()


def test_process_timeout_keeps_diagnostics_and_terminates(tmp_path):
    result = run_process([sys.executable, "-c", "while True: pass"], tmp_path, "timeout", 0.1)
    assert result["timed_out"] and result["returncode"] != 0
    assert (tmp_path / "timeout.stderr.log").exists()


@needs_icarus
def test_real_simulator_control_and_mutant_use_identical_testbench(case, tmp_path):
    bundle = prepare(case, tmp_path / "good")
    result = simulate_testbench(bundle, tmp_path / "good-run")
    assert result["status"] == "passed"
    assert result["requirement_ids"] == ["R1"] and result["source_ids"] == ["S1"]
    assert len(result["checks"]) == 2
    assert all(row["status"] == "passed" for row in result["checks"])
    assert result["waveform"] == "waves.vcd"
    assert not result["human_approved"]
    assert result["functional_coverage"] == "not_measured"
    (case / "sample.sv").write_text(RTL.replace("q <= d;", "q <= d + 1;"))
    mutant = prepare(case, tmp_path / "bad")
    assert (mutant / "testbench.sv").read_bytes() == (bundle / "testbench.sv").read_bytes()
    bad = simulate_testbench(mutant, tmp_path / "bad-run")
    assert bad["status"] == "check_failed"
    assert bad["checks"][1]["observed_hex"] == "06"
    assert bad["simulation"]["returncode"] != 0


@needs_icarus
@pytest.mark.parametrize(
    "rtl,status",
    [
        ("not valid Verilog", "compile_failed"),
        (RTL.replace("endmodule", "initial begin #2; $finish; end endmodule"), "runtime_failed"),
        (RTL.replace("endmodule", "initial begin #17; $finish; end endmodule"), "runtime_failed"),
        (RTL.replace("q <= d;", "q <= 8'bx;"), "check_failed"),
        (RTL.replace("endmodule", "initial forever begin end endmodule"), "timed_out"),
    ],
)
def test_real_failure_boundaries(case, tmp_path, rtl, status):
    (case / "sample.sv").write_text(rtl)
    bundle = prepare(case, tmp_path / "bundle")
    result = simulate_testbench(bundle, tmp_path / "run", timeout=1)
    assert result["status"] == status
    assert (tmp_path / "run" / "result.json").exists()


@needs_icarus
def test_cli_generates_and_executes_then_exits_nonzero_on_check_failure(case, tmp_path):
    runner = CliRunner()
    args = [
        "testbench",
        str(case / "plan.json"),
        "--source",
        str(case / "specification.json"),
        "--analysis",
        str(case / "analysis.json"),
        "--binding",
        str(case / "binding.json"),
        "--rtl",
        str(case / "sample.sv"),
        "--output",
        str(tmp_path / "bundle"),
    ]
    built = runner.invoke(app, args)
    assert built.exit_code == 0, built.output
    run = runner.invoke(app, ["simulate", str(tmp_path / "bundle"), "-o", str(tmp_path / "run")])
    assert run.exit_code == 0, run.output
    assert "passed" in run.output
    (case / "sample.sv").write_text(RTL.replace("q <= d;", "q <= d + 1;"))
    prepare(case, tmp_path / "mutant")
    failed = runner.invoke(app, ["simulate", str(tmp_path / "mutant"), "-o", str(tmp_path / "bad")])
    assert failed.exit_code == 1
    assert "check_failed" in failed.output
