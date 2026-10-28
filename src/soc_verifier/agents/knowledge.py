"""Load an explicit local catalog into an immutable run snapshot; no network."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from soc_verifier.domain.knowledge import KnowledgeEntry, KnowledgeSnapshot
from soc_verifier.storage.artifacts import ArtifactStore


def load_knowledge(catalog: Path, *, allow_proposed: bool = False) -> KnowledgeSnapshot:
    if catalog.stat().st_size > 1_000_000:
        raise ValueError("Knowledge catalog exceeds size limit")
    data = json.loads(catalog.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != "knowledge-catalog-v1":
        raise ValueError("Unknown knowledge catalog format")
    records = data.get("entries")
    if not isinstance(records, list) or not 1 <= len(records) <= 500:
        raise ValueError("Knowledge catalog must contain 1 to 500 entries")
    root = catalog.resolve().parent
    entries = []
    seen = set()
    for record in records:
        if not isinstance(record, dict) or any(
            not isinstance(record.get(key), str) for key in ("id", "file", "status", "sha256")
        ):
            raise ValueError("Malformed knowledge catalog entry")
        identifier = record["id"]
        if identifier in seen:
            raise ValueError("Duplicate knowledge catalog ID")
        seen.add(identifier)
        if record["status"] not in {"proposed", "approved"}:
            raise ValueError("Unknown knowledge review status")
        path = (root / record["file"]).resolve()
        if not path.is_relative_to(root) or path.suffix != ".md":
            raise ValueError("Knowledge files must be Markdown inside the catalog directory")
        if path.stat().st_size > 1_000_000:
            raise ValueError("Knowledge file exceeds size limit")
        # Entry boundaries use IDs, not arbitrary headings inside quoted sources.
        sections = re.split(
            r"(?m)(?=^## (?:K|C|TB|E)[0-9]{2} — )", path.read_text(encoding="utf-8")
        )
        matches = [s.strip() for s in sections if s.startswith(f"## {identifier} — ")]
        if len(matches) != 1:
            raise ValueError("Knowledge entry heading is missing or ambiguous")
        text = matches[0]
        if hashlib.sha256(text.encode()).hexdigest() != record["sha256"]:
            raise ValueError("Knowledge catalog is stale; review the changed entry")
        entry = KnowledgeEntry(
            id=identifier,
            title=text.splitlines()[0].split(" — ", 1)[1],
            status=record["status"],
            reviewer=record.get("reviewer", ""),
            source_path=record["file"],
            text=text,
            sha256=record["sha256"],
        )
        if entry.status == "approved" or allow_proposed:
            entries.append(entry)
    if not entries:
        raise ValueError("No approved knowledge; use --allow-proposed-knowledge only for a trial")
    return KnowledgeSnapshot(allow_proposed=allow_proposed, entries=entries)


def read_knowledge_accesses(artifacts: ArtifactStore) -> list[dict[str, Any]]:
    records = [artifacts.read(path.name) for path in artifacts.root.glob("knowledge-access.*.json")]
    if any(record.get("format") != "knowledge-access-v1" for record in records):
        raise ValueError("Unknown knowledge access record format")
    return sorted(records, key=lambda record: record["created_at"])
