"""Persistently split only output-truncated work; other failures remain explicit."""

import logging
from collections.abc import Callable

from pydantic import BaseModel

from soc_verifier.agents.base import OutputLimitError
from soc_verifier.agents.tasks import Task, TaskInputs, fingerprint, runtime_versions
from soc_verifier.storage.artifacts import ArtifactStore

logger = logging.getLogger(__name__)


def bounded_call[T: BaseModel, I](
    artifacts: ArtifactStore,
    stem: str,
    items: list[I],
    schema: type[T],
    generate: Callable[[list[I], Task], T],
    combine: Callable[[T, T], T],
    *,
    task: Task | None = None,
) -> T:
    name = f"{stem}.json"
    if task is None:
        task = Task.bind(
            artifacts,
            name,
            TaskInputs(
                role="analyst",
                stage=stem,
                assigned_ids=[],
                evidence={},
                input_sha256=fingerprint(items),
                instruction_sha256=fingerprint(""),
                schema_sha256=fingerprint(schema.model_json_schema()),
                versions=runtime_versions(),
                configuration={},
            ),
        )
    if task.envelope.inputs.input_sha256 != fingerprint(items):
        raise ValueError("Saved batch inputs changed; start a new run")
    cached = task.load(schema)
    if cached is not None:
        return cached
    split_name = f"{stem}.split.json"
    if not artifacts.exists(split_name):
        try:
            result = generate(items, task)
        except OutputLimitError:
            if len(items) < 2:
                raise
            artifacts.write(
                split_name,
                {
                    "format": "task-split-v1",
                    "task_id": task.envelope.task_id,
                    "input_fingerprint": task.envelope.input_fingerprint,
                    "split_at": len(items) // 2,
                    "item_count": len(items),
                },
            )
            logger.info("stage=split_output_limit artifact=%s items=%s", stem, len(items))
        else:
            task.save(result)
            return result
    split = artifacts.read(split_name)
    if (
        split.get("format") != "task-split-v1"
        or split.get("task_id") != task.envelope.task_id
        or split.get("input_fingerprint") != task.envelope.input_fingerprint
        or split["item_count"] != len(items)
        or not 0 < split["split_at"] < len(items)
    ):
        raise ValueError("Saved batch partition does not match its input")
    middle = split["split_at"]

    def child(side: str, part: list[I]) -> T:
        assert task is not None
        inputs = task.envelope.inputs.model_copy(
            update={
                "input_sha256": fingerprint(part),
                "assigned_ids": [str(getattr(item, "id", fingerprint(item))) for item in part],
                "parent_fingerprint": task.envelope.input_fingerprint,
            }
        )
        child_task = Task.bind(artifacts, f"{stem}.{side}.json", inputs)
        return bounded_call(
            artifacts, f"{stem}.{side}", part, schema, generate, combine, task=child_task
        )

    left = child("a", items[:middle])
    right = child("b", items[middle:])
    result = combine(left, right)
    task.save(result)
    return result
