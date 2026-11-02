"""Classify flat gap notes once with the existing reviewer; host enforces all other gates."""

import json

from soc_verifier.agents.base import AgentExecutor
from soc_verifier.agents.instructions import SCOPE_EXECUTION_GAPS
from soc_verifier.agents.tasks import (
    ArtifactReference,
    Task,
    TaskInputs,
    fingerprint,
    runtime_versions,
)
from soc_verifier.domain.models import SpecAnalysis, Specification, VerificationPlan
from soc_verifier.domain.readiness import GapAssessment
from soc_verifier.storage.artifacts import ArtifactStore


def scope_execution_gaps(
    agents: AgentExecutor,
    artifacts: ArtifactStore,
    specification: Specification,
    analysis: SpecAnalysis,
    plan: VerificationPlan,
    evidence: dict[str, ArtifactReference],
) -> GapAssessment:
    context = {
        "gaps": [{"gap_index": i, "text": gap} for i, gap in enumerate(analysis.gaps)],
        "requirements": [r.model_dump() for r in analysis.requirements],
        "plan_index": [{"id": i.id, "requirement_ids": i.requirement_ids} for i in plan.items],
        "source_directory": [{"id": b.id, "section": b.section} for b in specification.blocks],
    }
    task = Task.bind(
        artifacts,
        "execution-gaps.json",
        TaskInputs(
            role="reviewer",
            stage="execution.gaps",
            assigned_ids=[r.id for r in analysis.requirements],
            evidence=evidence,
            input_sha256=fingerprint(context),
            instruction_sha256=fingerprint(SCOPE_EXECUTION_GAPS),
            schema_sha256=fingerprint(GapAssessment.model_json_schema()),
            versions=runtime_versions(),
            configuration={"configuration": agents.configuration},
        ),
    )
    assessment = task.load(GapAssessment)
    if assessment is None:
        assessment = agents.run(
            role="reviewer",
            instruction=SCOPE_EXECUTION_GAPS,
            context=json.dumps(context),
            schema=GapAssessment,
            task=task.envelope,
        )
    assessment.validate_context(specification, analysis)
    task.save(assessment)
    return assessment
