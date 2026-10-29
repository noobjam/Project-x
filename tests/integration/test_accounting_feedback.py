import json

import pytest

from soc_verifier.domain.passage_accounting import AccountingValidationError, PassageDisposition
from soc_verifier.domain.source_audit import SourceFinding
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.source_audit import read_source_audit
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow

pytestmark = pytest.mark.integration


class ScriptedAgents:
    def __init__(self, *responses):
        self.configuration = {}
        self.responses = iter(responses)
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        output = next(self.responses)
        if isinstance(output, Exception):
            raise output
        return kwargs["schema"].model_validate(output.model_dump())


def overlapping(draft):
    return draft.model_copy(
        update={
            "dispositions": [
                PassageDisposition(
                    evidence_ids=draft.obligations[0].evidence_ids,
                    status="non_normative",
                    reason="Inline reference",
                )
            ]
        }
    )


def test_feedback_correction_and_analysis_only_resume(
    tmp_path, specification, passage_accounting_draft, clean_audit, verification_plan, clean_review
):
    store = ArtifactStore(tmp_path)
    bad = overlapping(passage_accounting_draft)
    first = ScriptedAgents(bad, RuntimeError("interruption"))
    with pytest.raises(RuntimeError, match="interruption"):
        PlanningWorkflow(first, store, 0, source_accounting=True).run(
            specification, analysis_only=True
        )
    assert store.exists("obligations.r000.attempt0.completed.json")
    assert not store.exists("obligations.r000.completed.json")
    second = ScriptedAgents(passage_accounting_draft, clean_audit)
    result = PlanningWorkflow(second, store, 0, source_accounting=True).run(analysis_only=True)
    assert result["status"] == "analysis_ready" and not store.exists("result.json")
    assert [c["role"] for c in second.calls] == ["analyst", "reviewer"]
    feedback = json.loads(second.calls[0]["context"])["validation_feedback"]
    assert feedback["issues"][0]["code"] == "non_normative_evidence"
    assert "extra:obligations.r000.attempt0.json" in second.calls[0]["task"].inputs.evidence
    third = ScriptedAgents(verification_plan, clean_review)
    result = PlanningWorkflow(third, store, 0, source_accounting=True).run()
    assert [c["role"] for c in third.calls] == ["planner", "reviewer"]
    assert result["status"] == "draft_ready"
    assert "source_audit" in third.calls[0]["task"].inputs.evidence
    assert read_source_audit(store, "source-audit.r000.json") == clean_audit
    # Every completed draft/audit/plan is reused, including the rejected first attempt.
    PlanningWorkflow(ScriptedAgents(), store, 0, source_accounting=True).run()


def test_two_invalid_disposition_attempts_stay_exhausted_after_resume(
    tmp_path, specification, passage_accounting_draft
):
    store = ArtifactStore(tmp_path)
    bad = overlapping(passage_accounting_draft)
    agents = ScriptedAgents(bad, bad)
    with pytest.raises(AccountingValidationError):
        PlanningWorkflow(agents, store, 0, source_accounting=True).run(specification)
    assert len(agents.calls) == 2 and not store.exists("analysis.json")
    assert not store.read("obligations.r000.attempt1.feedback.json")["correction_remaining"]
    with pytest.raises(AccountingValidationError):
        PlanningWorkflow(ScriptedAgents(), store, 0, source_accounting=True).run()


@pytest.mark.parametrize("change", ["delete", "statement", "evidence", "gaps"])
def test_correction_cannot_hide_or_rewrite_obligations(
    tmp_path, specification, passage_accounting_draft, change
):
    first = passage_accounting_draft.obligations[0]
    second = first.model_copy(update={"id": "REQ-SECOND"})
    original = passage_accounting_draft.model_copy(update={"obligations": [first, second]})
    if change == "delete":
        corrected = original.model_copy(update={"obligations": [first]})
    elif change == "gaps":
        original = original.model_copy(update={"gaps": ["Unknown latency"]})
        corrected = original.model_copy(update={"gaps": []})
    else:
        modified = first.model_copy(
            update={"statement": "Invented behavior"}
            if change == "statement"
            else {"evidence_ids": first.evidence_ids * 2}
        )
        corrected = original.model_copy(update={"obligations": [modified, second]})
    store = ArtifactStore(tmp_path)
    with pytest.raises(ValueError, match="frozen obligations"):
        PlanningWorkflow(
            ScriptedAgents(overlapping(original), corrected), store, 0, source_accounting=True
        ).run(specification)
    assert not store.exists("analysis.json")


@pytest.mark.parametrize(
    "file",
    [
        "obligations.r000.attempt0.json",
        "obligations.r000.attempt0.feedback.json",
        "source-audit.r000.json",
    ],
)
def test_attempt_feedback_and_audit_tampering_fail_before_more_calls(
    tmp_path, specification, passage_accounting_draft, clean_audit, file
):
    store = ArtifactStore(tmp_path)
    PlanningWorkflow(
        ScriptedAgents(
            overlapping(passage_accounting_draft), passage_accounting_draft, clean_audit
        ),
        store,
        0,
        source_accounting=True,
    ).run(specification, analysis_only=True)
    store.path(file).write_text("{}")
    with pytest.raises((ValueError, FileExistsError)):
        PlanningWorkflow(ScriptedAgents(), store, 0, source_accounting=True).run()


def test_advisory_audit_is_visible_to_planner_and_cannot_be_erased_by_clean_plan_review(
    tmp_path, specification, passage_accounting_draft, clean_audit, verification_plan, clean_review
):
    audit = clean_audit.model_copy(
        update={
            "findings": [
                SourceFinding(
                    id="F1",
                    kind="omission",
                    requirement_ids=[],
                    evidence_ids=["P00001:U00000"],
                    description="Provisional omission for owner review",
                    recommended_action="Check source scope",
                    conflict=None,
                )
            ]
        }
    )
    agents = ScriptedAgents(passage_accounting_draft, audit, verification_plan, clean_review)
    store = ArtifactStore(tmp_path)
    result = PlanningWorkflow(agents, store, 0, source_accounting=True).run(specification)
    assert (
        json.loads(agents.calls[2]["context"])["source_audit"]["judgment_state"] == "agent_proposed"
    )
    assert result["status"] == "needs_review"
    assert store.read("result.json")["human_approved"] is False


def test_invalid_audit_fails_before_planning(
    tmp_path, specification, passage_accounting_draft, clean_audit
):
    audit = clean_audit.model_copy(
        update={
            "findings": [
                SourceFinding(
                    id="F1",
                    kind="omission",
                    requirement_ids=[],
                    evidence_ids=["invented"],
                    description="Invalid citation",
                    recommended_action="Check source",
                    conflict=None,
                )
            ]
        }
    )
    agents = ScriptedAgents(passage_accounting_draft, audit)
    store = ArtifactStore(tmp_path)
    with pytest.raises(ValueError, match=r"unknown|Input should"):
        PlanningWorkflow(agents, store, 0, source_accounting=True).run(specification)
    assert [c["role"] for c in agents.calls] == ["analyst", "reviewer"]
    assert not store.exists("source-audit.r000.completed.json")
    assert not store.exists("plan.r000.json")


def test_batched_planners_receive_relevant_and_global_audit_findings(
    tmp_path, specification, passage_accounting_draft, clean_audit, verification_plan, clean_review
):
    from soc_verifier.domain.models import VerificationPlan
    from soc_verifier.domain.source_audit import SourceAudit

    first = passage_accounting_draft.obligations[0]
    draft = passage_accounting_draft.model_copy(
        update={"obligations": [first, first.model_copy(update={"id": "REQ-SECOND"})]}
    )
    audit = clean_audit.model_copy(
        update={
            "findings": [
                SourceFinding(
                    id=identifier,
                    kind="omission",
                    requirement_ids=ids,
                    evidence_ids=["P00001:U00000"],
                    description="Synthetic suggestion",
                    recommended_action="Check the cited evidence",
                    conflict=None,
                )
                for identifier, ids in [("LOCAL", [first.id]), ("GLOBAL", [])]
            ]
        }
    )
    contexts = []

    class BatchedAgents:
        @property
        def configuration(self):
            return {}

        def run(self, *, role, instruction, context, schema, task):
            if role == "analyst":
                return schema.model_validate(draft.model_dump())
            if issubclass(schema, SourceAudit):
                return audit
            if schema is VerificationPlan:
                payload = json.loads(context)
                contexts.append(payload)
                assigned = payload["assigned_requirements"]["requirements"][0]["id"]
                assert "source_audit" in task.inputs.evidence
                assert "unreviewed suggestions" in instruction
                return verification_plan.model_copy(
                    update={
                        "items": [
                            verification_plan.items[0].model_copy(
                                update={"requirement_ids": [assigned]}
                            )
                        ]
                    }
                )
            return clean_review

    store = ArtifactStore(tmp_path)
    result = PlanningWorkflow(
        BatchedAgents(), store, 0, source_accounting=True, plan_batch_size=1
    ).run(specification)
    assert result["status"] == "needs_review"
    assert [f["id"] for f in contexts[0]["source_audit"]["findings"]] == ["LOCAL", "GLOBAL"]
    assert [f["id"] for f in contexts[1]["source_audit"]["findings"]] == ["GLOBAL"]
