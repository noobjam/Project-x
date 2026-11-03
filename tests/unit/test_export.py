import pytest
from openpyxl import load_workbook

from soc_verifier.export.xlsx import export_plan


def test_export_preserves_text_ids_and_traceability(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    destination = tmp_path / "plan.xlsx"
    item = verification_plan.items[0].model_copy(
        update={"id": "1.10", "objective": '=HYPERLINK("https://example.com", "text")'}
    )
    plan = verification_plan.model_copy(update={"items": [item]})
    export_plan(
        destination, specification=specification, analysis=analysis, plan=plan, review=clean_review
    )
    workbook = load_workbook(destination)
    assert workbook.sheetnames == ["Verification plan", "Requirements", "Evidence", "Findings"]
    sheet = workbook["Verification plan"]
    assert sheet["A2"].value == "1.10"
    assert sheet["D2"].data_type == "s"
    assert sheet.freeze_panes == "C2"
    assert workbook["Evidence"]["A2"].value == "P00001"
    workbook.close()
    with pytest.raises(FileExistsError):
        export_plan(
            destination,
            specification=specification,
            analysis=analysis,
            plan=plan,
            review=clean_review,
        )


def test_failed_export_leaves_no_destination_and_can_retry(
    tmp_path, monkeypatch, specification, analysis, verification_plan, clean_review
):
    destination = tmp_path / "plan.xlsx"
    arguments = {
        "specification": specification,
        "analysis": analysis,
        "plan": verification_plan,
        "review": clean_review,
    }

    def fail(self, stream):
        stream.write(b"partial workbook")
        raise OSError("simulated disk failure")

    with monkeypatch.context() as patch:
        patch.setattr("soc_verifier.export.xlsx.Workbook.save", fail)
        with pytest.raises(OSError, match="disk failure"):
            export_plan(destination, **arguments)
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []
    export_plan(destination, **arguments)
    workbook = load_workbook(destination)
    assert workbook["Verification plan"]["A2"].value == verification_plan.items[0].id
    workbook.close()


@pytest.mark.parametrize("version", ["1.0", "2.0", "3.0", "4.0"])
def test_review_versions_remain_exportable_with_scope_visible(
    tmp_path, specification, analysis, verification_plan, version
):
    from soc_verifier.domain.review import read_review

    finding = {"severity": "warning", "target": "specification", "description": "Timing unresolved"}
    if version == "1.0":
        finding["item_ids"] = []
    else:
        finding.update(
            {
                "kind": "timing",
                "recommended_action": "=1+1",
                "scope": {
                    "kind": "requirements",
                    "requirement_ids": [analysis.requirements[0].id],
                    "rationale": "Synthetic scope",
                    "evidence": [{"source_id": "P00001", "quote": specification.blocks[0].text}],
                },
            }
        )
    path = tmp_path / "review.xlsx"
    export_plan(
        path,
        specification=specification,
        analysis=analysis,
        plan=verification_plan,
        review=read_review({"schema_version": version, "findings": [finding]}),
    )
    workbook = load_workbook(path)
    sheet = workbook["Findings"]
    assert sheet["D2"].value == "Timing unresolved"
    assert sheet["E2"].value == ("unknown (legacy)" if version == "1.0" else "requirements")
    if version != "1.0":
        assert sheet["F2"].value == analysis.requirements[0].id
        assert sheet["K2"].value == "=1+1" and sheet["K2"].data_type == "s"
        assert specification.blocks[0].text in sheet["H2"].value
    workbook.close()


@pytest.mark.parametrize("version", ["3.0", "4.0"])
def test_acceptance_notes_export_with_their_evidence_and_pending_approval(
    tmp_path, specification, analysis, verification_plan, version
):
    from soc_verifier.domain.review import read_review

    block = specification.blocks[0].model_copy(
        update={"id": "DRAFT", "text": "Draft; engineering review is pending."}
    )
    spec = specification.model_copy(update={"blocks": [*specification.blocks, block]})
    review = read_review(
        {
            "schema_version": version,
            "findings": [],
            "acceptance_notes": [
                {
                    "kind": "pending_engineering_review",
                    "description": "=1+1",
                    "rationale": "=Approval is separate from executable behavior",
                    "evidence": [{"source_id": block.id, "quote": block.text}],
                }
            ],
        }
    )
    path = tmp_path / "notes.xlsx"
    export_plan(path, specification=spec, analysis=analysis, plan=verification_plan, review=review)
    workbook = load_workbook(path)
    sheet = workbook["Acceptance notes"]
    assert sheet["B2"].value == "=1+1" and sheet["B2"].data_type == "s"
    assert sheet["C2"].data_type == "s"
    assert sheet["D2"].value == f"DRAFT: {block.text}"
    assert sheet["E2"].value == "agent_proposed"
    assert sheet["F2"].value == "Pending human review"
    assert workbook["Evidence"]["A3"].value == "DRAFT"
    workbook.close()


def test_global_dependencies_are_inspectable_in_export(
    tmp_path, specification, analysis, verification_plan
):
    from soc_verifier.domain.review import ScopedPlanReview

    item = verification_plan.items[0]
    review = ScopedPlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "target": "specification",
                    "kind": "timing",
                    "description": "Reset timing is unresolved.",
                    "recommended_action": "Clarify the reset definition.",
                    "scope": {
                        "kind": "global",
                        "rationale": "Every scenario requires reset.",
                        "evidence": [
                            {"source_id": "P00001", "quote": specification.blocks[0].text}
                        ],
                        "dependencies": [
                            {
                                "plan_item_id": item.id,
                                "plan_field": "stimulus",
                                "plan_quote": item.stimulus[0],
                                "evidence_indices": [0],
                                "rationale": "=Reset stimulus depends on this definition",
                            }
                        ],
                    },
                }
            ]
        }
    )
    path = tmp_path / "dependencies.xlsx"
    export_plan(
        path, specification=specification, analysis=analysis, plan=verification_plan, review=review
    )
    workbook = load_workbook(path)
    sheet = workbook["Global dependencies"]
    assert sheet["A2"].value == "review:0"
    assert sheet["B2"].value == item.id
    assert sheet["C2"].value == "stimulus"
    assert sheet["D2"].value == item.stimulus[0]
    assert specification.blocks[0].text in sheet["E2"].value
    assert sheet["F2"].data_type == "s"
    workbook.close()


def test_source_audit_export_keeps_evidence_and_provisional_judgments_as_text(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    from soc_verifier.domain.source_audit import KnowledgeApplication, SourceAudit, SourceFinding

    audit = SourceAudit(
        findings=[
            SourceFinding(
                id="F1",
                kind="lost_qualifier",
                requirement_ids=[analysis.requirements[0].id],
                evidence_ids=["P00001:U00000"],
                description="=1+1",
                recommended_action="Check controller scope",
                conflict=None,
            )
        ],
        knowledge_applications=[
            KnowledgeApplication(
                entry_id="K01",
                requirement_ids=[analysis.requirements[0].id],
                evidence_ids=["P00001:U00000"],
                assessment="uncertain",
                rationale="=1+1",
            )
        ],
    )
    path = tmp_path / "audit.xlsx"
    export_plan(
        path,
        specification=specification,
        analysis=analysis,
        plan=verification_plan,
        review=clean_review,
        source_audit=audit,
    )
    workbook = load_workbook(path)
    assert workbook["Source audit"]["E2"].value == specification.blocks[0].text
    assert workbook["Source audit"]["F2"].data_type == "s"
    assert workbook["Source audit"]["M2"].value == "agent_proposed"
    assert workbook["Knowledge application"]["E2"].data_type == "s"
    assert workbook["Knowledge application"]["F2"].value == "agent_proposed"
    workbook.close()
