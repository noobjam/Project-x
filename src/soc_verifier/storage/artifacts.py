"""Immutable local JSON artifacts, published atomically."""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from pydantic import BaseModel


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        if Path(name).name != name or name in {"", ".", ".."}:
            raise ValueError("Artifact names must be single file names")
        return self.root / name

    def exists(self, name: str) -> bool:
        return self.path(name).exists()

    def read(self, name: str) -> dict[str, Any]:
        data: dict[str, Any] = json.loads(self.path(name).read_text(encoding="utf-8"))
        return data

    def write(self, name: str, value: BaseModel | dict[str, Any]) -> Path:
        content = artifact_content(value)
        target = self.path(name)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.root, delete=False) as file:
            temporary = Path(file.name)
            try:
                file.write(content)
                file.flush()
                os.fsync(file.fileno())
                try:
                    os.link(temporary, target)
                except FileExistsError:
                    if target.read_text(encoding="utf-8") != content:
                        raise FileExistsError(f"Refusing to replace artifact: {target}") from None
            finally:
                temporary.unlink(missing_ok=True)
        return target


def artifact_content(value: BaseModel | dict[str, Any]) -> str:
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
