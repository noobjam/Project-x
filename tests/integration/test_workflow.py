import pytest

from soc_verifier.domain.models import PlanReview, ReviewFinding, Specification
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow

pytestmark = pytest.mark.integration


class FakeAgents:
    @property
    def configuration(self):
        return {}

    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = 0

    def run(self, *, role, instruction, context, schema, task=None):
        self.calls += 1
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return schema.model_validate(response.model_dump())


def error_review():
    return PlanReview(
        findings=[
            ReviewFinding(
                severity="error", item_ids=["VPLAN-RST-001"], description="Strengthen reset checks"
            )
        ]
    )


def test_success_is_a_draft_not_approval(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    agents = FakeAgents(analysis, verification_plan, clean_review)
    artifacts = ArtifactStore(tmp_path)
    workflow = PlanningWorkflow(agents, artifacts, max_revisions=2)
    result = workflow.run(Specification.model_validate(specification.model_dump()))
    assert result["status"] == "draft_ready"
    assert artifacts.read("result.json")["human_approved"] is False
    assert agents.calls == 3


@pytest.mark.parametrize("corrected", [True, False])
def test_review_reference_correction_preserves_only_valid_artifacts(
    tmp_path, specification, analysis, verification_plan, corrected
):
    invalid = PlanReview(
        findings=[
            ReviewFinding(
                severity="warning",
                target="specification",
                item_ids=["REQ-RST-001"],
                description="Missing timing information",
            )
        ]
    )
    valid = PlanReview(findings=[invalid.findings[0].model_copy(update={"item_ids": []})])
    agents = FakeAgents(analysis, verification_plan, invalid, valid if corrected else invalid)
    artifacts = ArtifactStore(tmp_path)
    workflow = PlanningWorkflow(agents, artifacts, max_revisions=0)
    initial = {"specification": specification.model_dump()}
    if corrected:
        result = workflow.run(Specification.model_validate(initial["specification"]))
        assert result["status"] == "needs_review"
        assert artifacts.read("review.r000.json") == valid.model_dump(mode="json")
    else:
        with pytest.raises(ValueError, match="after one correction"):
            workflow.run(Specification.model_validate(initial["specification"]))
        assert not artifacts.exists("review.r000.json")
        assert not artifacts.exists("result.json")
    assert artifacts.exists("analysis.json")
    assert artifacts.exists("plan.r000.json")
    assert agents.calls == 4


def test_reviewer_can_request_a_revision(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    agents = FakeAgents(
        analysis, verification_plan, error_review(), verification_plan, clean_review
    )
    artifacts = ArtifactStore(tmp_path)
    workflow = PlanningWorkflow(agents, artifacts, max_revisions=2)
    result = workflow.run(Specification.model_validate(specification.model_dump()))
    assert result["revision"] == 1
    assert result["status"] == "draft_ready"
    assert artifacts.exists("plan.r000.json") and artifacts.exists("plan.r001.json")
    assert agents.calls == 5


def test_revision_budget_stops_loop(tmp_path, specification, analysis, verification_plan):
    agents = FakeAgents(
        analysis, verification_plan, error_review(), verification_plan, error_review()
    )
    artifacts = ArtifactStore(tmp_path)
    workflow = PlanningWorkflow(agents, artifacts, max_revisions=1)
    result = workflow.run(Specification.model_validate(specification.model_dump()))
    assert result["status"] == "needs_review"
    assert artifacts.read("result.json")["revision_limit_reached"] is True
    assert agents.calls == 5


def test_resume_after_restart_does_not_repeat_completed_nodes(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    artifacts = ArtifactStore(tmp_path / "run")
    first = FakeAgents(analysis, verification_plan, RuntimeError("provider unavailable"))
    workflow = PlanningWorkflow(first, artifacts, max_revisions=1)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        workflow.run(Specification.model_validate(specification.model_dump()))
    second = FakeAgents(clean_review)
    workflow = PlanningWorkflow(second, artifacts, max_revisions=1)
    result = workflow.run()
    assert result["status"] == "draft_ready"
    assert second.calls == 1


def test_extraction_gaps_remain_visible(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    specification = specification.model_copy(
        update={"extraction_warnings": ["Diagram not interpreted"]}
    )
    workflow = PlanningWorkflow(
        FakeAgents(analysis, verification_plan, clean_review),
        ArtifactStore(tmp_path),
        max_revisions=0,
    )
    result = workflow.run(Specification.model_validate(specification.model_dump()))
    assert result["status"] == "needs_review"


def test_invalid_analysis_never_reaches_planner(tmp_path, specification, analysis):
    invalid = analysis.model_copy(
        update={
            "requirements": [
                analysis.requirements[0].model_copy(update={"source_ids": ["fabricated"]})
            ]
        }
    )
    agents = FakeAgents(invalid)
    workflow = PlanningWorkflow(agents, ArtifactStore(tmp_path), max_revisions=0)
    with pytest.raises(ValueError, match="unknown source"):
        workflow.run(Specification.model_validate(specification.model_dump()))
    assert agents.calls == 1


def test_replayed_nodes_reuse_saved_artifacts(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    artifacts = ArtifactStore(tmp_path)
    first = PlanningWorkflow(
        FakeAgents(analysis, verification_plan, clean_review), artifacts, max_revisions=0
    )
    initial = {"specification": specification.model_dump()}
    first.run(Specification.model_validate(initial["specification"]))
    no_calls = FakeAgents()
    second = PlanningWorkflow(no_calls, artifacts, max_revisions=0)
    assert (
        second.run(Specification.model_validate(initial["specification"]))["status"]
        == "draft_ready"
    )
    assert no_calls.calls == 0


def test_missing_requirement_routes_back_to_analysis(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    missing = PlanReview(
        findings=[
            ReviewFinding(
                severity="error",
                target="analysis",
                item_ids=[],
                description="A second reset requirement was omitted from analysis.",
            )
        ]
    )
    repaired = analysis.model_copy(
        update={
            "requirements": [
                *analysis.requirements,
                analysis.requirements[0].model_copy(update={"id": "REQ-RST-002"}),
            ]
        }
    )
    repaired_plan = verification_plan.model_copy(
        update={
            "items": [
                verification_plan.items[0].model_copy(
                    update={"requirement_ids": ["REQ-RST-001", "REQ-RST-002"]}
                )
            ]
        }
    )
    agents = FakeAgents(analysis, verification_plan, missing, repaired, repaired_plan, clean_review)
    artifacts = ArtifactStore(tmp_path)
    workflow = PlanningWorkflow(agents, artifacts, max_revisions=1)
    result = workflow.run(Specification.model_validate(specification.model_dump()))
    assert result["status"] == "draft_ready"
    assert agents.calls == 6
    assert len(artifacts.read("analysis.json")["requirements"]) == 1
    final = artifacts.read("result.json")
    assert len(artifacts.read(final["analysis_artifact"])["requirements"]) == 2
    assert final["revision"] == 1
    assert final["revision_limit_reached"] is False


def test_specification_gaps_do_not_trigger_unfixable_revisions(
    tmp_path, specification, analysis, verification_plan
):
    gap = PlanReview(
        findings=[
            ReviewFinding(
                severity="error",
                target="specification",
                item_ids=[],
                description="The source does not define reset timing; ask the specification owner.",
            )
        ]
    )
    agents = FakeAgents(analysis, verification_plan, gap)
    artifacts = ArtifactStore(tmp_path)
    workflow = PlanningWorkflow(agents, artifacts, max_revisions=2)
    result = workflow.run(Specification.model_validate(specification.model_dump()))
    assert result["status"] == "needs_review"
    assert agents.calls == 3
    assert artifacts.read("result.json")["revision_limit_reached"] is False


def test_analysis_revision_budget_and_restart(tmp_path, specification, analysis, verification_plan):
    missing = PlanReview(
        findings=[
            ReviewFinding(
                severity="error", target="analysis", item_ids=[], description="Missing requirement"
            )
        ]
    )
    artifacts = ArtifactStore(tmp_path / "run")
    first = FakeAgents(analysis, verification_plan, missing, RuntimeError("provider unavailable"))
    workflow = PlanningWorkflow(first, artifacts, max_revisions=1)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        workflow.run(Specification.model_validate(specification.model_dump()))
    second = FakeAgents(analysis, verification_plan, missing)
    workflow = PlanningWorkflow(second, artifacts, max_revisions=1)
    result = workflow.run()
    assert result["status"] == "needs_review"
    assert result["analysis_revision"] == 1
    assert second.calls == 3
    assert artifacts.read("result.json")["revision_limit_reached"] is True


@pytest.mark.parametrize("change", ["prompt", "processing", "code", "partition"])
def test_resume_rejects_changed_execution_before_any_agent_calls(
    tmp_path, specification, analysis, verification_plan, clean_review, monkeypatch, change
):
    import soc_verifier.workflows.spec_to_plan.workflow as module

    artifacts = ArtifactStore(tmp_path)
    PlanningWorkflow(
        FakeAgents(analysis, verification_plan, clean_review), artifacts, max_revisions=0
    ).run(specification)
    versions = module.runtime_versions()
    if change != "partition":
        key = {"prompt": "prompt", "processing": "source_processing", "code": "code_sha256"}[change]
        monkeypatch.setattr(module, "runtime_versions", lambda: {**versions, key: "different"})
    agents = FakeAgents()
    with pytest.raises(ValueError, match="Run inputs or versions changed"):
        PlanningWorkflow(
            agents, artifacts, max_revisions=0, plan_batch_size=4 if change == "partition" else 8
        ).run()
    assert agents.calls == 0
