"""Aggregate explicit engineering judgments; never infer correctness from linked IDs."""

from hashlib import sha256
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import Field, ValidationError, model_validator

from soc_verifier.domain.models import (
    Contract,
    NonEmpty,
    PlanReview,
    SpecAnalysis,
    VerificationPlan,
    validate_sources,
    validate_traceability,
)
from soc_verifier.evaluation.baseline import Digest
from soc_verifier.evaluation.packets import CaseId, load_packet

LabelState = Literal["agent_proposed", "imported_reference", "human_reviewed", "disputed"]
RunStatus = Literal["complete", "failed", "malformed", "interrupted", "budget_exhausted"]


class EvidenceSpan(Contract):
    document_id: Digest
    block_id: NonEmpty
    text_sha256: Digest
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def nonempty_span(self) -> Self:
        if self.end <= self.start:
            raise ValueError("Evidence spans must be nonempty half-open ranges")
        return self


class Label(Contract):
    id: NonEmpty
    kind: Literal["obligation", "review_control"]
    expected: Literal["behavior", "flag_conflict", "defect", "valid"]
    statement: NonEmpty
    state: LabelState = "agent_proposed"
    reviewer: NonEmpty | None = None
    reference_origin: NonEmpty | None = None
    reference_sha256: Digest | None = None
    evidence: list[EvidenceSpan]
    availability: Literal["available", "unavailable"] = "available"
    unavailable_reason: NonEmpty | None = None
    exclusion: Literal["non_normative", "outside_packet_scope"] | None = None
    exclusion_reason: NonEmpty | None = None
    exclusion_authority: NonEmpty | None = None
    candidate_plan_sha256: Digest | None = None
    target_item_id: NonEmpty | None = None

    @model_validator(mode="after")
    def label_provenance(self) -> Self:
        if self.state == "imported_reference" and not (
            self.reference_origin and self.reference_sha256
        ):
            raise ValueError("Imported labels require an exact reference origin and hash")
        if bool(self.reference_origin) != bool(self.reference_sha256):
            raise ValueError("Reference origin and hash must be supplied together")
        if self.state == "human_reviewed" and not self.reviewer:
            raise ValueError("Reviewed labels require an identified reviewer")
        if self.availability == "available" and not self.evidence:
            raise ValueError("Available labels require source evidence")
        if self.availability == "unavailable" and not self.unavailable_reason:
            raise ValueError("Unavailable evidence requires an explicit limitation")
        if self.exclusion and not (
            self.state == "human_reviewed" and self.exclusion_reason and self.exclusion_authority
        ):
            raise ValueError("Exclusions require reviewed scope, reason and authority")
        if self.kind == "obligation":
            if (
                self.expected not in {"behavior", "flag_conflict"}
                or self.candidate_plan_sha256
                or self.target_item_id
            ):
                raise ValueError("Obligations must describe behavior or a source conflict")
        elif (
            self.expected not in {"defect", "valid"}
            or not self.candidate_plan_sha256
            or not self.target_item_id
        ):
            raise ValueError("Review controls must bind an exact candidate plan and item")
        return self


class Annotations(Contract):
    format: Literal["soc-verifier-annotations-v1"] = "soc-verifier-annotations-v1"
    case_id: CaseId
    source_sha256: Digest
    revision: Annotated[int, Field(ge=1)]
    coverage_unknown: bool = True
    labels: list[Label]

    @model_validator(mode="after")
    def distinct_labels(self) -> Self:
        _unique([label.id for label in self.labels])
        return self


class ObligationJudgment(Contract):
    label_id: NonEmpty
    extraction: Literal["covered", "missed", "unresolved"]
    requirement_ids: list[NonEmpty]
    scenario: Literal["adequate", "inadequate", "unresolved"]
    item_ids: list[NonEmpty]
    rationale: NonEmpty

    @model_validator(mode="after")
    def supported_verdicts(self) -> Self:
        if self.extraction == "covered" and not self.requirement_ids:
            raise ValueError("Covered obligations require actual output requirement IDs")
        if self.scenario == "adequate" and (not self.item_ids or self.extraction != "covered"):
            raise ValueError("Adequate scenarios require covered obligations and actual plan items")
        return self


class SupportJudgment(Contract):
    target: Literal["analysis", "plan"]
    target_id: NonEmpty
    verdict: Literal["supported", "unsupported", "unresolved"]
    rationale: NonEmpty


class ReviewJudgment(Contract):
    label_id: NonEmpty
    verdict: Literal["detected", "not_detected", "unresolved"]
    finding_indices: list[Annotated[int, Field(ge=0)]]
    rationale: NonEmpty

    @model_validator(mode="after")
    def findings_match_verdict(self) -> Self:
        if (self.verdict == "detected") != bool(self.finding_indices):
            raise ValueError("Detected controls require finding indices; other verdicts do not")
        return self


class Assessment(Contract):
    format: Literal["soc-verifier-assessment-v1"] = "soc-verifier-assessment-v1"
    case_id: CaseId
    source_sha256: Digest
    annotations_sha256: Digest
    run_status: RunStatus
    judgment_state: Literal["agent_proposed", "human_reviewed"] = "agent_proposed"
    assessor: NonEmpty
    artifact_hashes: dict[str, Digest]
    obligations: list[ObligationJudgment]
    support: list[SupportJudgment]
    review: list[ReviewJudgment]

    @model_validator(mode="after")
    def distinct_judgments(self) -> Self:
        if not set(self.artifact_hashes) <= {"analysis", "plan", "review"}:
            raise ValueError("Unknown evaluation output artifact role")
        _unique([row.label_id for row in self.obligations])
        _unique([f"{row.target}:{row.target_id}" for row in self.support])
        _unique([row.label_id for row in self.review])
        return self


def _unique(ids: list[str]) -> None:
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evaluation IDs")


def validate_annotations(packet: Path, annotations: Annotations) -> None:
    manifest, specification = load_packet(packet)
    if (
        annotations.case_id != manifest.case_id
        or annotations.source_sha256 != manifest.source_sha256
    ):
        raise ValueError("Annotations belong to a different source packet")
    blocks = {block.id: block for block in specification.blocks}
    for label in annotations.labels:
        for span in label.evidence:
            block = blocks.get(span.block_id)
            if block is None or manifest.block_documents[span.block_id] != span.document_id:
                raise ValueError("Annotation cites an unknown source document or block")
            if sha256(block.text.encode()).hexdigest() != span.text_sha256 or span.end > len(
                block.text
            ):
                raise ValueError("Annotation text hash or span mismatch")


def score_packet(
    packet: Path,
    annotations_path: Path,
    assessment_path: Path,
    artifacts: dict[str, Path],
) -> dict[str, Any]:
    manifest, specification = load_packet(packet)
    annotation_data = annotations_path.read_bytes()
    annotations = Annotations.model_validate_json(annotation_data)
    validate_annotations(packet, annotations)
    assessment = Assessment.model_validate_json(assessment_path.read_bytes())
    if (
        assessment.case_id != manifest.case_id
        or assessment.source_sha256 != manifest.source_sha256
        or assessment.annotations_sha256 != sha256(annotation_data).hexdigest()
    ):
        raise ValueError("Assessment is stale for this packet or annotation revision")
    if set(artifacts) != set(assessment.artifact_hashes):
        raise ValueError("Assessment must bind exactly the supplied output artifacts")
    parsed: dict[str, Any] = {}
    structural_errors = []
    artifact_models: dict[str, type[Contract]] = {
        "analysis": SpecAnalysis,
        "plan": VerificationPlan,
        "review": PlanReview,
    }
    for name, model in artifact_models.items():
        if name not in artifacts:
            continue
        data = artifacts[name].read_bytes()
        if sha256(data).hexdigest() != assessment.artifact_hashes[name]:
            raise ValueError("Assessment output hash mismatch")
        try:
            parsed[name] = model.model_validate_json(data)
        except ValidationError:
            structural_errors.append(f"{name}: invalid artifact schema")
    analysis, plan, review = (parsed.get(name) for name in ("analysis", "plan", "review"))
    try:
        if analysis:
            validate_sources(analysis, specification)
        if analysis and plan:
            validate_traceability(plan, analysis)
    except ValueError:
        structural_errors.append("Invalid source or requirement links")
    if assessment.run_status == "complete" and len(parsed) != 3:
        structural_errors.append("Complete runs require analysis, plan and review artifacts")
    outcome = "malformed" if structural_errors else assessment.run_status
    requirements = {item.id for item in analysis.requirements} if analysis else set()
    items = {item.id: item for item in plan.items} if plan else {}
    labels = {label.id: label for label in annotations.labels if not label.exclusion}
    judgments = {row.label_id: row for row in assessment.obligations}
    for row in assessment.obligations:
        label = labels.get(row.label_id)
        if not label or label.kind != "obligation":
            raise ValueError("Judgment cites an unknown or excluded obligation")
        if not set(row.requirement_ids) <= requirements or not set(row.item_ids) <= set(items):
            raise ValueError("Judgment cites nonexistent output IDs")
        if row.scenario == "adequate" and not set(row.requirement_ids) <= {
            requirement
            for item_id in row.item_ids
            for requirement in items[item_id].requirement_ids
        }:
            raise ValueError("Scenario judgment is not linked to its mapped requirements")
        if label.availability == "unavailable" and (
            row.extraction == "covered" or row.scenario == "adequate"
        ):
            raise ValueError("Unavailable evidence cannot establish semantic coverage")
    support: dict[tuple[str, str], str] = {
        (row.target, row.target_id): row.verdict for row in assessment.support
    }
    targets = {("analysis", identifier) for identifier in requirements} | {
        ("plan", identifier) for identifier in items
    }
    if not set(support) <= targets:
        raise ValueError("Support judgment cites a nonexistent output")
    review_judgments = {row.label_id: row for row in assessment.review}
    for review_row in assessment.review:
        label = labels.get(review_row.label_id)
        if not label or label.kind != "review_control":
            raise ValueError("Judgment cites an unknown review control")
        if review is None or any(
            index >= len(review.findings) for index in review_row.finding_indices
        ):
            raise ValueError("Review judgment cites missing findings")
        for index in review_row.finding_indices:
            finding = review.findings[index]
            if finding.target != "plan" or label.target_item_id not in finding.item_ids:
                raise ValueError("Review finding is not attached to its control item")
    for label in labels.values():
        if label.kind == "review_control" and (
            (
                "plan" in assessment.artifact_hashes
                and label.candidate_plan_sha256 != assessment.artifact_hashes["plan"]
            )
            or (plan is not None and label.target_item_id not in items)
        ):
            raise ValueError("Review control belongs to another candidate plan")
    groups: dict[str, Any] = {}
    for group, states in {
        "reviewed": {"human_reviewed"},
        "provisional": {"agent_proposed", "imported_reference"},
        "disputed": {"disputed"},
    }.items():
        selected = [label for label in labels.values() if label.state in states]
        obligations = [label for label in selected if label.kind == "obligation"]
        extracted = dict.fromkeys(("covered", "missed", "unresolved"), 0)
        scenarios = dict.fromkeys(("adequate", "inadequate", "unresolved"), 0)
        for label in obligations:
            judgment = judgments.get(label.id)
            extracted[judgment.extraction if judgment else "unresolved"] += 1
            scenarios[judgment.scenario if judgment else "unresolved"] += 1
        controls = [label for label in selected if label.kind == "review_control"]
        detected, false_alarms, assessed_valid, unresolved = 0, 0, 0, 0
        for label in controls:
            result = review_judgments.get(label.id)
            if not result or result.verdict == "unresolved":
                unresolved += 1
            elif label.expected == "valid":
                assessed_valid += 1
                false_alarms += result.verdict == "detected"
            else:
                detected += result.verdict == "detected"
        defects = sum(label.expected == "defect" for label in controls)
        groups[group] = {
            "obligations": len(obligations),
            "extraction": {
                **extracted,
                "recall": extracted["covered"] / len(obligations) if obligations else None,
            },
            "scenarios": {
                **scenarios,
                "adequacy": scenarios["adequate"] / len(obligations) if obligations else None,
            },
            "unavailable": sum(label.availability == "unavailable" for label in selected),
            "review": {
                "defects": defects,
                "detected": detected,
                "detection_recall": detected / defects if defects else None,
                "valid_controls": len(controls) - defects,
                "assessed_valid": assessed_valid,
                "false_alarms": false_alarms,
                "false_alarm_rate": false_alarms / assessed_valid if assessed_valid else None,
                "unresolved": unresolved,
            },
        }
    support_counts = {
        key: sum(support.get(target, "unresolved") == key for target in targets)
        for key in ("supported", "unsupported", "unresolved")
    }
    mapped_findings = {index for row in assessment.review for index in row.finding_indices}
    unmapped_findings = len(review.findings) - len(mapped_findings) if review else 0
    reviewed = groups["reviewed"]
    ready = (
        outcome == "complete"
        and not annotations.coverage_unknown
        and manifest.context_state == "human_reviewed"
        and assessment.judgment_state == "human_reviewed"
        and bool(reviewed["obligations"])
        and all(
            label.state == "human_reviewed" and label.availability == "available"
            for label in labels.values()
        )
        and not reviewed["extraction"]["unresolved"]
        and not reviewed["scenarios"]["unresolved"]
        and not reviewed["review"]["unresolved"]
        and not support_counts["unresolved"]
        and not unmapped_findings
    )
    passes = (
        reviewed["extraction"]["recall"] == 1
        and reviewed["scenarios"]["adequacy"] == 1
        and reviewed["review"]["detected"] == reviewed["review"]["defects"]
        and not reviewed["review"]["false_alarms"]
        and not support_counts["unsupported"]
    )
    return {
        "format": "soc-verifier-score-v1",
        "case_id": manifest.case_id,
        "source_sha256": manifest.source_sha256,
        "annotations_sha256": assessment.annotations_sha256,
        "assessment_sha256": sha256(assessment_path.read_bytes()).hexdigest(),
        "run_status": outcome,
        "declared_run_status": assessment.run_status,
        "structural_errors": structural_errors,
        "judgment_state": assessment.judgment_state,
        "groups": groups,
        "output_support": {"total": len(targets), **support_counts},
        "unmapped_review_findings": unmapped_findings,
        "excluded_labels": [label.id for label in annotations.labels if label.exclusion],
        "coverage_unknown": annotations.coverage_unknown,
        "semantic_acceptance": ("pass" if passes else "fail") if ready else "pending",
        "editing_time": "not_measured",
        "scope": "declared_packet_only",
    }
