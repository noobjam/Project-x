"""Plan -> bound directed bench -> local execution, with immutable lineage."""

import hashlib
import re
from pathlib import Path
from typing import Any

from soc_verifier.domain.models import (
    SpecAnalysis,
    Specification,
    VerificationItem,
    VerificationPlan,
    validate_sources,
    validate_traceability,
)
from soc_verifier.domain.testbench import TestbenchBinding, TestbenchManifest
from soc_verifier.simulation.iverilog import read_log, run_process, tools
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.plan_to_simulation.render import render_testbench


def _validate(files: dict[str, bytes]) -> tuple[TestbenchBinding, VerificationItem, list[str]]:
    spec = Specification.model_validate_json(files["specification.json"])
    analysis = SpecAnalysis.model_validate_json(files["analysis.json"])
    plan = VerificationPlan.model_validate_json(files["plan.json"])
    binding = TestbenchBinding.model_validate_json(files["binding.json"])
    validate_sources(analysis, spec)
    validate_traceability(plan, analysis)
    item = next((item for item in plan.items if item.id == binding.plan_item_id), None)
    if item is None:
        raise ValueError("Binding targets an unknown plan item")
    binding.validate_item(item)
    source_ids = sorted(
        {
            source
            for requirement in analysis.requirements
            if requirement.id in item.requirement_ids
            for source in requirement.source_ids
        }
    )
    return binding, item, source_ids


def prepare_testbench(
    specification: Path,
    analysis: Path,
    plan: Path,
    binding: Path,
    rtl: list[Path],
    output: Path,
    *,
    reuse: bool = False,
) -> Path:
    files = {
        "specification.json": specification.read_bytes(),
        "analysis.json": analysis.read_bytes(),
        "plan.json": plan.read_bytes(),
        "binding.json": binding.read_bytes(),
    }
    configuration, _, _ = _validate(files)
    rtl_names = []
    for index, path in enumerate(rtl):
        if path.suffix not in {".v", ".sv"}:
            raise ValueError("This slice supports standalone Verilog/SystemVerilog source files")
        name = f"rtl-{index}{path.suffix}"
        rtl_names.append(name)
        files[name] = path.read_bytes()
    files["testbench.sv"] = render_testbench(configuration).encode()
    manifest = TestbenchManifest(
        generator="directed-sv-v3",
        rtl_files=rtl_names,
        hashes={name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
    )
    if reuse and output.exists():
        saved, *_ = _read_bundle(output)
        if saved != manifest:
            raise ValueError("Existing testbench bundle belongs to different inputs")
        return output
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        with (output / name).open("xb") as stream:
            stream.write(data)
    ArtifactStore(output).write("manifest.json", manifest)
    return output


def _read_bundle(
    bundle: Path,
) -> tuple[TestbenchManifest, TestbenchBinding, VerificationItem, list[str], dict[str, bytes]]:
    manifest = TestbenchManifest.model_validate_json((bundle / "manifest.json").read_bytes())
    files = {}
    for name, expected_hash in manifest.hashes.items():
        path = bundle / name
        if path.is_symlink():
            raise ValueError("Bundle snapshots must be regular files, not symlinks")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected_hash:
            raise ValueError("Bundle snapshot changed; prepare a new testbench bundle")
        files[name] = data
    binding, item, sources = _validate(files)
    if files["testbench.sv"] != render_testbench(binding, generator=manifest.generator).encode():
        raise ValueError("Testbench does not match its declared binding and generator")
    return manifest, binding, item, sources, files


def _check_results(binding: TestbenchBinding, text: str) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    for step_index, step in enumerate(binding.steps):
        for check in step.checks:
            rows.append(
                {
                    "index": len(rows),
                    "step_index": step_index,
                    "description": step.description,
                    **check.model_dump(
                        exclude={"phase"} if binding.format != "directed-testbench-v3" else set()
                    ),
                    "status": "not_run",
                    "observed_hex": None,
                }
            )
    seen: set[int] = set()
    valid = True
    for line in text.splitlines():
        if not line.startswith("SV_CHECK|"):
            continue
        match = re.fullmatch(r"SV_CHECK\|(\d+)\|(PASS|FAIL)\|([0-9a-fA-FxXzZ]+)", line)
        if match is None:
            valid = False
            continue
        index = int(match[1])
        if index >= len(rows) or index in seen:
            valid = False
            continue
        seen.add(index)
        row = rows[index]
        row["observed_hex"] = match[3]
        agrees = not re.search("[xz]", match[3], re.I) and int(match[3], 16) == row["value"]
        row["status"] = "passed" if match[2] == "PASS" and agrees else "failed"
        valid &= (match[2] == "PASS") == bool(agrees)
    complete = text.splitlines().count("SV_COMPLETE") == 1
    return rows, valid and complete and all(row["status"] == "passed" for row in rows)


def simulate_testbench(bundle: Path, output: Path, *, timeout: float = 10) -> dict[str, Any]:
    if not 0 < timeout <= 120:
        raise ValueError("Simulator timeout must be between 0 and 120 seconds per process")
    manifest, binding, item, sources, files = _read_bundle(bundle)
    if manifest.generator != "directed-sv-v3":
        raise ValueError(
            "Legacy testbench lacks port-width validation; prepare a new bundle before simulation"
        )
    compiler, runtime = tools()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    # Execute the verified bytes, not paths another process could change after validation.
    for name, data in files.items():
        with (output / name).open("xb") as stream:
            stream.write(data)
    artifacts = ArtifactStore(output)
    artifacts.write("manifest.json", manifest)
    versions = {}
    for label, tool in (("compiler-version", compiler), ("runtime-version", runtime)):
        receipt = run_process([tool, "-V"], output, label, timeout)
        version_text = read_log(output / receipt["stdout"]) + read_log(output / receipt["stderr"])
        receipt["version"] = version_text.splitlines()[0] if version_text else "unavailable"
        versions[label] = receipt
    compile_receipt = run_process(
        [
            compiler,
            "-g2012",
            "-s",
            "soc_verifier_tb",
            "-o",
            "simulation.vvp",
            *manifest.rtl_files,
            "testbench.sv",
        ],
        output,
        "compile",
        timeout,
    )
    simulation = None
    text = ""
    status = "compile_failed"
    if compile_receipt["timed_out"]:
        status = "timed_out"
    elif compile_receipt["returncode"] == 0:
        simulation = run_process([runtime, "simulation.vvp"], output, "simulation", timeout)
        status = "timed_out" if simulation["timed_out"] else "runtime_failed"
        try:
            text = read_log(output / "simulation.stdout.log")
        except ValueError:
            text = ""  # Full logs remain on disk; missing evidence cannot pass.
    checks, completed = _check_results(binding, text)
    if simulation is not None and not simulation["timed_out"]:
        if simulation["returncode"] == 0 and completed:
            status = "passed"
        elif any(row["status"] == "failed" for row in checks):
            status = "check_failed"
    result: dict[str, Any] = {
        "format": "simulation-result-v2"
        if binding.format == "directed-testbench-v3"
        else "simulation-result-v1",
        "status": status,
        "plan_item_id": item.id,
        "requirement_ids": item.requirement_ids,
        "source_ids": sources,
        "binding_origin": binding.origin,
        "binding_author": binding.author,
        "human_approved": False,
        "bundle_sha256": hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest(),
        "tools": versions,
        "compile": compile_receipt,
        "simulation": simulation,
        "checks": checks,
        "expected_results": item.expected_results,
        "unbound_expected_results": sorted(
            set(range(len(item.expected_results)))
            - {row["expected_result_index"] for row in checks}
        ),
        "functional_coverage": "not_measured",
        "waveform": "waves.vcd" if (output / "waves.vcd").is_file() else None,
    }
    artifacts.write("result.json", result)
    (output / "summary.txt").write_text(
        f"Plan item: {item.id}\nStatus: {status}\n"
        f"Checks: {sum(row['status'] == 'passed' for row in checks)} passed, "
        f"{sum(row['status'] == 'failed' for row in checks)} failed, "
        f"{sum(row['status'] == 'not_run' for row in checks)} not run\n"
        f"Unbound expected results: {len(result['unbound_expected_results'])}\n"
        "Scope: selected directed checks; functional coverage is not measured.\n",
        encoding="utf-8",
    )
    return result
