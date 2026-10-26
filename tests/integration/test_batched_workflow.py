import json

import pytest

from soc_verifier.agents import instructions as prompts
from soc_verifier.domain.models import (
    PlanReview,
    Requirement,
    Specification,
    VerificationItem,
    VerificationPlan,
)
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.batching import AnalysisBatch
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow

pytestmark = pytest.mark.integration


class EvidenceAgents:
    def __init__(self, fail_source=None):
        self.fail_source = fail_source
        self.chunk_calls = []
        self.reviewed = []

    def run(self, *, role, instruction, context, schema):
        payload = json.loads(context)
        if instruction == prompts.ANALYZE_CHUNK:
            block = payload["evidence"][0]
            self.chunk_calls.append(block["id"])
            if block["id"] == self.fail_source:
                raise RuntimeError("interrupted chunk")
            result = AnalysisBatch(
                requirements=[
                    Requirement(
                        id="local-id",
                        statement=block["text"],
                        feature=block["section"],
                        basis="explicit",
                        source_ids=[block["id"]],
                        rationale="Stated",
                        open_questions=[],
                    )
                ],
                gaps=[],
            )
        elif instruction == prompts.ANALYZE_SYSTEM:
            result = AnalysisBatch(
                requirements=[
                    Requirement(
                        id="interaction",
                        statement="Reset must clear interrupts before boot completes.",
                        feature="Reset/boot interaction",
                        basis="derived",
                        source_ids=["P00001", "P00002"],
                        rationale="Cross-component ordering",
                        open_questions=[],
                    )
                ],
                gaps=[],
            )
        elif schema is VerificationPlan:
            result = VerificationPlan(
                items=[
                    VerificationItem(
                        id=f"local-{number}",
                        requirement_ids=[requirement["id"]],
                        feature=requirement["feature"],
                        objective=requirement["statement"],
                        method="simulation",
                        preconditions=[],
                        stimulus=["Exercise the specified behavior"],
                        expected_results=[requirement["statement"]],
                        coverage_intent=[],
                        environment_needs=[],
                        priority="high",
                        open_questions=[],
                    )
                    for number, requirement in enumerate(
                        payload["assigned_requirements"]["requirements"]
                    )
                ]
            )
        else:
            if instruction == prompts.REVIEW_CHUNK:
                self.reviewed.extend(item["id"] for item in payload["evidence"])
            result = PlanReview(findings=[])
        return schema.model_validate(result.model_dump())


def large_spec(specification):
    blocks = [
        specification.blocks[0].model_copy(
            update={
                "id": f"P{index:05d}",
                "section": f"Feature {index}",
                "text": f"Requirement {index}: " + "Reset must clear pending interrupts. " * 12,
            }
        )
        for index in range(1, 4)
    ]
    return specification.model_copy(update={"blocks": blocks})


@pytest.mark.parametrize("workers", [1, 2])
def test_large_spec_preserves_evidence_and_system_interactions(tmp_path, specification, workers):
    spec = large_spec(specification)
    artifacts = ArtifactStore(tmp_path)
    agents = EvidenceAgents()
    workflow = PlanningWorkflow(
        agents,
        artifacts,
        max_revisions=0,
        chunk_max_characters=1000,
        plan_batch_size=1,
        batch_workers=workers,
    )
    result = workflow.run(Specification.model_validate(spec.model_dump()))
    assert result["status"] == "draft_ready"
    assert sorted(agents.chunk_calls) == ["P00001", "P00002", "P00003"]
    assert sorted(agents.reviewed) == ["P00001", "P00002", "P00003"]
    assert len(result["analysis"]["requirements"]) == 4
    assert len(result["plan"]["items"]) == 4
    assert len({item["id"] for item in result["plan"]["items"]}) == 4
    assert artifacts.exists("analysis.r000.system.json")
    assert artifacts.exists("review.r000.system.json")
    assert artifacts.read("result.json")["human_approved"] is False


def test_restart_reuses_completed_chunks(tmp_path, specification):
    spec = large_spec(specification)
    artifacts = ArtifactStore(tmp_path / "run")
    workflow = PlanningWorkflow(
        EvidenceAgents(fail_source="P00002"),
        artifacts,
        max_revisions=0,
        chunk_max_characters=1000,
        plan_batch_size=1,
    )
    with pytest.raises(RuntimeError, match="interrupted chunk"):
        workflow.run(Specification.model_validate(spec.model_dump()))
    assert artifacts.exists("analysis.r000.chunk0000.json")
    remaining = EvidenceAgents()
    workflow = PlanningWorkflow(
        remaining, artifacts, max_revisions=0, chunk_max_characters=1000, plan_batch_size=1
    )
    assert workflow.run()["status"] == "draft_ready"
    assert remaining.chunk_calls == ["P00002", "P00003"]


@pytest.mark.parametrize("repair_succeeds", [True, False])
def test_chunk_citation_correction_is_bounded(tmp_path, specification, repair_succeeds):

    class InvalidCitationAgents(EvidenceAgents):
        def run(self, *, role, instruction, context, schema):
            result = super().run(instruction=instruction, context=context, schema=schema, role=role)
            if instruction == prompts.ANALYZE_CHUNK and self.chunk_calls[-1] == "P00001":
                payload = json.loads(context)
                if "validation_feedback" in payload:
                    assert payload["validation_feedback"]["unknown_source_ids"] == ["invented"]
                if not repair_succeeds or "validation_feedback" not in payload:
                    result = result.model_copy(
                        update={
                            "requirements": [
                                result.requirements[0].model_copy(
                                    update={"source_ids": ["invented"]}
                                )
                            ]
                        }
                    )
            return result

    agents = InvalidCitationAgents()
    artifacts = ArtifactStore(tmp_path)
    workflow = PlanningWorkflow(agents, artifacts, max_revisions=0, chunk_max_characters=1000)
    initial = {"specification": large_spec(specification).model_dump()}
    if repair_succeeds:
        workflow.run(Specification.model_validate(initial["specification"]))
        assert artifacts.exists("result.json")
    else:
        with pytest.raises(ValueError, match="after one correction"):
            workflow.run(Specification.model_validate(initial["specification"]))
        assert not artifacts.exists("analysis.r000.chunk0000.json")
    assert agents.chunk_calls.count("P00001") == 2


@pytest.mark.parametrize("repair_succeeds", [True, False])
@pytest.mark.parametrize("defect", ["missing", "unknown"])
def test_plan_batch_traceability_correction_is_bounded(
    tmp_path, specification, repair_succeeds, defect
):

    class BrokenPlanAgents(EvidenceAgents):
        first_group = None
        first_group_calls = 0

        def run(self, *, role, instruction, context, schema):
            result = super().run(instruction=instruction, context=context, schema=schema, role=role)
            if schema is not VerificationPlan:
                return result
            payload = json.loads(context)
            assigned = [r["id"] for r in payload["assigned_requirements"]["requirements"]]
            if self.first_group is None:
                self.first_group = assigned
            if assigned == self.first_group:
                self.first_group_calls += 1
                if "validation_feedback" in payload:
                    feedback = payload["validation_feedback"]
                    assert feedback["missing_requirement_ids"] == [assigned[0]]
                    assert feedback["unknown_requirement_ids"] == (
                        ["invented"] if defect == "unknown" else []
                    )
                    assert "previous_plan" in payload
                if not repair_succeeds or "validation_feedback" not in payload:
                    items = (
                        result.items[1:]
                        if defect == "missing"
                        else [
                            result.items[0].model_copy(update={"requirement_ids": ["invented"]}),
                            *result.items[1:],
                        ]
                    )
                    result = result.model_copy(update={"items": items})
            return result

    agents = BrokenPlanAgents()
    artifacts = ArtifactStore(tmp_path)
    workflow = PlanningWorkflow(
        agents, artifacts, max_revisions=0, chunk_max_characters=1000, plan_batch_size=2
    )
    initial = {"specification": large_spec(specification).model_dump()}
    if repair_succeeds:
        workflow.run(Specification.model_validate(initial["specification"]))
        assert artifacts.exists("result.json")
        assert artifacts.exists("plan.r000.batch0000.json")
    else:
        with pytest.raises(ValueError, match="after one correction"):
            workflow.run(Specification.model_validate(initial["specification"]))
        assert not artifacts.exists("plan.r000.batch0000.json")
        assert not artifacts.exists("result.json")
    assert artifacts.exists("analysis.json")
    assert agents.first_group_calls == 2
