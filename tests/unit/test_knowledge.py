import hashlib
import json
from pathlib import Path

import pytest

from soc_verifier.agents.knowledge import load_knowledge
from soc_verifier.domain.knowledge import KnowledgeSnapshot


def test_catalog_requires_explicit_proposed_opt_in(knowledge_catalog, knowledge_snapshot):
    with pytest.raises(ValueError, match="No approved knowledge"):
        load_knowledge(knowledge_catalog)
    assert load_knowledge(knowledge_catalog, allow_proposed=True) == knowledge_snapshot


def test_approval_is_bound_to_reviewer_and_exact_content(knowledge_catalog):
    data = json.loads(knowledge_catalog.read_text())
    data["entries"][0].update(status="approved")
    knowledge_catalog.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="reviewer"):
        load_knowledge(knowledge_catalog)
    data["entries"][0]["reviewer"] = "synthetic-reviewer"
    knowledge_catalog.write_text(json.dumps(data))
    snapshot = load_knowledge(knowledge_catalog)
    assert not snapshot.allow_proposed
    assert snapshot.entries[0].reviewer == "synthetic-reviewer"
    source = knowledge_catalog.parent / "patterns.md"
    source.write_text(source.read_text() + "Changed guidance.")
    with pytest.raises(ValueError, match="stale"):
        load_knowledge(knowledge_catalog)
    assert "Changed guidance" not in snapshot.entries[0].text


@pytest.mark.parametrize("change", ["format", "duplicate", "missing", "status", "hash", "empty"])
def test_catalog_rejects_malformed_entries(knowledge_catalog, change):
    data = json.loads(knowledge_catalog.read_text())
    if change == "format":
        data["format"] = "unknown"
    elif change == "duplicate":
        data["entries"].append(data["entries"][0])
    elif change == "missing":
        del data["entries"][0]["file"]
    elif change == "status":
        data["entries"][0]["status"] = "greenlit"
    elif change == "hash":
        data["entries"][0]["sha256"] = "0" * 64
    else:
        data["entries"] = []
    knowledge_catalog.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_knowledge(knowledge_catalog, allow_proposed=True)


@pytest.mark.parametrize("symlink", [False, True])
def test_catalog_cannot_read_outside_its_directory(knowledge_catalog, symlink):
    data = json.loads(knowledge_catalog.read_text())
    outside = knowledge_catalog.parent.parent / "outside.md"
    outside.write_text("private source or human reference answer")
    if symlink:
        (knowledge_catalog.parent / "linked.md").symlink_to(outside)
        data["entries"][0]["file"] = "linked.md"
    else:
        data["entries"][0]["file"] = "../outside.md"
    knowledge_catalog.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="inside the catalog"):
        load_knowledge(knowledge_catalog, allow_proposed=True)


@pytest.mark.parametrize("change", ["content", "duplicate", "proposed"])
def test_snapshot_revalidates_content_and_policy(knowledge_snapshot, change):
    data = knowledge_snapshot.model_dump()
    if change == "content":
        data["entries"][0]["text"] += " changed"
    elif change == "duplicate":
        data["entries"].append(data["entries"][0])
    else:
        data["allow_proposed"] = False
    with pytest.raises(ValueError):
        KnowledgeSnapshot.model_validate(data)


def test_entry_boundaries_preserve_embedded_source_headings(knowledge_catalog):
    data = json.loads(knowledge_catalog.read_text())
    source = knowledge_catalog.parent / "patterns.md"
    text = source.read_text().strip() + "\n## Quoted source heading\nKeep this limitation."
    source.write_text(text)
    data["entries"][0]["sha256"] = hashlib.sha256(text.encode()).hexdigest()
    knowledge_catalog.write_text(json.dumps(data))
    assert load_knowledge(knowledge_catalog, allow_proposed=True).entries[0].text == text


def test_public_catalog_is_current_and_contains_only_proposed_public_entries():
    snapshot = load_knowledge(Path("docs/knowledge/catalog.json"), allow_proposed=True)
    assert len(snapshot.entries) == 48
    assert {e.status for e in snapshot.entries} == {"proposed"}
    assert not {"E04", "E05", "E06", "E07"} & {e.id for e in snapshot.entries}


def test_knowledge_ids_cannot_replace_specification_evidence(analysis, specification):
    from soc_verifier.domain.models import validate_sources

    altered = analysis.model_copy(
        update={
            "requirements": [analysis.requirements[0].model_copy(update={"source_ids": ["K01"]})]
        }
    )
    with pytest.raises(ValueError):
        validate_sources(altered, specification)
