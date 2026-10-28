"""Persist and verify the deterministic projections of an accounted extraction."""

from hashlib import sha256

from soc_verifier.domain.accounting import AccountingDraft, SourceAccounting, compile_accounting
from soc_verifier.domain.models import SpecAnalysis, Specification
from soc_verifier.storage.artifacts import ArtifactStore, artifact_content


def project_accounting(
    artifacts: ArtifactStore, extraction_name: str, analysis_name: str
) -> tuple[SpecAnalysis, SourceAccounting]:
    spec = Specification.model_validate(artifacts.read("specification.json"))
    draft = AccountingDraft.model_validate(artifacts.read(extraction_name))
    analysis, obligations, unaccounted = compile_accounting(draft, spec)
    report = SourceAccounting(
        specification_sha256=sha256(artifacts.path("specification.json").read_bytes()).hexdigest(),
        analysis_artifact=analysis_name,
        analysis_sha256=sha256(artifact_content(analysis).encode()).hexdigest(),
        extraction_artifact=extraction_name,
        extraction_sha256=sha256(artifacts.path(extraction_name).read_bytes()).hexdigest(),
        obligations=obligations,
        dispositions=draft.dispositions,
        unaccounted=unaccounted,
    )
    return analysis, report


def read_accounting(artifacts: ArtifactStore, name: str) -> SourceAccounting:
    report = SourceAccounting.model_validate(artifacts.read(name))
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
