"""Validate and inspect source audits against pinned inputs and actual KB reads."""

from soc_verifier.agents.knowledge import read_knowledge_accesses
from soc_verifier.agents.tasks import Task, TaskEnvelope
from soc_verifier.domain.knowledge import KnowledgeSnapshot
from soc_verifier.domain.models import SpecAnalysis, Specification
from soc_verifier.domain.source_audit import SourceAudit, validate_source_audit
from soc_verifier.storage.artifacts import ArtifactStore


def validate_audit_task(audit: SourceAudit, task: Task) -> None:
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
    envelope = TaskEnvelope.model_validate(
        artifacts.read(f"{name.removesuffix('.json')}.task.json")
    )
    if envelope.output_artifact != name or envelope.inputs.role != "reviewer":
        raise ValueError("Source audit task binding mismatch")
    task = Task(artifacts, envelope)
    audit = task.load(SourceAudit)
    if audit is None:
        raise ValueError("Source audit has no completed output")
    validate_audit_task(audit, task)
    return audit
