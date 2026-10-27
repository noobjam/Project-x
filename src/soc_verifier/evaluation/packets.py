"""Small, source-only evaluation projections; never a reference retrieval index."""

import re
import subprocess
import urllib.request
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from soc_verifier.domain.models import Contract, NonEmpty, SourceBlock, Specification
from soc_verifier.evaluation.baseline import Digest, _git, _json_bytes, verify_baseline
from soc_verifier.ingestion.docx import ingest_docx

CaseId = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]


def relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ValueError("Expected a confined relative path")
    if path.as_posix() != value:
        raise ValueError("Expected a canonical relative path")
    return value


def require_ignored(path: Path) -> Path:
    root = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
    target = path.resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError("Evaluation output must be inside an ignored repository directory")
    result = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", target.relative_to(root).as_posix()],
        check=False,
    )
    if result.returncode:
        raise ValueError("Evaluation output must be inside an ignored repository directory")
    return target


class SourceRecord(Contract):
    name: NonEmpty
    sha256: Digest
    adapter: Literal["docx-v1", "text-lines-v1"]
    revision: NonEmpty


class PacketManifest(Contract):
    format: Literal["soc-verifier-packet-v1"] = "soc-verifier-packet-v1"
    case_id: CaseId
    scope: NonEmpty
    runtime_input: Literal["source/specification.json"] = "source/specification.json"
    source_sha256: Digest
    sources: Annotated[list[SourceRecord], Field(min_length=1)]
    block_documents: dict[str, Digest]
    limitations: list[NonEmpty]
    context_state: Literal["proposed", "human_reviewed"] = "proposed"
    context_reviewer: NonEmpty | None = None

    @model_validator(mode="after")
    def checked_context(self) -> Self:
        if self.context_state == "human_reviewed" and not self.context_reviewer:
            raise ValueError("Reviewed context requires an identified reviewer")
        if not set(self.block_documents.values()) <= {source.sha256 for source in self.sources}:
            raise ValueError("Unknown source document in packet")
        return self


class PrivateCase(Contract):
    case_id: CaseId
    scope: NonEmpty
    block_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    limitations: list[NonEmpty]


class PrivateSelection(Contract):
    format: Literal["soc-verifier-private-selection-v1"] = "soc-verifier-private-selection-v1"
    baseline_manifest_sha256: Digest
    cases: Annotated[list[PrivateCase], Field(min_length=1)]


class LineSelection(Contract):
    path: str
    first: int = Field(ge=1)
    last: int = Field(ge=1)

    @model_validator(mode="after")
    def checked_range(self) -> Self:
        relative_path(self.path)
        if self.first > self.last:
            raise ValueError("Reversed source line range")
        return self


class PublicCase(Contract):
    case_id: CaseId
    scope: NonEmpty
    selections: Annotated[list[LineSelection], Field(min_length=1)]
    limitations: list[NonEmpty]


class PublicRecipe(Contract):
    format: Literal["opentitan-packets-v1"] = "opentitan-packets-v1"
    repository: Literal["https://github.com/lowRISC/opentitan"]
    revision: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    files: dict[str, Digest]
    cases: Annotated[list[PublicCase], Field(min_length=1)]

    @model_validator(mode="after")
    def pinned_files(self) -> Self:
        for name in self.files:
            relative_path(name)
        if "LICENSE" not in self.files:
            raise ValueError("Public source inventory must retain its license")
        if any(
            selection.path not in self.files for case in self.cases for selection in case.selections
        ):
            raise ValueError("All selections must refer to pinned source files")
        _unique_cases([case.case_id for case in self.cases])
        return self


def _unique_cases(ids: list[str]) -> None:
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evaluation case IDs")


def write_packet(output: Path, specification: Specification, manifest: PacketManifest) -> None:
    """Write one new immutable source projection. Labels live outside source/."""
    data = _json_bytes(specification.model_dump(mode="json"))
    if sha256(data).hexdigest() != manifest.source_sha256:
        raise ValueError("Packet source hash mismatch")
    if set(manifest.block_documents) != {block.id for block in specification.blocks}:
        raise ValueError("Packet document mapping must cover exactly its source blocks")
    output = require_ignored(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "source").mkdir()
    (output / manifest.runtime_input).write_bytes(data)
    payload = _json_bytes(manifest.model_dump(mode="json"))
    (output / "packet.sha256").write_text(sha256(payload).hexdigest() + "\n")
    (output / "packet.json").write_bytes(payload)


def load_packet(path: Path) -> tuple[PacketManifest, Specification]:
    payload = (path / "packet.json").read_bytes()
    if sha256(payload).hexdigest() != (path / "packet.sha256").read_text().strip():
        raise ValueError("Packet manifest checksum mismatch")
    manifest = PacketManifest.model_validate_json(payload)
    source = (path / manifest.runtime_input).resolve()
    if not source.is_relative_to(path.resolve()):
        raise ValueError("Packet source escapes its directory")
    data = source.read_bytes()
    if sha256(data).hexdigest() != manifest.source_sha256:
        raise ValueError("Packet source hash mismatch")
    specification = Specification.model_validate_json(data)
    if set(manifest.block_documents) != {block.id for block in specification.blocks}:
        raise ValueError("Packet source mapping mismatch")
    return manifest, specification


def prepare_private(baseline: Path, selection: PrivateSelection, output: Path) -> list[Path]:
    manifest = verify_baseline(baseline)
    if (
        sha256((baseline / "manifest.json").read_bytes()).hexdigest()
        != selection.baseline_manifest_sha256
    ):
        raise ValueError("Private selection belongs to another baseline")
    original = next(
        file for file in manifest.files if file.role == "source" and file.path.endswith(".docx")
    )
    specification = ingest_docx(baseline / original.path)
    frozen = Specification.model_validate_json((baseline / manifest.runtime_input).read_bytes())
    if specification != frozen:
        raise ValueError("DOCX adapter changed; freeze a new baseline before selecting packets")
    _unique_cases([case.case_id for case in selection.cases])
    packets = []
    for case in selection.cases:
        ids = set(case.block_ids)
        blocks = [block for block in specification.blocks if block.id in ids]
        if len(ids) != len(case.block_ids) or len(blocks) != len(ids):
            raise ValueError("Private selection contains duplicate or unknown block IDs")
        projected = specification.model_copy(update={"blocks": blocks})
        packet = PacketManifest(
            case_id=case.case_id,
            scope=case.scope,
            source_sha256=sha256(_json_bytes(projected.model_dump(mode="json"))).hexdigest(),
            sources=[
                SourceRecord(
                    name=original.path,
                    sha256=specification.sha256,
                    adapter="docx-v1",
                    revision=manifest.git_commit,
                )
            ],
            block_documents={block.id: specification.sha256 for block in blocks},
            limitations=case.limitations,
        )
        path = output / case.case_id
        write_packet(path, projected, packet)
        packets.append(path)
    return packets


def fetch_public(recipe: PublicRecipe, output: Path) -> None:
    """Explicit public-source download only. Preparation and scoring stay offline."""
    output = require_ignored(output)
    for name, digest in recipe.files.items():
        path = output / name
        if not path.resolve().is_relative_to(output):
            raise ValueError("Public source path escapes its directory")
        if path.exists():
            data = path.read_bytes()
        else:
            url = f"https://raw.githubusercontent.com/lowRISC/opentitan/{recipe.revision}/{name}"
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read()
        if sha256(data).hexdigest() != digest:
            raise ValueError(f"Public source hash mismatch: {name}")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(data)


def prepare_public(recipe: PublicRecipe, source_root: Path, output: Path) -> list[Path]:
    content = {}
    for name, digest in recipe.files.items():
        data = (source_root / name).read_bytes()
        if sha256(data).hexdigest() != digest:
            raise ValueError(f"Public source hash mismatch: {name}")
        content[name] = data.decode("utf-8").splitlines()
    packets = []
    for case in recipe.cases:
        blocks = []
        documents = {}
        used = {}
        for selection in case.selections:
            lines = content[selection.path]
            if selection.last > len(lines):
                raise ValueError("Public selection exceeds its source file")
            digest = recipe.files[selection.path]
            used[selection.path] = digest
            section = selection.path
            for number, line in enumerate(lines, start=1):
                if re.match(r"^#{1,6} ", line):
                    section = line.lstrip("# ")
                if not selection.first <= number <= selection.last or not line:
                    continue
                identifier = f"D{digest}:L{number:05d}"
                if identifier in documents:
                    raise ValueError("Overlapping public selections")
                blocks.append(
                    SourceBlock(
                        id=identifier,
                        kind="table_row" if line.startswith("|") else "paragraph",
                        section=f"{selection.path}: {section}",
                        locator=f"{selection.path}:L{number}",
                        text=line,
                    )
                )
                documents[identifier] = digest
        # This identity is a source-package digest, not a fictional original DOCX hash.
        package_hash = sha256(_json_bytes({"revision": recipe.revision, "files": used})).hexdigest()
        specification = Specification(
            document_name=case.case_id,
            sha256=package_hash,
            blocks=blocks,
            extraction_warnings=case.limitations,
        )
        manifest = PacketManifest(
            case_id=case.case_id,
            scope=case.scope,
            source_sha256=sha256(_json_bytes(specification.model_dump(mode="json"))).hexdigest(),
            sources=[
                SourceRecord(
                    name=name, sha256=digest, adapter="text-lines-v1", revision=recipe.revision
                )
                for name, digest in used.items()
            ],
            block_documents=documents,
            limitations=case.limitations,
        )
        path = output / case.case_id
        write_packet(path, specification, manifest)
        packets.append(path)
    return packets
