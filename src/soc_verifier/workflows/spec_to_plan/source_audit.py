"""Validate and inspect source audits against pinned inputs and actual KB reads."""

import json
from typing import Any

from soc_verifier.agents import instructions as prompts
from soc_verifier.agents.base import AgentExecutor
from soc_verifier.agents.knowledge import read_knowledge_accesses
from soc_verifier.agents.tasks import ArtifactReference, Task, TaskEnvelope, TaskInputs, fingerprint
from soc_verifier.domain.accounting import source_units
from soc_verifier.domain.knowledge import KnowledgeSnapshot
from soc_verifier.domain.models import SpecAnalysis, Specification
from soc_verifier.domain.source_audit import SourceAudit, bound_audit_schema, validate_source_audit
from soc_verifier.domain.source_inventory import (
    SourceInventory,
    inventory_schema,
    validate_inventory,
)
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.accounting import source_context

SOURCE_FIRST = "source-first-v1"


def _names(task: Task) -> tuple[str, str]:
    stem = task.envelope.output_artifact.removesuffix(".json")
    return f"{stem}.inventory.json", f"{stem}.comparison.json"


def _inventory_inputs(task: Task, spec: Specification) -> TaskInputs:
    parent = task.envelope.inputs
    return TaskInputs(
        role="reviewer",
        stage=f"{parent.stage}.inventory",
        assigned_ids=[u.id for u in source_units(spec)],
        evidence={
            key: ref for key, ref in parent.evidence.items() if key in {"source", "knowledge"}
        },
        input_sha256=fingerprint(source_context(spec)),
        instruction_sha256=fingerprint(prompts.INVENTORY_SOURCE),
        schema_sha256=fingerprint(inventory_schema(spec).model_json_schema()),
        versions=parent.versions,
        configuration=parent.configuration,
    )


def _saved_task(artifacts: ArtifactStore, name: str) -> Task:
    envelope = TaskEnvelope.model_validate(
        artifacts.read(f"{name.removesuffix('.json')}.task.json")
    )
    if envelope.output_artifact != name or envelope.inputs.role != "reviewer":
        raise ValueError("Source audit task binding mismatch")
    return Task(artifacts, envelope)


def _source_first_task(
    agents: AgentExecutor, task: Task, spec: Specification
) -> tuple[Task, dict[str, Any]]:
    inventory_name, comparison_name = _names(task)
    inventory_task = Task.bind(task.artifacts, inventory_name, _inventory_inputs(task, spec))
    schema = inventory_schema(spec)
    inventory = inventory_task.load(schema)
    if inventory is None:
        inventory = agents.run(
            role="reviewer",
            instruction=prompts.INVENTORY_SOURCE,
            schema=schema,
            task=inventory_task.envelope,
            context=json.dumps({"specification": source_context(spec)}),
        )
    validate_inventory(inventory, spec)
    inventory_task.save(inventory)
    inputs = task.envelope.inputs.evidence
    analysis = SpecAnalysis.model_validate(inputs["analysis"].read(task.artifacts))
    context = {
        "specification": source_context(spec),
        "source_inventory": inventory.model_dump(mode="json"),
        "analysis": analysis.model_dump(mode="json"),
        "accounting": inputs["source_accounting"].read(task.artifacts),
    }
    comparison = task.child(
        comparison_name,
        stage=f"{task.envelope.inputs.stage}.comparison",
        assigned_ids=task.envelope.inputs.assigned_ids,
        data=context,
        instruction=prompts.AUDIT_SOURCE,
        schema=bound_audit_schema(spec, analysis),
        extra_inputs=[inventory_name],
    )
    return comparison, context


def execute_source_audit(agents: AgentExecutor, task: Task) -> SourceAudit:
    """Use the same audit task for workflow extraction and frozen calibration inputs."""
    inputs = task.envelope.inputs.evidence
    spec = Specification.model_validate(inputs["source"].read(task.artifacts))
    analysis = SpecAnalysis.model_validate(inputs["analysis"].read(task.artifacts))
    schema = bound_audit_schema(spec, analysis)
    audit = task.load(schema)
    if audit is None:
        if task.envelope.inputs.configuration.get("source_audit_mode") == SOURCE_FIRST:
            comparison, context = _source_first_task(agents, task, spec)
        else:
            comparison = task
            context = {
                "specification": source_context(spec),
                "analysis": analysis.model_dump(mode="json"),
                "accounting": inputs["source_accounting"].read(task.artifacts),
            }
        audit = comparison.load(schema)
        if audit is None:
            audit = agents.run(
                role="reviewer",
                instruction=prompts.AUDIT_SOURCE,
                schema=schema,
                task=comparison.envelope,
                context=json.dumps(context),
            )
        _validate_comparison(audit, comparison)
        comparison.save(audit)
    validate_audit_task(audit, task)
    task.save(audit)
    return audit


def validate_audit_task(audit: SourceAudit, task: Task) -> None:
    if task.envelope.inputs.configuration.get("source_audit_mode") == SOURCE_FIRST:
        inventory_name, comparison_name = _names(task)
        spec = Specification.model_validate(
            task.envelope.inputs.evidence["source"].read(task.artifacts)
        )
        inventory_task = _saved_task(task.artifacts, inventory_name)
        inventory_inputs = inventory_task.envelope.inputs
        # Historical reads must not depend on the current prompt/code hash.
        expected_refs = {
            k: v for k, v in task.envelope.inputs.evidence.items() if k in {"source", "knowledge"}
        }
        if (
            inventory_inputs.evidence != expected_refs
            or inventory_inputs.parent_fingerprint is not None
            or inventory_inputs.versions != task.envelope.inputs.versions
            or inventory_inputs.configuration != task.envelope.inputs.configuration
            or inventory_inputs.stage != f"{task.envelope.inputs.stage}.inventory"
            or inventory_inputs.assigned_ids != [u.id for u in source_units(spec)]
        ):
            raise ValueError("Source inventory must be bound only to source and knowledge")
        inventory = inventory_task.load(SourceInventory)
        if inventory is None:
            raise ValueError("Source audit lacks its completed source inventory")
        validate_inventory(inventory, spec)
        comparison = _saved_task(task.artifacts, comparison_name)
        saved = comparison.load(SourceAudit)
        expected_inputs = {
            **task.envelope.inputs.evidence,
            f"extra:{inventory_name}": ArtifactReference.capture(task.artifacts, inventory_name),
        }
        if (
            comparison.envelope.inputs.parent_fingerprint != task.envelope.input_fingerprint
            or comparison.envelope.inputs.evidence != expected_inputs
            or comparison.envelope.inputs.versions != task.envelope.inputs.versions
            or comparison.envelope.inputs.configuration != task.envelope.inputs.configuration
            or comparison.envelope.inputs.instruction_sha256
            != task.envelope.inputs.instruction_sha256
            or comparison.envelope.inputs.schema_sha256 != task.envelope.inputs.schema_sha256
            or comparison.envelope.inputs.assigned_ids != task.envelope.inputs.assigned_ids
            or saved is None
            or saved.model_dump(mode="json") != audit.model_dump(mode="json")
        ):
            raise ValueError("Source audit projection differs from its bound comparison")
        _validate_comparison(audit, comparison)
        return
    _validate_comparison(audit, task)


def _validate_comparison(audit: SourceAudit, task: Task) -> None:
    task.validate_inputs()
    inputs = task.envelope.inputs.evidence
    known: set[str] = set()
    read: set[str] = set()
    if reference := inputs.get("knowledge"):
        knowledge = KnowledgeSnapshot.model_validate(reference.read(task.artifacts))
        known = {e.id for e in knowledge.entries}
        for access in read_knowledge_accesses(task.artifacts):
            if (
                access["task_id"] == task.envelope.task_id
                and access["tool"] == "get_knowledge_entries"
                and access["snapshot_sha256"] == reference.sha256
            ):
                read.update(access["entry_ids"])
    validate_source_audit(
        audit,
        Specification.model_validate(inputs["source"].read(task.artifacts)),
        SpecAnalysis.model_validate(inputs["analysis"].read(task.artifacts)),
        known_knowledge=known,
        read_knowledge=read,
    )


def read_source_audit(artifacts: ArtifactStore, name: str) -> SourceAudit:
    task = _saved_task(artifacts, name)
    audit = task.load(SourceAudit)
    if audit is None:
        raise ValueError("Source audit has no completed output")
    validate_audit_task(audit, task)
    return audit
