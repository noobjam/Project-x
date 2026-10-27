import json
import sys
from copy import deepcopy
from hashlib import sha256

import pytest
from pydantic import ValidationError

from soc_verifier.evaluation.__main__ import main
from soc_verifier.evaluation.baseline import _json_bytes
from soc_verifier.evaluation.packets import PacketManifest, SourceRecord, load_packet, write_packet
from soc_verifier.evaluation.pilot import freeze_pilot, verify_pilot
from soc_verifier.evaluation.scoring import Annotations, score_packet, validate_annotations


def digest(data):
    return sha256(_json_bytes(data)).hexdigest()


@pytest.fixture
def case(evaluation_repo, specification, analysis, verification_plan):
    # Reviewed states below are synthetic test inputs, never real engineering approvals.
    blocks = [
        specification.blocks[0],
        specification.blocks[0].model_copy(
            update={"id": "P00002", "text": "A wake request stays high until software clears it."}
        ),
    ]
    specification = specification.model_copy(update={"blocks": blocks})
    source_hash = digest(specification.model_dump(mode="json"))
    packet = evaluation_repo / "artifacts" / "synthetic"
    manifest = PacketManifest(
        case_id="synthetic",
        scope="Synthetic reset and wake",
        source_sha256=source_hash,
        sources=[
            SourceRecord(
                name="synthetic.docx",
                sha256=specification.sha256,
                adapter="docx-v1",
                revision="synthetic-v1",
            )
        ],
        block_documents={block.id: specification.sha256 for block in blocks},
        limitations=[],
        context_state="human_reviewed",
        context_reviewer="synthetic-test-reviewer",
    )
    write_packet(packet, specification, manifest)
    requirements = analysis.model_dump(mode="json")
    requirements["requirements"].append(
        {
            **requirements["requirements"][0],
            "id": "REQ-WAKE",
            "source_ids": ["P00002"],
            "statement": blocks[1].text,
        }
    )
    plan = verification_plan.model_dump(mode="json")
    plan["items"].append(
        {
            **plan["items"][0],
            "id": "PLAN-WAKE",
            "requirement_ids": ["REQ-WAKE"],
            "objective": "Check a wake request persists",
            "expected_results": ["Request stays high until software clears it."],
        }
    )
    labels, judgments, support = [], [], []
    for index, block in enumerate(blocks):
        label_id = f"OBL-{index + 1}"
        labels.append(
            {
                "id": label_id,
                "kind": "obligation",
                "expected": "behavior",
                "statement": block.text,
                "state": "human_reviewed",
                "reviewer": "synthetic-test-reviewer",
                "evidence": [
                    {
                        "document_id": specification.sha256,
                        "block_id": block.id,
                        "text_sha256": sha256(block.text.encode()).hexdigest(),
                        "start": 0,
                        "end": len(block.text),
                    }
                ],
            }
        )
        requirement_id, item_id = (
            requirements["requirements"][index]["id"],
            plan["items"][index]["id"],
        )
        judgments.append(
            {
                "label_id": label_id,
                "extraction": "covered",
                "requirement_ids": [requirement_id],
                "scenario": "adequate",
                "item_ids": [item_id],
                "rationale": "Synthetic matching behavior",
            }
        )
        support.extend(
            [
                {
                    "target": role,
                    "target_id": identifier,
                    "verdict": "supported",
                    "rationale": "Synthetic support judgment",
                }
                for role, identifier in (("analysis", requirement_id), ("plan", item_id))
            ]
        )
    return {
        "packet": packet,
        "annotations": {
            "case_id": "synthetic",
            "source_sha256": source_hash,
            "revision": 1,
            "coverage_unknown": False,
            "labels": labels,
        },
        "assessment": {
            "case_id": "synthetic",
            "source_sha256": source_hash,
            "run_status": "complete",
            "judgment_state": "human_reviewed",
            "assessor": "synthetic-test-reviewer",
            "obligations": judgments,
            "support": support,
            "review": [],
        },
        "outputs": {
            "analysis": requirements,
            "plan": plan,
            "review": {"schema_version": "1.0", "findings": []},
        },
    }


def persist(case):
    reference = case["packet"] / "reference"
    reference.mkdir(exist_ok=True)
    annotations = reference / "annotations.json"
    annotations.write_bytes(_json_bytes(case["annotations"]))
    artifacts = {}
    for name, value in case["outputs"].items():
        path = reference / f"{name}.json"
        path.write_bytes(_json_bytes(value))
        artifacts[name] = path
    assessment = reference / "assessment.json"
    case["assessment"]["annotations_sha256"] = sha256(annotations.read_bytes()).hexdigest()
    case["assessment"]["artifact_hashes"] = {
        name: sha256(path.read_bytes()).hexdigest() for name, path in artifacts.items()
    }
    assessment.write_bytes(_json_bytes(case["assessment"]))
    return case["packet"], annotations, assessment, artifacts


def test_removing_output_obligation_reduces_recall_even_with_complete_remaining_links(case):
    assert score_packet(*persist(case))["semantic_acceptance"] == "pass"
    original_source = (case["packet"] / "source/specification.json").read_bytes()
    original_annotations = _json_bytes(case["annotations"])
    case["outputs"]["analysis"]["requirements"].pop()
    case["outputs"]["plan"]["items"].pop()
    case["assessment"]["obligations"][1] = {
        "label_id": "OBL-2",
        "extraction": "missed",
        "requirement_ids": [],
        "scenario": "inadequate",
        "item_ids": [],
        "rationale": "Removed from output",
    }
    case["assessment"]["support"] = case["assessment"]["support"][:2]
    report = score_packet(*persist(case))
    assert report["groups"]["reviewed"]["extraction"]["recall"] == 0.5
    assert report["groups"]["reviewed"]["obligations"] == 2
    assert report["structural_errors"] == []
    assert report["semantic_acceptance"] == "fail"
    assert (case["packet"] / "source/specification.json").read_bytes() == original_source
    assert _json_bytes(case["annotations"]) == original_annotations


def test_linked_ids_without_judgments_do_not_establish_quality(case):
    case["assessment"]["obligations"] = []
    case["assessment"]["support"] = []
    report = score_packet(*persist(case))
    assert report["groups"]["reviewed"]["extraction"]["recall"] == 0
    assert report["groups"]["reviewed"]["extraction"]["unresolved"] == 2
    assert report["output_support"]["unresolved"] == 4
    assert report["semantic_acceptance"] == "pending"


@pytest.mark.parametrize(
    "state,group",
    [
        ("agent_proposed", "provisional"),
        ("imported_reference", "provisional"),
        ("disputed", "disputed"),
    ],
)
def test_unreviewed_labels_never_produce_a_semantic_pass(case, state, group):
    case["annotations"]["labels"][0]["state"] = state
    if state == "imported_reference":
        case["annotations"]["labels"][0].update(
            reference_origin="synthetic-reference.xlsx#Sheet1!A1", reference_sha256="b" * 64
        )
    report = score_packet(*persist(case))
    assert report["groups"][group]["obligations"] == 1
    assert report["groups"]["reviewed"]["obligations"] == 1
    assert report["semantic_acceptance"] == "pending"


@pytest.mark.parametrize(
    "barrier", ["unknown_coverage", "provisional_judgment", "unreviewed_context"]
)
def test_other_acceptance_gates_remain_explicit(case, barrier):
    if barrier == "unknown_coverage":
        case["annotations"]["coverage_unknown"] = True
    elif barrier == "provisional_judgment":
        case["assessment"]["judgment_state"] = "agent_proposed"
    else:
        path = case["packet"] / "packet.json"
        manifest = json.loads(path.read_bytes())
        manifest["context_state"] = "proposed"
        path.write_bytes(_json_bytes(manifest))
        (case["packet"] / "packet.sha256").write_text(sha256(path.read_bytes()).hexdigest())
    assert score_packet(*persist(case))["semantic_acceptance"] == "pending"


def test_missing_evidence_stays_in_denominator(case):
    case["annotations"]["labels"][1].update(
        availability="unavailable", unavailable_reason="Diagram not extracted", evidence=[]
    )
    case["assessment"]["obligations"][1].update(
        extraction="unresolved", requirement_ids=[], scenario="unresolved", item_ids=[]
    )
    report = score_packet(*persist(case))
    assert report["groups"]["reviewed"]["obligations"] == 2
    assert report["groups"]["reviewed"]["unavailable"] == 1
    assert report["groups"]["reviewed"]["extraction"]["recall"] == 0.5
    assert report["semantic_acceptance"] == "pending"


def test_extraction_scenario_and_unsupported_behavior_are_separate(case):
    case["assessment"]["obligations"][1]["scenario"] = "inadequate"
    case["assessment"]["support"][-1]["verdict"] = "unsupported"
    report = score_packet(*persist(case))
    assert report["groups"]["reviewed"]["extraction"]["recall"] == 1
    assert report["groups"]["reviewed"]["scenarios"]["adequacy"] == 0.5
    assert report["output_support"]["unsupported"] == 1
    assert report["semantic_acceptance"] == "fail"


def test_review_false_alarm_and_defect_detection_use_frozen_controls(case):
    case["outputs"]["plan"]["items"][1]["expected_results"] = [
        "A wake pulse may disappear before software observes it."
    ]
    plan_hash = digest(case["outputs"]["plan"])
    for index, expected in enumerate(("valid", "defect")):
        item_id = case["outputs"]["plan"]["items"][index]["id"]
        case["annotations"]["labels"].append(
            {
                **deepcopy(case["annotations"]["labels"][index]),
                "id": f"CONTROL-{index}",
                "kind": "review_control",
                "expected": expected,
                "candidate_plan_sha256": plan_hash,
                "target_item_id": item_id,
            }
        )
        case["outputs"]["review"]["findings"].append(
            {
                "target": "plan",
                "item_ids": [item_id],
                "description": "Synthetic review finding",
                "severity": "error",
            }
        )
        case["assessment"]["review"].append(
            {
                "label_id": f"CONTROL-{index}",
                "verdict": "detected",
                "finding_indices": [index],
                "rationale": "Synthetic control match",
            }
        )
    report = score_packet(*persist(case))
    review = report["groups"]["reviewed"]["review"]
    assert review["defects"] == review["detected"] == 1
    assert review["valid_controls"] == review["false_alarms"] == 1
    assert review["false_alarm_rate"] == 1
    assert report["semantic_acceptance"] == "fail"
    case["outputs"]["plan"]["items"][1]["objective"] = "Changed candidate"
    with pytest.raises(ValueError, match="another candidate plan"):
        score_packet(*persist(case))


@pytest.mark.parametrize("status", ["failed", "malformed", "interrupted", "budget_exhausted"])
def test_incomplete_runs_are_reported_with_the_original_denominator(case, status):
    case["outputs"] = {}
    case["assessment"].update(run_status=status, obligations=[], support=[], review=[])
    report = score_packet(*persist(case))
    assert report["run_status"] == status
    assert report["groups"]["reviewed"]["obligations"] == 2
    assert report["groups"]["reviewed"]["extraction"]["unresolved"] == 2
    assert report["semantic_acceptance"] == "pending"


def test_malformed_artifact_cannot_claim_a_complete_run(case):
    case["outputs"]["analysis"] = {"not": "an analysis"}
    case["assessment"].update(obligations=[], support=[])
    report = score_packet(*persist(case))
    assert report["run_status"] == "malformed"
    assert report["structural_errors"]
    assert report["semantic_acceptance"] == "pending"


@pytest.mark.parametrize(
    "problem", ["source", "document", "hash", "range", "version", "output_id", "exclusion"]
)
def test_stale_or_invalid_evidence_and_judgments_are_rejected(case, problem):
    label = case["annotations"]["labels"][0]
    if problem == "source":
        case["annotations"]["source_sha256"] = "0" * 64
    elif problem == "document":
        label["evidence"][0]["document_id"] = "0" * 64
    elif problem == "hash":
        label["evidence"][0]["text_sha256"] = "0" * 64
    elif problem == "range":
        label["evidence"][0]["end"] = 9999
    elif problem == "version":
        case["annotations"]["format"] = "unknown-v99"
    elif problem == "output_id":
        case["assessment"]["obligations"][0]["requirement_ids"] = ["MISSING"]
    else:
        label["exclusion"] = "non_normative"
    with pytest.raises((ValueError, ValidationError)):
        score_packet(*persist(case))


@pytest.mark.parametrize("target", ["annotations", "analysis"])
def test_assessment_hashes_reject_silent_input_changes(case, target):
    args = persist(case)
    path = args[1] if target == "annotations" else args[3]["analysis"]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match=r"stale|hash mismatch"):
        score_packet(*args)


def test_source_mutation_requires_new_expected_labels_and_keeps_control_unchanged(case):
    args = persist(case)
    old_manifest, old_source = load_packet(case["packet"])
    original = [
        (path, path.read_bytes())
        for path in (args[1], case["packet"] / "source/specification.json")
    ]
    changed_block = old_source.blocks[1].model_copy(
        update={"text": "A wake request is a single-cycle pulse."}
    )
    changed_doc_id = sha256(b"synthetic changed source document").hexdigest()
    changed_source = old_source.model_copy(
        update={"sha256": changed_doc_id, "blocks": [old_source.blocks[0], changed_block]}
    )
    source_hash = digest(changed_source.model_dump(mode="json"))
    changed_manifest = old_manifest.model_copy(
        update={
            "case_id": "mutated",
            "source_sha256": source_hash,
            "sources": [
                SourceRecord(
                    name="mutated.docx",
                    sha256=changed_doc_id,
                    adapter="docx-v1",
                    revision="synthetic-v2",
                )
            ],
            "block_documents": {block.id: changed_doc_id for block in changed_source.blocks},
        }
    )
    path = case["packet"].parent / "mutated"
    write_packet(path, changed_source, changed_manifest)
    with pytest.raises(ValueError, match="different source packet"):
        validate_annotations(path, Annotations.model_validate(case["annotations"]))
    revised = deepcopy(case["annotations"])
    revised.update(case_id="mutated", source_sha256=source_hash, revision=2)
    revised["labels"][1]["statement"] = changed_block.text
    for label, block in zip(revised["labels"], changed_source.blocks, strict=True):
        label["evidence"][0].update(
            document_id=changed_doc_id,
            text_sha256=sha256(block.text.encode()).hexdigest(),
            end=len(block.text),
        )
    validate_annotations(path, Annotations.model_validate(revised))
    assert revised["labels"][1]["statement"] != case["annotations"]["labels"][1]["statement"]
    for original_path, content in original:
        assert original_path.read_bytes() == content


def test_scoring_cli_writes_an_offline_report_without_overwriting(case, monkeypatch, capsys):
    packet, annotations, assessment, artifacts = persist(case)
    output = packet / "reference/report.json"
    command = [
        "evaluation",
        "score",
        "--packet",
        str(packet),
        "--annotations",
        str(annotations),
        "--assessment",
        str(assessment),
        "--output",
        str(output),
    ]
    for name, path in artifacts.items():
        command.extend([f"--{name}", str(path)])
    monkeypatch.setattr(sys, "argv", command)
    main()
    assert json.loads(output.read_bytes())["semantic_acceptance"] == "pass"
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    assert "Wrote packet score" in capsys.readouterr().out


def test_unmapped_review_findings_remain_unassessed(case):
    case["outputs"]["review"]["findings"].append(
        {
            "target": "specification",
            "item_ids": [],
            "severity": "warning",
            "description": "Unassessed synthetic finding",
        }
    )
    report = score_packet(*persist(case))
    assert report["unmapped_review_findings"] == 1
    assert report["semantic_acceptance"] == "pending"


def test_pilot_freezes_label_revision_and_detects_later_edits(case):
    _, annotations, _, _ = persist(case)
    root = case["packet"].parent
    inventory = freeze_pilot(root, annotations_file="reference/annotations.json")
    assert verify_pilot(root) == inventory
    assert "synthetic/reference/annotations.json" in inventory.files
    with pytest.raises(FileExistsError):
        freeze_pilot(root, annotations_file="reference/annotations.json")
    annotations.write_bytes(annotations.read_bytes() + b" ")
    with pytest.raises(ValueError, match="changed"):
        verify_pilot(root)


def test_pilot_refuses_uncommitted_preparation_code(case, evaluation_repo):
    persist(case)
    (evaluation_repo / "uv.lock").write_text("changed\n")
    with pytest.raises(ValueError, match="Commit"):
        freeze_pilot(case["packet"].parent, annotations_file="reference/annotations.json")
