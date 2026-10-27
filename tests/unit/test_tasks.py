import json

import pytest
from pydantic import ValidationError

from soc_verifier.agents.tasks import (
    ArtifactReference,
    Task,
    TaskInputs,
    fingerprint,
    runtime_versions,
)
from soc_verifier.domain.models import SpecAnalysis
from soc_verifier.storage.artifacts import ArtifactStore


def bind(artifacts, specification, **changes):
    artifacts.write("specification.json", specification)
    inputs = TaskInputs(
        role="analyst",
        stage="analysis",
        assigned_ids=["P00001"],
        evidence={"source": ArtifactReference.capture(artifacts, "specification.json")},
        input_sha256=fingerprint(specification),
        instruction_sha256=fingerprint("analyze"),
        schema_sha256=fingerprint(SpecAnalysis.model_json_schema()),
        versions=runtime_versions(),
        configuration={},
    ).model_copy(update=changes)
    return Task.bind(artifacts, "analysis.json", inputs)


@pytest.mark.parametrize(
    "field,value",
    [
        ("assigned_ids", ["P00002"]),
        ("input_sha256", "changed"),
        ("instruction_sha256", "changed"),
        ("schema_sha256", "changed"),
        ("configuration", {"max_output_tokens": 512}),
        ("versions", {"prompt": "changed"}),
        ("versions", {"source_processing": "changed"}),
        ("versions", {"tools": "changed"}),
    ],
)
def test_changed_task_input_cannot_reuse_checkpoint(
    tmp_path, specification, analysis, field, value
):
    artifacts = ArtifactStore(tmp_path)
    task = bind(artifacts, specification)
    task.save(analysis)
    with pytest.raises(ValueError, match="inputs or versions changed"):
        bind(artifacts, specification, **{field: value})


def test_content_changed_without_changing_ids_is_rejected(tmp_path, specification, analysis):
    artifacts = ArtifactStore(tmp_path)
    task = bind(artifacts, specification)
    task.save(analysis)
    source = specification.model_dump(mode="json")
    source["blocks"][0]["text"] = "A different reset requirement."
    artifacts.path("specification.json").write_text(json.dumps(source))
    with pytest.raises(ValueError, match="input artifact changed"):
        task.load(SpecAnalysis)


def test_output_tampering_is_not_accepted(tmp_path, specification, analysis):
    artifacts = ArtifactStore(tmp_path)
    task = bind(artifacts, specification)
    task.save(analysis)
    artifacts.path("analysis.json").write_text(analysis.model_dump_json())
    with pytest.raises(ValueError, match="artifact changed"):
        task.load(SpecAnalysis)


def test_atomic_completion_recovers_missing_projection_without_generation(
    tmp_path, specification, analysis, monkeypatch
):
    artifacts = ArtifactStore(tmp_path)
    task = bind(artifacts, specification)
    write = artifacts.write

    def interrupted(name, value):
        if name == "analysis.json":
            raise OSError("interrupted output publication")
        return write(name, value)

    monkeypatch.setattr(artifacts, "write", interrupted)
    with pytest.raises(OSError):
        task.save(analysis)
    assert artifacts.exists("analysis.completed.json")
    monkeypatch.setattr(artifacts, "write", write)
    restored = bind(artifacts, specification)
    assert restored.envelope.task_id == task.envelope.task_id
    assert restored.load(SpecAnalysis) == analysis
    assert artifacts.exists("analysis.json")


@pytest.mark.parametrize(
    "artifact,field",
    [
        ("analysis.task.json", "format"),
        ("analysis.completed.json", "format"),
    ],
)
def test_unknown_contract_versions_fail_explicitly(
    tmp_path, specification, analysis, artifact, field
):
    artifacts = ArtifactStore(tmp_path)
    task = bind(artifacts, specification)
    task.save(analysis)
    data = artifacts.read(artifact)
    data[field] = "unknown-v999"
    artifacts.path(artifact).write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        bind(artifacts, specification).load(SpecAnalysis)


def test_task_metadata_never_rebinds_an_unversioned_checkpoint(tmp_path, specification, analysis):
    artifacts = ArtifactStore(tmp_path)
    artifacts.write("analysis.json", analysis)
    with pytest.raises(ValueError, match="Legacy checkpoint"):
        bind(artifacts, specification)
