import pytest
from pydantic import ValidationError

from soc_verifier.domain.models import (
    SpecAnalysis,
    VerificationPlan,
    validate_sources,
    validate_traceability,
)


def test_rejects_fabricated_evidence(analysis, specification):
    invalid = analysis.model_copy(
        update={
            "requirements": [
                analysis.requirements[0].model_copy(update={"source_ids": ["NONEXISTENT"]})
            ]
        }
    )
    with pytest.raises(ValueError, match="unknown source"):
        validate_sources(invalid, specification)


def test_rejects_unknown_requirement(analysis, verification_plan):
    invalid = verification_plan.model_copy(
        update={
            "items": [
                verification_plan.items[0].model_copy(update={"requirement_ids": ["UNKNOWN"]})
            ]
        }
    )
    with pytest.raises(ValueError, match="unknown requirement"):
        validate_traceability(invalid, analysis)


def test_rejects_uncovered_requirement(analysis, verification_plan):
    another = analysis.requirements[0].model_copy(update={"id": "REQ-RST-002"})
    expanded = analysis.model_copy(update={"requirements": [*analysis.requirements, another]})
    with pytest.raises(ValueError, match="without verification items"):
        validate_traceability(verification_plan, expanded)


def test_rejects_duplicate_ids(analysis, verification_plan):
    with pytest.raises(ValidationError, match="Duplicate requirement"):
        SpecAnalysis(requirements=analysis.requirements * 2, gaps=[])
    with pytest.raises(ValidationError, match="Duplicate verification"):
        VerificationPlan(items=verification_plan.items * 2)


def test_rejects_numeric_ids(analysis):
    payload = analysis.model_dump()
    payload["requirements"][0]["id"] = 1.1
    with pytest.raises(ValidationError):
        SpecAnalysis.model_validate(payload)
