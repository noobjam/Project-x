"""Freeze private evaluation inputs separately from reference material."""

import json
import platform
import subprocess
from datetime import UTC, datetime
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from soc_verifier.agents.instructions import PROMPT_VERSION
from soc_verifier.domain.models import (
    Contract,
    PlanReview,
    SpecAnalysis,
    Specification,
    VerificationPlan,
)
from soc_verifier.ingestion.docx import ingest_docx
from soc_verifier.settings import Settings

Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
FileRole = Literal["source", "reference", "historical", "provenance"]
SETTINGS_FIELDS = {
    "model",
    "provider",
    "agent_max_turns",
    "max_revisions",
    "max_output_tokens",
    "max_input_characters",
    "request_timeout_seconds",
    "chunk_max_characters",
    "plan_batch_size",
    "batch_workers",
    "max_model_calls",
    "max_cost_usd",
}


class SnapshotFile(Contract):
    path: str
    sha256: Digest
    size_bytes: int = Field(ge=0)
    role: FileRole
    origin: str | None = None

    @model_validator(mode="after")
    def confined_path(self) -> "SnapshotFile":
        path = PurePosixPath(self.path)
        if (
            not self.path
            or not path.parts
            or path.is_absolute()
            or ".." in path.parts
            or "\\" in self.path
            or path.parts[0] != self.role
            or path.as_posix() != self.path
        ):
            raise ValueError("Snapshot paths must remain within their role directory")
        return self


class BaselineManifest(Contract):
    format: Literal["soc-verifier-evaluation-baseline-v1"] = "soc-verifier-evaluation-baseline-v1"
    created_at: str
    git_commit: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    git_tree: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    engine: Literal["openai-agents-v1"] = "openai-agents-v1"
    prompt_version: str
    configuration: dict[str, Any]
    environment: dict[str, str]
    schema_hashes: dict[str, Digest]
    runtime_input: Literal["source/specification.json"] = "source/specification.json"
    reference_status: Literal["imported_reference_unreviewed"] = "imported_reference_unreviewed"
    semantic_acceptance: Literal["pending"] = "pending"
    historical_status: Literal["not_a_controlled_baseline", "not_supplied"]
    files: list[SnapshotFile]

    @model_validator(mode="after")
    def check_inventory(self) -> "BaselineManifest":
        paths = [file.path for file in self.files]
        if len(paths) != len(set(paths)) or self.runtime_input not in paths:
            raise ValueError("Snapshot must have unique files and a source-only runtime input")
        if set(self.configuration) != SETTINGS_FIELDS:
            raise ValueError("Snapshot configuration must match the safe settings allowlist")
        return self


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ValueError("Git provenance check failed")
    return result.stdout.strip()


def _history_files(root: Path, source_hash: str) -> list[Path]:
    manifest = json.loads((root / "manifest.json").read_text())
    result = json.loads((root / "result.json").read_text())
    if manifest.get("specification_sha256") != source_hash:
        raise ValueError("Historical run belongs to a different source document")
    names = ["manifest.json", "result.json", "specification.json"]
    for role in ("analysis", "plan", "review"):
        name = result.get(f"{role}_artifact", "analysis.json" if role == "analysis" else None)
        if not isinstance(name, str) or Path(name).name != name or not name.endswith(".json"):
            raise ValueError("Historical artifact references must be JSON basenames")
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError("Historical artifact references must be distinct")
    return [root / name for name in names]


def freeze_baseline(
    *,
    repository: Path,
    source: Path,
    reference: Path,
    output: Path,
    settings: Settings,
    historical_run: Path | None = None,
) -> BaselineManifest:
    """Create a new ignored bundle. The manifest is the completion marker."""
    root = Path(_git(repository, "rev-parse", "--show-toplevel")).resolve()
    output = output.resolve()
    try:
        relative = output.relative_to(root)
    except ValueError:
        raise ValueError(
            "Evaluation snapshots must be in an ignored repository directory"
        ) from None
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", relative.as_posix()], check=False
    )
    if relative == Path(".") or ignored.returncode:
        raise ValueError("Evaluation snapshots must be in an ignored repository directory")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError(
            "Commit or stash repository changes before freezing a reproducible baseline"
        )
    if not settings.model.strip() or not settings.provider.strip():
        raise ValueError("Set model and provider to freeze the intended baseline configuration")
    if source.suffix.lower() != ".docx" or reference.suffix.lower() != ".xlsx":
        raise ValueError("The initial evaluation freeze requires a DOCX source and XLSX reference")

    source, reference = source.resolve(), reference.resolve()
    source_data, reference_data = source.read_bytes(), reference.read_bytes()
    source_hash = sha256(source_data).hexdigest()
    historical = _history_files(historical_run, source_hash) if historical_run else []
    # Read all inputs before publication; errors cannot create a completed manifest.
    history_data = [(path, path.read_bytes()) for path in historical]
    lock = (root / "uv.lock").read_bytes()
    commit, tree = _git(root, "rev-parse", "HEAD"), _git(root, "rev-parse", "HEAD^{tree}")
    output.mkdir(parents=True, exist_ok=False)
    files: list[SnapshotFile] = []

    def save(path: str, data: bytes, role: FileRole, origin: Path | None = None) -> None:
        entry = SnapshotFile(
            path=path,
            sha256=sha256(data).hexdigest(),
            size_bytes=len(data),
            role=role,
            origin=str(origin.resolve()) if origin else None,
        )
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        files.append(entry)

    save(f"source/{source.name}", source_data, "source", source)
    specification = ingest_docx(output / "source" / source.name)
    save("source/specification.json", _json_bytes(specification.model_dump(mode="json")), "source")
    save(f"reference/{reference.name}", reference_data, "reference", reference)
    for path, data in history_data:
        save(f"historical/{path.name}", data, "historical", path)
    save("provenance/uv.lock", lock, "provenance", root / "uv.lock")
    manifest = BaselineManifest(
        created_at=datetime.now(UTC).isoformat(),
        git_commit=commit,
        git_tree=tree,
        prompt_version=PROMPT_VERSION,
        configuration=settings.model_dump(mode="json", include=SETTINGS_FIELDS),
        environment={
            "python": platform.python_version(),
            **{
                name: version(name)
                for name in (
                    "soc-verifier",
                    "openai",
                    "openai-agents",
                    "pydantic",
                    "python-docx",
                    "lxml",
                )
            },
        },
        schema_hashes={
            model.__name__: sha256(_json_bytes(model.model_json_schema())).hexdigest()
            for model in (Specification, SpecAnalysis, VerificationPlan, PlanReview)
        },
        historical_status="not_a_controlled_baseline" if historical_run else "not_supplied",
        files=files,
    )
    payload = _json_bytes(manifest.model_dump(mode="json"))
    (output / "manifest.sha256").write_text(sha256(payload).hexdigest() + "\n")
    with (output / "manifest.json").open("xb") as stream:
        stream.write(payload)
    return verify_baseline(output)


def verify_baseline(bundle: Path, *, check_originals: bool = False) -> BaselineManifest:
    """Detect drift and path escapes. This is integrity checking, not semantic approval."""
    bundle = bundle.resolve()
    payload = (bundle / "manifest.json").read_bytes()
    if sha256(payload).hexdigest() != (bundle / "manifest.sha256").read_text().strip():
        raise ValueError("Snapshot manifest checksum mismatch")
    manifest = BaselineManifest.model_validate_json(payload)
    for file in manifest.files:
        target = (bundle / file.path).resolve()
        if not target.is_relative_to(bundle):
            raise ValueError("Snapshot file escapes its bundle")
        data = target.read_bytes()
        if len(data) != file.size_bytes or sha256(data).hexdigest() != file.sha256:
            raise ValueError(f"Snapshot content changed: {file.path}")
        if (
            check_originals
            and file.origin
            and sha256(Path(file.origin).read_bytes()).hexdigest() != file.sha256
        ):
            raise ValueError(f"Original input changed: {file.path}")
    Specification.model_validate_json((bundle / manifest.runtime_input).read_bytes())
    return manifest
