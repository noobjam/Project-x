"""Persistently split only output-truncated work; other failures remain explicit."""

import logging
from collections.abc import Callable

from pydantic import BaseModel

from soc_verifier.agents.base import OutputLimitError
from soc_verifier.storage.artifacts import ArtifactStore

logger = logging.getLogger(__name__)


def bounded_call[T: BaseModel, I](
    artifacts: ArtifactStore,
    stem: str,
    items: list[I],
    schema: type[T],
    generate: Callable[[list[I]], T],
    combine: Callable[[T, T], T],
) -> T:
    name = f"{stem}.json"
    if artifacts.exists(name):
        return schema.model_validate(artifacts.read(name))
    split_name = f"{stem}.split.json"
    if not artifacts.exists(split_name):
        try:
            result = generate(items)
        except OutputLimitError:
            if len(items) < 2:
                raise
            artifacts.write(split_name, {"split_at": len(items) // 2, "item_count": len(items)})
            logger.info("stage=split_output_limit artifact=%s items=%s", stem, len(items))
        else:
            artifacts.write(name, result)
            return result
    split = artifacts.read(split_name)
    if split["item_count"] != len(items) or not 0 < split["split_at"] < len(items):
        raise ValueError("Saved batch partition does not match its input")
    middle = split["split_at"]
    left = bounded_call(artifacts, f"{stem}.a", items[:middle], schema, generate, combine)
    right = bounded_call(artifacts, f"{stem}.b", items[middle:], schema, generate, combine)
    result = combine(left, right)
    artifacts.write(name, result)
    return result
