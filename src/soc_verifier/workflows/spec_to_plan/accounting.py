"""Persist and verify the deterministic projections of an accounted extraction."""

from hashlib import sha256
from typing import Literal

from soc_verifier.domain.accounting import (
    AccountingDraft,
    SourceAccounting,
    UnitAccountingDraft,
    compile_accounting,
    compile_unit_accounting,
)
from soc_verifier.domain.models import SpecAnalysis, Specification
from soc_verifier.storage.artifacts import ArtifactStore, artifact_content


def project_accounting(
    artifacts: ArtifactStore, extraction_name: str, analysis_name: str
) -> tuple[SpecAnalysis, SourceAccounting]:
    spec = Specification.model_validate(artifacts.read("specification.json"))
    data = artifacts.read(extraction_name)
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
