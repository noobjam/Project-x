"""Explicit legacy result reads; domain models continue to validate their V1 schemas."""

from typing import Any

from soc_verifier.storage.artifacts import ArtifactStore


def read_result(artifacts: ArtifactStore) -> dict[str, Any]:
    result = artifacts.read("result.json")
    # The earliest exports predate the version field. Never reinterpret an unknown version.
    if result.get("schema_version", "1.0") not in {"1.0", "2.0"}:
        raise ValueError("Unknown run result schema version")
    return result
