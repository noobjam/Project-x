"""Freeze a prepared pilot's source packets and annotation revisions together."""

from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from soc_verifier.domain.models import Contract
from soc_verifier.evaluation.baseline import Digest, _git, _json_bytes
from soc_verifier.evaluation.packets import load_packet, relative_path, require_ignored
from soc_verifier.evaluation.scoring import Annotations, validate_annotations


class PilotInventory(Contract):
    format: Literal["soc-verifier-pilot-v1"] = "soc-verifier-pilot-v1"
    preparation_commit: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    annotations_file: str
    files: dict[str, Digest]

    @model_validator(mode="after")
    def confined_inventory(self) -> Self:
        relative_path(self.annotations_file)
        if not self.annotations_file.startswith("reference/"):
            raise ValueError("Annotations must remain outside runtime source input")
        for name in self.files:
            relative_path(name)
        if not any(name.endswith("/packet.json") for name in self.files):
            raise ValueError("Pilot must contain at least one source packet")
        return self


def freeze_pilot(
    root: Path, *, annotations_file: str = "reference/annotations.v001.json"
) -> PilotInventory:
    root = require_ignored(root)
    relative_path(annotations_file)
    if not annotations_file.startswith("reference/"):
        raise ValueError("Annotations must remain outside runtime source input")
    if _git(Path.cwd(), "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Commit repository changes before freezing the pilot")
    if (root / "inventory.json").exists() or (root / "inventory.sha256").exists():
        raise FileExistsError("Pilot inventory already exists; use a new pilot directory")
    files = {}
    for path in sorted(root.iterdir()):
        if not path.is_dir() or not (path / "packet.json").exists():
            continue
        manifest, _ = load_packet(path)
        if path.name != manifest.case_id:
            raise ValueError("Packet directory does not match its case ID")
        annotations = Annotations.model_validate_json((path / annotations_file).read_bytes())
        validate_annotations(path, annotations)
        for name in ("packet.json", "packet.sha256", manifest.runtime_input, annotations_file):
            target = (path / name).resolve()
            if not target.is_relative_to(root):
                raise ValueError("Pilot file escapes its directory")
            files[f"{path.name}/{name}"] = sha256(target.read_bytes()).hexdigest()
    for name in ("private-selection.json", "opentitan.json"):
        if (root / name).exists():
            files[name] = sha256((root / name).read_bytes()).hexdigest()
    inventory = PilotInventory(
        preparation_commit=_git(Path.cwd(), "rev-parse", "HEAD"),
        annotations_file=annotations_file,
        files=files,
    )
    payload = _json_bytes(inventory.model_dump(mode="json"))
    (root / "inventory.sha256").write_text(sha256(payload).hexdigest() + "\n")
    with (root / "inventory.json").open("xb") as stream:
        stream.write(payload)
    return verify_pilot(root)


def verify_pilot(root: Path) -> PilotInventory:
    root = root.resolve()
    payload = (root / "inventory.json").read_bytes()
    if sha256(payload).hexdigest() != (root / "inventory.sha256").read_text().strip():
        raise ValueError("Pilot inventory checksum mismatch")
    inventory = PilotInventory.model_validate_json(payload)
    for name, digest in inventory.files.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Pilot file changed or escaped its directory")
    for name in inventory.files:
        if name.endswith("/packet.json"):
            packet = root / Path(name).parent
            manifest, _ = load_packet(packet)
            required = {
                f"{packet.name}/{file}"
                for file in ("packet.sha256", manifest.runtime_input, inventory.annotations_file)
            }
            if not required <= inventory.files.keys():
                raise ValueError("Pilot inventory is missing source or annotation files")
            validate_annotations(
                packet,
                Annotations.model_validate_json((packet / inventory.annotations_file).read_bytes()),
            )
    return inventory
