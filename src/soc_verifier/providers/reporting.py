"""Read-only task accounting, including explicit unavailable attribution for V1 runs."""

from decimal import Decimal
from typing import Any

from soc_verifier.agents.tasks import Task, TaskEnvelope
from soc_verifier.providers.budget import read_spending
from soc_verifier.storage.artifacts import ArtifactStore


def read_task_report(artifacts: ArtifactStore) -> dict[str, Any]:
    tasks = {}
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(artifacts.root.glob("*.task.json")):
        task = TaskEnvelope.model_validate(artifacts.read(path.name))
        if task.task_id in tasks:
            raise ValueError("Duplicate task identity")
        tasks[task.task_id] = task
        rows[task.task_id] = _row(task.task_id, task.inputs.role, task.inputs.stage)
        rows[task.task_id]["output_artifact"] = task.output_artifact
        rows[task.task_id]["input_fingerprint"] = task.input_fingerprint
        if Task(artifacts, task).completion() is not None:
            rows[task.task_id]["status"] = "completed"
    for path in sorted(artifacts.root.glob("invocation.*.json")):
        if path.name.endswith(".result.json"):
            continue
        invocation = artifacts.read(path.name)
        if invocation.get("format") != "agent-invocation-v1":
            raise ValueError("Unknown invocation format")
        row = _attributed_row(invocation, tasks, rows)
        row["invocations"] += 1
        result_name = path.name.removesuffix(".json") + ".result.json"
        if artifacts.exists(result_name):
            result = artifacts.read(result_name)
            if result.get("format") != "agent-invocation-result-v1":
                raise ValueError("Unknown invocation result format")
            if result["status"] == "failed":
                row["failed_invocations"] += 1
        else:
            row["unfinished_invocations"] += 1
    for path in sorted(artifacts.root.glob("cost-reserved.*.json")):
        reservation = artifacts.read(path.name)
        if "format" not in reservation:
            row = rows.setdefault("unavailable", _row(None, "unavailable", "legacy"))
        elif reservation["format"] == "task-reservation-v1":
            row = _attributed_row(reservation, tasks, rows)
        else:
            raise ValueError("Unknown cost reservation format")
        row["model_calls"] += 1
        settled = f"cost-settled.{int(reservation['attempt']):05d}.json"
        if artifacts.exists(settled):
            row["reported_usd"] += Decimal(artifacts.read(settled)["cost_usd"])
        else:
            row["reserved_usd"] += Decimal(reservation["reserved_usd"])
            row["unsettled_calls"] += 1
    total = read_spending(artifacts)
    if (
        sum((r["reported_usd"] for r in rows.values()), Decimal(0)) != total.reported
        or sum((r["reserved_usd"] for r in rows.values()), Decimal(0)) != total.reserved
    ):
        raise ValueError("Task totals do not reconcile to the run ledger")
    for row in rows.values():
        for key in ("reported_usd", "reserved_usd"):
            row[key] = str(row[key])
        if row["status"] != "completed":
            if row["unfinished_invocations"]:
                row["status"] = "running_or_interrupted"
            elif row["failed_invocations"]:
                row["status"] = "failed_or_split"
            elif row["invocations"]:
                row["status"] = "returned_not_accepted"
    return {
        "format": "task-spending-report-v1",
        "attribution": ("partial" if "unavailable" in rows else "available")
        if tasks
        else "unavailable",
        "reported_usd": str(total.reported),
        "reserved_usd": str(total.reserved),
        "unsettled_calls": total.unsettled_calls,
        "tasks": list(rows.values()),
    }


def _row(task_id: str | None, role: str, stage: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "role": role,
        "stage": stage,
        "status": "pending" if task_id else "unavailable",
        "model_calls": 0,
        "invocations": 0,
        "failed_invocations": 0,
        "unfinished_invocations": 0,
        "unsettled_calls": 0,
        "reported_usd": Decimal(0),
        "reserved_usd": Decimal(0),
    }


def _attributed_row(
    record: dict[str, Any],
    tasks: dict[str, TaskEnvelope],
    rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    task = tasks.get(record.get("task_id", ""))
    if task is None or any(
        record.get(key) != expected
        for key, expected in {
            "input_fingerprint": task.input_fingerprint,
            "role": task.inputs.role,
            "stage": task.inputs.stage,
        }.items()
    ):
        raise ValueError("Accounting record does not match its task")
    return rows[task.task_id]
