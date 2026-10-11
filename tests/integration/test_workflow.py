import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from soc_verifier.domain.models import PlanReview, ReviewFinding
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.graph import build_graph

pytestmark = pytest.mark.integration


class FakeLLM:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = 0

    def generate(self, *, instruction, context, schema):
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
    llm = FakeLLM(analysis, verification_plan, clean_review)
    artifacts = ArtifactStore(tmp_path)
    graph = build_graph(llm, artifacts, InMemorySaver(), max_revisions=2)
    result = graph.invoke(
        {"specification": specification.model_dump()}, {"configurable": {"thread_id": "ok"}}
    )
    assert result["status"] == "draft_ready"
    assert artifacts.read("result.json")["human_approved"] is False
    assert llm.calls == 3


def test_reviewer_can_request_a_revision(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    llm = FakeLLM(analysis, verification_plan, error_review(), verification_plan, clean_review)
    artifacts = ArtifactStore(tmp_path)
    graph = build_graph(llm, artifacts, InMemorySaver(), max_revisions=2)
    result = graph.invoke(
        {"specification": specification.model_dump()}, {"configurable": {"thread_id": "revise"}}
    )
    assert result["revision"] == 1
    assert result["status"] == "draft_ready"
    assert artifacts.exists("plan.r000.json") and artifacts.exists("plan.r001.json")
    assert llm.calls == 5


def test_revision_budget_stops_loop(tmp_path, specification, analysis, verification_plan):
    llm = FakeLLM(analysis, verification_plan, error_review(), verification_plan, error_review())
    artifacts = ArtifactStore(tmp_path)
    graph = build_graph(llm, artifacts, InMemorySaver(), max_revisions=1)
    result = graph.invoke(
        {"specification": specification.model_dump()}, {"configurable": {"thread_id": "limit"}}
    )
    assert result["status"] == "needs_review"
    assert artifacts.read("result.json")["revision_limit_reached"] is True
    assert llm.calls == 5


def test_resume_after_restart_does_not_repeat_completed_nodes(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    artifacts = ArtifactStore(tmp_path / "run")
    database = str(tmp_path / "checkpoints.sqlite")
    config = {"configurable": {"thread_id": "restart"}}
    first = FakeLLM(analysis, verification_plan, RuntimeError("provider unavailable"))
    with SqliteSaver.from_conn_string(database) as checkpoints:
        graph = build_graph(first, artifacts, checkpoints, max_revisions=1)
        with pytest.raises(RuntimeError, match="provider unavailable"):
            graph.invoke({"specification": specification.model_dump()}, config, durability="sync")
    second = FakeLLM(clean_review)
    with SqliteSaver.from_conn_string(database) as checkpoints:
        graph = build_graph(second, artifacts, checkpoints, max_revisions=1)
        result = graph.invoke(None, config, durability="sync")
    assert result["status"] == "draft_ready"
    assert second.calls == 1


def test_extraction_gaps_remain_visible(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    specification = specification.model_copy(
        update={"extraction_warnings": ["Diagram not interpreted"]}
    )
    graph = build_graph(
        FakeLLM(analysis, verification_plan, clean_review),
        ArtifactStore(tmp_path),
        InMemorySaver(),
        max_revisions=0,
    )
    result = graph.invoke(
        {"specification": specification.model_dump()}, {"configurable": {"thread_id": "gap"}}
    )
    assert result["status"] == "needs_review"


def test_invalid_analysis_never_reaches_planner(tmp_path, specification, analysis):
    invalid = analysis.model_copy(
        update={
            "requirements": [
                analysis.requirements[0].model_copy(update={"source_ids": ["fabricated"]})
            ]
        }
    )
    llm = FakeLLM(invalid)
    graph = build_graph(llm, ArtifactStore(tmp_path), InMemorySaver(), max_revisions=0)
    with pytest.raises(ValueError, match="unknown source"):
        graph.invoke(
            {"specification": specification.model_dump()},
            {"configurable": {"thread_id": "invalid"}},
        )
    assert llm.calls == 1


def test_replayed_nodes_reuse_saved_artifacts(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    artifacts = ArtifactStore(tmp_path)
    first = build_graph(
        FakeLLM(analysis, verification_plan, clean_review),
        artifacts,
        InMemorySaver(),
        max_revisions=0,
    )
    config = {"configurable": {"thread_id": "replay"}}
    initial = {"specification": specification.model_dump()}
    first.invoke(initial, config)
    # Simulate checkpoint loss after artifacts have already been published.
    no_calls = FakeLLM()
    second = build_graph(no_calls, artifacts, InMemorySaver(), max_revisions=0)
    assert second.invoke(initial, config)["status"] == "draft_ready"
    assert no_calls.calls == 0
