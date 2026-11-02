"""Bounded local Icarus processes. Inputs are explicitly supplied trusted RTL."""

import os
import shutil
import signal
import subprocess
from contextlib import suppress
from pathlib import Path
from time import monotonic
from typing import Any


def tools() -> tuple[str, str]:
    compiler, runtime = shutil.which("iverilog"), shutil.which("vvp")
    if compiler is None or runtime is None:
        raise ValueError("Install Icarus Verilog (iverilog and vvp) before simulation")
    return compiler, runtime


def run_process(arguments: list[str], output: Path, label: str, timeout: float) -> dict[str, Any]:
    """Keep logs on disk; terminate the process group if the deadline expires."""
    started = monotonic()
    timed_out = False
    with (
        (output / f"{label}.stdout.log").open("xb") as stdout,
        (output / f"{label}.stderr.log").open("xb") as stderr,
        subprocess.Popen(
            arguments, cwd=output, stdout=stdout, stderr=stderr, start_new_session=True
        ) as process,
    ):
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        return {
            "arguments": arguments,
            "returncode": process.returncode,
            "timed_out": timed_out,
            "elapsed_seconds": round(monotonic() - started, 6),
            "stdout": f"{label}.stdout.log",
            "stderr": f"{label}.stderr.log",
        }


def read_log(path: Path) -> str:
    # RTL can itself print. Keep unbounded diagnostic content out of the result parser.
    if path.stat().st_size > 1_000_000:
        raise ValueError("Simulator log exceeds the report limit; inspect the local log")
    return path.read_text(encoding="utf-8", errors="replace")
