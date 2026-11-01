import json

import pytest

from soc_verifier.agents.tasks import (
    ArtifactReference,
    Task,
    TaskInputs,
    fingerprint,
    runtime_versions,
)
from soc_verifier.domain.accounting import source_units
from soc_verifier.domain.source_audit import SourceAudit, bound_audit_schema
from soc_verifier.domain.source_inventory import (
    PassageReading,
    SourceInventory,
    inventory_schema,
    validate_inventory,
)
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.source_audit import execute_source_audit, read_source_audit
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow


class Scripted:
    def __init__(self, *responses):
        self.configuration = {}
        self.responses = iter(responses)
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        output = next(self.responses)
        if isinstance(output, Exception):
            raise output
        return kwargs["schema"].model_validate(output.model_dump())


@pytest.mark.parametrize("classification,facts", [("behavior", []), ("context", ["fact"])])
def test_passage_classification_cannot_contradict_its_fact_list(classification, facts):
    with pytest.raises(ValueError):
        PassageReading(
            evidence_id="P1:U00000", classification=classification, facts=facts, reason="fixture"
        )


@pytest.mark.parametrize(
    "classification,facts,valid",
    [
        ("behavior", ["Reset clears pending interrupts."], True),
        ("behavior", [], False),
        ("context", [], True),
        ("context", ["This is a section heading."], False),
        ("unresolved", [], True),
        ("unresolved", ["Reset clears pending interrupts."], True),
    ],
)
def test_bound_and_persisted_inventory_accept_the_same_readings(
    specification, classification, facts, valid
):
    payload = {
        "format": "source-inventory-v1",
        "readings": [
            {
                "evidence_id": source_units(specification)[0].id,
                "classification": classification,
                "facts": facts,
                "reason": "Synthetic classification fixture",
            }
        ],
    }
    bound = inventory_schema(specification)
    if valid:
        output = bound.model_validate(payload)
        assert output.model_dump(mode="json") == payload
        assert SourceInventory.model_validate_json(output.model_dump_json()).model_dump() == payload
    else:
        for schema in (bound, SourceInventory):
            with pytest.raises(ValueError):
                schema.model_validate(payload)


def test_historical_source_first_read_does_not_rebuild_generation_schema(
    tmp_path, specification, passage_accounting_draft, source_inventory, clean_audit, monkeypatch
):
    from soc_verifier.agents import instructions
    from soc_verifier.workflows.spec_to_plan import source_audit

    store = ArtifactStore(tmp_path)
    PlanningWorkflow(
        Scripted(passage_accounting_draft, source_inventory, clean_audit),
        store,
        0,
        source_accounting=True,
    ).run(specification, analysis_only=True)

    def changed_schema(_spec):
        raise AssertionError("Historical reads must use persisted contracts")

    monkeypatch.setattr(source_audit, "inventory_schema", changed_schema)
    monkeypatch.setattr(instructions, "PROMPT_VERSION", "future")
    monkeypatch.setattr(instructions, "INVENTORY_SOURCE", "Future generation instructions")
    assert read_source_audit(store, "source-audit.r000.json") == clean_audit


def test_inventory_cannot_access_candidate_and_reuses_completed_work(
    tmp_path, specification, passage_accounting_draft, source_inventory, clean_audit
):
    store = ArtifactStore(tmp_path)
    agents = Scripted(
        passage_accounting_draft, source_inventory, RuntimeError("comparison stopped")
    )
    with pytest.raises(RuntimeError, match="comparison stopped"):
        PlanningWorkflow(agents, store, 0, source_accounting=True).run(
            specification, analysis_only=True
        )
    first, comparison = agents.calls[1:]
    assert issubclass(first["schema"], SourceInventory)
    assert set(first["task"].inputs.evidence) == {"source"}
    assert first["task"].inputs.parent_fingerprint is None
    assert set(json.loads(first["context"])) == {"specification"}
    assert not any("REQ-" in i for i in first["task"].inputs.assigned_ids)
    assert json.loads(comparison["context"])["source_inventory"] == source_inventory.model_dump()
    assert set(comparison["task"].inputs.evidence) == {
        "source",
        "analysis",
        "source_accounting",
        "extra:source-audit.r000.inventory.json",
    }
    resumed = Scripted(clean_audit)
    result = PlanningWorkflow(resumed, store, 0, source_accounting=True).run(analysis_only=True)
    assert result["status"] == "analysis_ready"
    assert len(resumed.calls) == 1 and issubclass(resumed.calls[0]["schema"], SourceAudit)
    assert read_source_audit(store, "source-audit.r000.json") == clean_audit
    # Recover both projections from their receipts without another invocation.
    store.path("source-audit.r000.json").unlink()
    store.path("source-audit.r000.inventory.json").unlink()
    PlanningWorkflow(Scripted(), store, 0, source_accounting=True).run(analysis_only=True)


@pytest.mark.parametrize("change", ["missing", "duplicate", "unknown"])
def test_inventory_rejects_incomplete_or_fabricated_passage_accounting(
    specification, source_inventory, change
):
    row = source_inventory.readings[0]
    readings = (
        []
        if change == "missing"
        else [row, row]
        if change == "duplicate"
        else [row.model_copy(update={"evidence_id": "invented"})]
    )
    with pytest.raises(ValueError, match="exactly once"):
        validate_inventory(
            source_inventory.model_copy(update={"readings": readings}), specification
        )
    with pytest.raises(ValueError):
        inventory_schema(specification).model_validate(
            {"format": "source-inventory-v1", "readings": []}
        )


@pytest.mark.parametrize(
    "file",
    [
        "source-audit.r000.inventory.json",
        "source-audit.r000.comparison.json",
        "source-audit.r000.inventory.task.json",
    ],
)
def test_inventory_or_comparison_tampering_fails_before_inference(
    tmp_path, specification, passage_accounting_draft, source_inventory, clean_audit, file
):
    store = ArtifactStore(tmp_path)
    PlanningWorkflow(
        Scripted(passage_accounting_draft, source_inventory, clean_audit),
        store,
        0,
        source_accounting=True,
    ).run(specification, analysis_only=True)
    store.path(file).write_text("{}")
    with pytest.raises(ValueError):
        PlanningWorkflow(Scripted(), store, 0, source_accounting=True).run(analysis_only=True)


def test_candidate_reference_in_inventory_binding_is_rejected(
    tmp_path, specification, passage_accounting_draft, source_inventory, clean_audit
):
    store = ArtifactStore(tmp_path)
    PlanningWorkflow(
        Scripted(passage_accounting_draft, source_inventory, clean_audit),
        store,
        0,
        source_accounting=True,
    ).run(specification, analysis_only=True)
    metadata = store.read("source-audit.r000.inventory.task.json")
    metadata["inputs"]["evidence"]["analysis"] = ArtifactReference.capture(
        store, "analysis.json"
    ).model_dump()
    metadata["input_fingerprint"] = fingerprint(metadata["inputs"])
    store.path("source-audit.r000.inventory.task.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="only to source"):
        read_source_audit(store, "source-audit.r000.json")


def test_legacy_audit_without_inventory_remains_readable(
    tmp_path, specification, analysis, clean_audit
):
    store = ArtifactStore(tmp_path)
    store.write("specification.json", specification)
    store.write("analysis.json", analysis)
    schema = bound_audit_schema(specification, analysis)
    task = Task.bind(
        store,
        "legacy.json",
        TaskInputs(
            role="reviewer",
            stage="legacy",
            assigned_ids=[r.id for r in analysis.requirements],
            evidence={
                k: ArtifactReference.capture(store, name)
                for k, name in [("source", "specification.json"), ("analysis", "analysis.json")]
            },
            input_sha256=fingerprint({}),
            instruction_sha256=fingerprint("historical"),
            schema_sha256=fingerprint(schema.model_json_schema()),
            versions={"prompt": "12"},
            configuration={},
        ),
    )
    task.save(clean_audit)
    assert read_source_audit(store, "legacy.json") == clean_audit


def test_invalid_inventory_stops_before_comparison(tmp_path, specification, analysis, clean_audit):
    store = ArtifactStore(tmp_path)
    store.write("specification.json", specification)
    store.write("analysis.json", analysis)
    store.write("accounting.json", {})
    task = Task.bind(
        store,
        "audit.json",
        TaskInputs(
            role="reviewer",
            stage="audit",
            assigned_ids=[r.id for r in analysis.requirements],
            evidence={
                k: ArtifactReference.capture(store, name)
                for k, name in [
                    ("source", "specification.json"),
                    ("analysis", "analysis.json"),
                    ("source_accounting", "accounting.json"),
                ]
            },
            input_sha256=fingerprint({}),
            instruction_sha256=fingerprint("unused"),
            schema_sha256=fingerprint({}),
            versions=runtime_versions(),
            configuration={"source_audit_mode": "source-first-v1"},
        ),
    )
    agents = Scripted(SourceInventory(readings=[]), clean_audit)
    with pytest.raises(ValueError):
        execute_source_audit(agents, task)
    assert len(agents.calls) == 1 and not store.exists("audit.completed.json")
    assert task.envelope.inputs.assigned_ids != [u.id for u in source_units(specification)]
