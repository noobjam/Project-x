"""Persist and verify the deterministic projections of an accounted extraction."""

import json
from hashlib import sha256
from typing import Any, Literal

from soc_verifier.agents import instructions as prompts
from soc_verifier.agents.base import AgentExecutor
from soc_verifier.agents.tasks import ArtifactReference, Task
from soc_verifier.domain.accounting import (
    AccountingDraft,
    SourceAccounting,
    UnitAccountingDraft,
    compile_accounting,
    compile_unit_accounting,
    source_units,
)
from soc_verifier.domain.models import SpecAnalysis, Specification
from soc_verifier.domain.passage_accounting import (
    AccountingValidationError,
    PassageAccounting,
    PassageAccountingDraft,
    compile_passage_accounting,
)
from soc_verifier.storage.artifacts import ArtifactStore, artifact_content


def project_accounting(
    artifacts: ArtifactStore, extraction_name: str, analysis_name: str
) -> tuple[SpecAnalysis, SourceAccounting | PassageAccounting]:
    spec = Specification.model_validate(artifacts.read("specification.json"))
    data = artifacts.read(extraction_name)
    if data.get("format") == "source-accounting-draft-v3":
        current = PassageAccountingDraft.model_validate(data)
        analysis, obligations, passages, unaccounted = compile_passage_accounting(current, spec)
        return analysis, PassageAccounting(
            specification_sha256=sha256(
                artifacts.path("specification.json").read_bytes()
            ).hexdigest(),
            analysis_artifact=analysis_name,
            analysis_sha256=sha256(artifact_content(analysis).encode()).hexdigest(),
            extraction_artifact=extraction_name,
            extraction_sha256=sha256(artifacts.path(extraction_name).read_bytes()).hexdigest(),
            obligations=obligations,
            dispositions=passages,
            unaccounted=unaccounted,
        )
    format_version: Literal["source-accounting-v1", "source-accounting-v2"]
    if data.get("format") == "source-accounting-draft-v2":
        draft = UnitAccountingDraft.model_validate(data)
        analysis, obligations, unaccounted = compile_unit_accounting(draft, spec)
        dispositions = draft.dispositions
        format_version = "source-accounting-v2"
    else:
        legacy = AccountingDraft.model_validate(data)
        analysis, obligations, unaccounted = compile_accounting(legacy, spec)
        dispositions = legacy.dispositions
        format_version = "source-accounting-v1"
    report = SourceAccounting(
        format=format_version,
        specification_sha256=sha256(artifacts.path("specification.json").read_bytes()).hexdigest(),
        analysis_artifact=analysis_name,
        analysis_sha256=sha256(artifact_content(analysis).encode()).hexdigest(),
        extraction_artifact=extraction_name,
        extraction_sha256=sha256(artifacts.path(extraction_name).read_bytes()).hexdigest(),
        obligations=obligations,
        dispositions=dispositions,
        unaccounted=unaccounted,
    )
    return analysis, report


def read_accounting(artifacts: ArtifactStore, name: str) -> SourceAccounting | PassageAccounting:
    data = artifacts.read(name)
    report: SourceAccounting | PassageAccounting = (
        PassageAccounting.model_validate(data)
        if data.get("format") == "source-accounting-v3"
        else SourceAccounting.model_validate(data)
    )
    analysis, expected = project_accounting(
        artifacts, report.extraction_artifact, report.analysis_artifact
    )
    if (
        report != expected
        or artifacts.path(report.analysis_artifact).read_bytes()
        != artifact_content(analysis).encode()
    ):
        raise ValueError("Source accounting or its bound inputs changed")
    return report


def source_context(spec: Specification) -> dict[str, Any]:
    units = source_units(spec)
    return {
        "document_name": spec.document_name,
        "extraction_warnings": spec.extraction_warnings,
        "blocks": [
            {
                "id": b.id,
                "section": b.section,
                "locator": b.locator,
                "units": [u.model_dump(mode="json") for u in units if u.block_id == b.id],
            }
            for b in spec.blocks
        ],
    }


def extract_with_feedback(
    agents: AgentExecutor,
    task: Task,
    spec: Specification,
    schema: type[PassageAccountingDraft],
    context: dict[str, Any],
) -> PassageAccountingDraft:
    """Checkpoint unaccepted attempts; one correction may change dispositions only."""
    artifacts = task.artifacts
    stem = task.envelope.output_artifact.removesuffix(".json")
    original: PassageAccountingDraft | None = None
    extra: list[str] = []
    for index in range(2):
        name = f"{stem}.attempt{index}.json"
        attempt = task.child(
            name,
            stage=f"{stem}.attempt{index}",
            assigned_ids=task.envelope.inputs.assigned_ids,
            data=context,
            instruction=prompts.ANALYZE_ACCOUNTED,
            schema=schema,
            extra_inputs=extra,
        )
        draft = attempt.load(schema)
        if draft is None:
            draft = agents.run(
                role="analyst",
                instruction=prompts.ANALYZE_ACCOUNTED,
                context=json.dumps(context),
                schema=schema,
                task=attempt.envelope,
            )
        # Attempt completion means a returned draft, never domain acceptance.
        attempt.save(draft)
        if original is not None and (
            draft.obligations != original.obligations or draft.gaps != original.gaps
        ):
            raise ValueError("Accounting correction changed frozen obligations or gaps")
        try:
            compile_passage_accounting(draft, spec)
        except AccountingValidationError as error:
            feedback_name = f"{stem}.attempt{index}.feedback.json"
            feedback = {
                "format": "source-accounting-feedback-v1",
                "rejected_draft": ArtifactReference.capture(artifacts, name).model_dump(),
                "issues": [i.model_dump() for i in error.issues],
                "repairable": error.repairable,
                "correction_remaining": error.repairable and index == 0,
                "instruction": (
                    "Change only dispositions. Preserve every obligation, its ID, facts and "
                    "evidence, and all gaps exactly. Do not hide uncertainty to pass validation."
                ),
            }
            artifacts.write(feedback_name, feedback)
            if index or not error.repairable:
                raise
            original = draft
            context = {
                **context,
                "rejected_draft": draft.model_dump(mode="json"),
                "validation_feedback": feedback,
            }
            extra = [name, feedback_name]
            continue
        task.save(draft)
        return draft
    raise AssertionError("Unreachable accounting correction state")
