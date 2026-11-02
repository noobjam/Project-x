"""Actual SDK + tools + Icarus; only the model's HTTP replies are synthetic."""

import json
import shutil
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr
from typer.testing import CliRunner

from soc_verifier.agents import instructions
from soc_verifier.agents.base import ModelResponseError
from soc_verifier.agents.runtime import AgentRuntime
from soc_verifier.cli import app
from soc_verifier.domain.hardware import HardwareSnapshot, HardwareTarget
from soc_verifier.domain.review import ScopedPlanReview
from soc_verifier.domain.testbench_proposal import ObservedTestbenchProposal as Proposal
from soc_verifier.providers.budget import BudgetExceeded, read_spending
from soc_verifier.providers.reporting import read_task_report
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow
from soc_verifier.workflows.verification import VerificationWorkflow

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not shutil.which("iverilog") or not shutil.which("vvp"), reason="Icarus is not installed"
    ),
]
RTL = """module interrupt_ctrl(input clk, rst, output reg [3:0] pending);
initial pending = 4'hf;
always @(posedge clk) if (rst) pending <= 0;
endmodule
"""


def response(output):
    return httpx.Response(
        200,
        json={
            "id": "resp-synthetic",
            "object": "response",
            "created_at": 1,
            "model": "openai/gpt-6.1-terra",
            "status": "completed",
            "error": None,
            "output": output,
            "usage": {
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
                "cost": 0.0001,
            },
        },
    )


@pytest.fixture
def harness(tmp_path, specification, analysis, verification_plan, knowledge_snapshot):
    clients = []

    def make(
        *,
        use_knowledge=True,
        change=None,
        review=None,
        rtl=RTL,
        plan_output=None,
        analysis_output=None,
        gap_output=None,
        proposal_outputs=None,
        target_output=None,
        source_read_ids=None,
        source_query="reset",
        knowledge_read_ids=None,
        **settings_changes,
    ):
        directory = tmp_path / f"case-{len(clients)}"
        artifacts = ArtifactStore(directory)
        source_path = artifacts.path("input.sv")
        source_path.write_text(rtl)
        target = target_output or HardwareTarget.model_validate(
            {
                "top_module": "interrupt_ctrl",
                "parameters": {},
                "clock": "clk",
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "rst", "direction": "input", "width": 1},
                    {"name": "pending", "direction": "output", "width": 4},
                ],
            }
        )
        hardware = HardwareSnapshot.capture(target, [source_path])
        proposal = {
            "format": "testbench-proposal-v2",
            "plan_item_id": verification_plan.items[0].id,
            "status": "ready",
            "rationale": "Synthetic reset-check proposal for the integration test.",
            "initial_inputs": [{"signal": "rst", "value": 1}],
            "steps": [
                {
                    "description": "Assert reset",
                    "inputs": [],
                    "cycles": 1,
                    "checks": [
                        {
                            "signal": "pending",
                            "value": 0,
                            "expected_result_index": 0,
                            "phase": "post_edge",
                            "source_ids": ["P00001"],
                        }
                    ],
                }
            ],
            "rtl_source_ids": ["rtl-0"],
            "open_questions": [],
        }
        if change:
            change(proposal)
        requests = []

        def api(request):
            assert request.url.host == "openrouter.ai"
            if request.method == "GET":
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "endpoints": [
                                {
                                    "tag": "test-endpoint",
                                    "context_length": 1_000_000,
                                    "max_completion_tokens": 1000,
                                    "pricing": {"prompt": "0.0000001", "completion": "0.0000002"},
                                }
                            ]
                        }
                    },
                )
            assert request.url.path == "/api/v1/responses"
            payload = json.loads(request.content)
            assert payload["model"] == "openai/gpt-6.1-terra"
            assert payload["provider"]["only"] == ["test-endpoint"]
            assert payload["store"] is False
            requests.append(payload)
            instruction = payload["instructions"]
            role = {
                instructions.ANALYZE: "analyst",
                instructions.PLAN: "planner",
                instructions.REVIEW: "reviewer",
                instructions.BUILD_TESTBENCH: "testbench",
                instructions.BUILD_EXPERIMENTAL_TESTBENCH: "testbench",
                instructions.SCOPE_EXECUTION_GAPS: "gap_scope",
            }[instruction]
            schema = payload.get("text", {}).get("format", {}).get("schema", {})
            if role == "testbench" and schema:
                # Model the observed provider rejection instead of accepting every schema.
                for name in ("InputValue", "ProposedCheck"):
                    limit = schema["$defs"][name]["properties"]["value"].get("maximum")
                    if limit is not None and limit > 2**53 - 1:
                        return httpx.Response(400, json={"error": {"code": "invalid_json_schema"}})
            assert "hardware_target" in json.dumps(payload["input"])
            choice = payload.get("tool_choice")
            if isinstance(choice, dict) and choice["type"] == "function":
                name = choice["name"]
                arguments = {
                    "search_knowledge": {"query": "reset", "offset": 0},
                    "get_knowledge_entries": {
                        "ids": knowledge_read_ids or ["K01"],
                        "start_character": 0,
                    },
                    "search_spec": {"query": source_query, "offset": 0},
                    "get_source_blocks": {
                        "ids": source_read_ids or ["P00001"],
                        "start_character": 0,
                    },
                    "read_rtl": {"source_id": "rtl-0", "start_line": 1, "max_lines": 80},
                }[name]
                identifier = f"tool-{len(requests)}"
                return response(
                    [
                        {
                            "type": "function_call",
                            "id": identifier,
                            "call_id": identifier,
                            "name": name,
                            "arguments": json.dumps(arguments),
                            "status": "completed",
                        }
                    ]
                )
            output = {
                "analyst": (analysis_output or analysis).model_dump(),
                "planner": (plan_output or verification_plan).model_dump(),
                "reviewer": (review or ScopedPlanReview(findings=[])).model_dump(),
                "testbench": proposal,
                "gap_scope": gap_output,
            }[role]
            if role == "testbench" and proposal_outputs:
                user = next(m for m in payload["input"] if m.get("role") == "user")
                content = user["content"]
                text = content if isinstance(content, str) else "".join(p["text"] for p in content)
                context = json.loads(text.split("\nDeclared hardware configuration")[0])
                output = {**proposal, **proposal_outputs[context["plan_item"]["id"]]}
            return response(
                [
                    {
                        "type": "message",
                        "id": "final",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {"type": "output_text", "text": json.dumps(output), "annotations": []}
                        ],
                    }
                ]
            )

        settings = Settings(
            _env_file=None,
            **{
                "openrouter_api_key": SecretStr("test-only"),
                "model": "openai/gpt-6.1-terra",
                "provider": "test-endpoint",
                "model_api": "responses",
                "max_output_tokens": 256,
                "agent_max_turns": 8,
                "planner_source_lookup": True,
                "max_model_calls": 30,
                "max_revisions": 0,
                "artifact_dir": tmp_path / "cli-artifacts",
                **settings_changes,
            },
        )
        client = httpx.Client(transport=httpx.MockTransport(api))
        clients.append(client)
        if use_knowledge:
            artifacts.write("knowledge.json", knowledge_snapshot)
        runtime = AgentRuntime(settings, client, artifacts=artifacts)
        workflow = VerificationWorkflow(
            PlanningWorkflow(runtime, artifacts, max_revisions=0), hardware
        )
        return SimpleNamespace(
            workflow=workflow,
            artifacts=artifacts,
            requests=requests,
            settings=settings,
            hardware=hardware,
            client=client,
            api=api,
            target=target,
            rtl=source_path,
        )

    yield make
    for client in clients:
        client.close()


def test_all_agents_feed_real_execution_with_one_ledger_and_reusable_checkpoints(
    harness, specification
):
    run = harness()
    result = run.workflow.run(specification)
    assert result["status"] == "passed"
    assert result["unexecuted_item_ids"] == []
    assert result["human_approved"] is False
    assert len(run.requests) == 17
    report = read_task_report(run.artifacts)
    assert {row["role"] for row in report["tasks"]} == {
        "analyst",
        "planner",
        "reviewer",
        "testbench",
    }
    assert all(row["status"] == "completed" for row in report["tasks"])
    assert read_spending(run.artifacts).attempts == 17
    binding = run.artifacts.read("binding.000.json")
    assert binding["origin"] == "agent" and binding["format"] == "directed-testbench-v3"
    assert binding["proposal_sha256"] == result["cases"][0]["proposal"]["sha256"]
    assert run.artifacts.read("testbench.000.task.json")["format"] == "agent-task-v2"
    assert list(run.artifacts.root.glob("hardware-access.*.json"))
    assert run.workflow.run(specification) == result
    assert len(run.requests) == 17  # no inference or simulator rerun on completed resume
    assert len(list(run.artifacts.root.glob("simulation-000-*"))) == 1


def test_wrong_design_is_detected_through_connected_agent_path(harness, specification):
    run = harness(rtl=RTL.replace("pending <= 0", "pending <= 1"))
    result = run.workflow.run(specification)
    assert result["status"] == "failed"
    path = run.artifacts.root / result["cases"][0]["result"]
    assert json.loads(path.read_text())["checks"][0]["status"] == "failed"


def test_every_specialist_receives_the_executor_timing_and_observation_limits(
    harness, specification
):
    run = harness(use_knowledge=False)
    assert run.workflow.run(specification)["status"] == "passed"
    seen = set()
    for request in run.requests:
        seen.add(request["instructions"])
        user = next(message for message in request["input"] if message.get("role") == "user")
        content = user["content"]
        text = content if isinstance(content, str) else "".join(part["text"] for part in content)
        configuration = json.loads(
            text.split("Declared hardware configuration (not a behavioral specification):\n")[1]
        )
        profile = configuration["execution_profile"]
        assert profile["format"] == "directed-execution-v2"
        assert profile["clock_period_ns"] == 10
        assert profile["sample_after_rising_edge_ns"] == 1
        assert "explicitly configured read-only internal probes" in profile["observation"]
        assert profile["pre_edge_checks"] is True
        assert profile["sample_before_rising_edge_ns"] == 1
        assert profile["internal_signal_checks"] is False
        assert profile["timing_basis"] == "testbench scheduling, not a DUT timing requirement"
    assert seen == {
        instructions.ANALYZE,
        instructions.PLAN,
        instructions.REVIEW,
        instructions.BUILD_TESTBENCH,
    }


def test_testbench_uses_remaining_planning_budget_not_a_fresh_allocation(harness, specification):
    run = harness(max_model_calls=16)
    with pytest.raises(BudgetExceeded):
        run.workflow.run(specification)
    assert len(run.requests) == 16
    assert run.artifacts.exists("result.json")  # planning completed
    assert not run.artifacts.exists("pipeline-result.json")
    assert not run.artifacts.exists("binding.000.json")


def test_internal_probe_and_pre_edge_check_survive_agent_proposal_binding(harness, specification):
    import jsonschema

    target = HardwareTarget.model_validate(
        {
            "format": "hardware-target-v2",
            "top_module": "interrupt_ctrl",
            "parameters": {},
            "clock": "clk",
            "ports": [
                {"name": "clk", "direction": "input", "width": 1},
                {"name": "rst", "direction": "input", "width": 1},
                {"name": "pending", "direction": "output", "width": 4},
            ],
            "probes": [{"name": "reset_state", "path": "state", "width": 4}],
        }
    )
    rtl = RTL.replace(
        "endmodule",
        """reg [3:0] state = 9;
always @(posedge clk) if (rst) state <= 0;
endmodule""",
    )
    specification = specification.model_copy(
        update={
            "blocks": [
                specification.blocks[0].model_copy(
                    update={
                        "text": (
                            "System reset clears pending interrupts and internal state. "
                            "Before reset, state is 9."
                        )
                    }
                )
            ]
        }
    )

    def proposal(value):
        value["steps"][0]["checks"].extend(
            [
                {
                    "signal": "reset_state",
                    "value": 9,
                    "phase": "pre_edge",
                    "expected_result_index": 0,
                    "source_ids": ["P00001"],
                },
                {
                    "signal": "reset_state",
                    "value": 0,
                    "phase": "post_edge",
                    "expected_result_index": 0,
                    "source_ids": ["P00001"],
                },
            ]
        )

    run = harness(target_output=target, rtl=rtl, change=proposal)
    result = run.workflow.run(specification)
    assert result["status"] == "passed"
    binding = run.artifacts.read("binding.000.json")
    assert binding["probes"] == [p.model_dump() for p in target.probes]
    assert result["cases"][0]["checks_observed"] == 3
    for request in run.requests:
        user = next(m for m in request["input"] if m.get("role") == "user")
        content = user["content"]
        text = content if isinstance(content, str) else "".join(p["text"] for p in content)
        configuration = json.loads(
            text.split("Declared hardware configuration (not a behavioral specification):\n")[1]
        )
        profile = configuration["execution_profile"]
        assert profile["internal_signal_checks"] is True
        assert profile["internal_probes"] == binding["probes"]
    request = next(
        r
        for r in run.requests
        if r["instructions"] == instructions.BUILD_TESTBENCH and "format" in r.get("text", {})
    )
    jsonschema.validate(
        run.artifacts.read("testbench.000.json"), request["text"]["format"]["schema"]
    )
    assert run.workflow.run(specification) == result
    assert len(run.requests) == 17


def test_planning_findings_block_testbench_and_simulation(harness, specification):
    review = ScopedPlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "target": "specification",
                    "kind": "ambiguity",
                    "recommended_action": "Resolve the common clock/reset definition.",
                    "scope": {
                        "kind": "global",
                        "rationale": "Every case depends on this setup.",
                        "evidence": [],
                    },
                    "description": "Reset polarity needs a design decision",
                }
            ]
        }
    )
    run = harness(review=review)
    result = run.workflow.run(specification)
    assert result["status"] == "blocked" and result["cases"] == []
    assert not run.artifacts.exists("testbench.000.task.json")


@pytest.mark.parametrize(
    "rtl,status", [(RTL, "partial"), (RTL.replace("pending <= 0", "pending <= 1"), "failed")]
)
def test_item_finding_blocks_only_its_scenario(
    harness, specification, verification_plan, rtl, status
):
    first = verification_plan.items[0]
    second = first.model_copy(update={"id": "VPLAN-NEEDS-INTERNAL-SIGNAL"})
    plan = verification_plan.model_copy(update={"items": [first, second]})
    review = ScopedPlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "target": "plan",
                    "kind": "execution_binding",
                    "recommended_action": "Supply an internal probe for this scenario.",
                    "scope": {
                        "kind": "items",
                        "item_ids": [second.id],
                        "rationale": "Only this scenario needs the probe.",
                        "evidence": [
                            {"source_id": "P00001", "quote": specification.blocks[0].text}
                        ],
                    },
                    "description": "This scenario needs unsupported internal observation",
                }
            ]
        }
    )
    run = harness(plan_output=plan, review=review, rtl=rtl)
    result = run.workflow.run(specification)
    assert result["status"] == status
    assert [case["plan_item_id"] for case in result["cases"]] == [first.id]
    assert result["cases"][0]["status"] == ("passed" if status == "partial" else "check_failed")
    assert result["blocked_item_ids"] == [second.id]
    assert result["unexecuted_item_ids"] == [second.id]
    assert run.artifacts.read("result.json")["status"] == "needs_review"
    assert not run.artifacts.exists("testbench.001.task.json")
    assert run.workflow.run(specification) == result
    assert len(run.requests) == 17


@pytest.mark.parametrize(
    "scope_kind,rtl,expected",
    [
        ("requirements", RTL, "partial"),
        ("requirements", RTL.replace("pending <= 0", "pending <= 1"), "failed"),
        ("global", RTL, "blocked"),
        ("unknown", RTL, "blocked"),
    ],
)
def test_requirement_scoped_review_through_sdk_and_simulator(
    harness, specification, analysis, verification_plan, scope_kind, rtl, expected
):
    import jsonschema

    # Reset asserted is independently testable; release recovery needs an owner decision.
    source = specification.blocks[0].model_copy(
        update={"id": "RELEASE-SOURCE", "text": "Reset release recovery time is unspecified."}
    )
    specification = specification.model_copy(update={"blocks": [*specification.blocks, source]})
    requirement = analysis.requirements[0].model_copy(
        update={
            "id": "RELEASE",
            "statement": source.text,
            "source_ids": [source.id],
        }
    )
    analysis = analysis.model_copy(update={"requirements": [*analysis.requirements, requirement]})
    first = verification_plan.items[0]
    second = first.model_copy(
        update={
            "id": "release",
            "requirement_ids": [requirement.id],
            "objective": "Check recovery after reset release",
            "preconditions": ["Reset asserted"],
            "stimulus": ["Deassert reset"],
            "expected_results": ["Observe reset release recovery"],
        }
    )
    plan = verification_plan.model_copy(update={"items": [first, second]})
    review = ScopedPlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "target": "specification",
                    "kind": "timing",
                    "description": "Recovery interval is unspecified.",
                    "recommended_action": "Ask the owner to define reset release recovery.",
                    "scope": {
                        "kind": scope_kind,
                        **(
                            {"requirement_ids": [requirement.id]}
                            if scope_kind == "requirements"
                            else {}
                        ),
                        "rationale": "Synthetic routing control, not a live semantic judgment.",
                        "evidence": [{"source_id": source.id, "quote": source.text}],
                    },
                }
            ]
        }
    )
    run = harness(review=review, plan_output=plan, analysis_output=analysis, rtl=rtl)
    result = run.workflow.run(specification)
    assert result["status"] == expected
    assert run.artifacts.read("review.r000.json")["schema_version"] == "2.0"
    assert run.artifacts.read("readiness.json")["format"] == "execution-readiness-v2"
    reviewer_request = next(
        r
        for r in run.requests
        if r["instructions"] == instructions.REVIEW and "format" in r.get("text", {})
    )
    jsonschema.validate(review.model_dump(), reviewer_request["text"]["format"]["schema"])
    if scope_kind == "requirements":
        assert [c["plan_item_id"] for c in result["cases"]] == [first.id]
        assert result["cases"][0]["checks_observed"] == 1
        assert result["blocked_item_ids"] == [second.id]
        assert result["cases"][0]["status"] == (
            "passed" if expected == "partial" else "check_failed"
        )
    else:
        assert result["cases"] == []
        assert result["blocked_item_ids"] == [first.id, second.id]
        assert run.artifacts.read("readiness.json")["issues"][0]["scope_basis"] == scope_kind
    calls = len(run.requests)
    assert run.workflow.run(specification) == result
    assert len(run.requests) == calls  # No repeat model calls when resuming completed work.
    assert not run.artifacts.exists("testbench.001.task.json")


def test_one_testbench_request_for_input_does_not_stop_the_next_scenario(
    harness, specification, verification_plan
):
    first = verification_plan.items[0]
    second = first.model_copy(update={"id": "SECOND"})
    plan = verification_plan.model_copy(update={"items": [first, second]})
    run = harness(
        plan_output=plan,
        proposal_outputs={
            first.id: {
                "status": "needs_input",
                "initial_inputs": [],
                "steps": [],
                "open_questions": ["Internal probe unsupported"],
            },
            second.id: {"plan_item_id": second.id},
        },
    )
    result = run.workflow.run(specification)
    assert result["status"] == "partial"
    assert [case["status"] for case in result["cases"]] == ["needs_input", "passed"]
    assert result["blocked_item_ids"] == [first.id]
    assert result["unexecuted_item_ids"] == [first.id]
    assert not run.artifacts.exists("binding.000.json")
    assert run.artifacts.exists("binding.001.json")


def gap_note(specification):
    return {
        "gaps": [
            {
                "gap_index": 0,
                "disposition": "note",
                "requirement_ids": [],
                "note_kind": "specified_behavior",
                "rationale": "The source already specifies reset clearing.",
                "evidence": [
                    {"source_id": specification.blocks[0].id, "quote": specification.blocks[0].text}
                ],
            }
        ]
    }


def unknown_observation_review():
    return ScopedPlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "target": "specification",
                    "kind": "ambiguity",
                    "description": "Data settling is unspecified; reset flags are independent.",
                    "recommended_action": "Identify checks that require settled data.",
                    "scope": {
                        "kind": "unknown",
                        "rationale": "The reviewer did not establish all affected setups.",
                        "evidence": [],
                    },
                }
            ]
        }
    )


def experimental_proposal(specification, issue_ids):
    return {
        "format": "testbench-proposal-v3",
        "judgment_state": "agent_proposed",
        "issue_assessments": [
            {
                "issue_id": identifier,
                "disposition": "independent",
                "rationale": "Only reset is driven and pending is checked; no data setup/read.",
                "evidence": [
                    {"source_id": specification.blocks[0].id, "quote": specification.blocks[0].text}
                ],
            }
            for identifier in issue_ids
        ],
    }


def test_experimental_case_can_execute_without_clearing_unknown_review_or_gap(
    harness, specification, analysis
):
    import jsonschema

    run = harness(
        review=unknown_observation_review(),
        analysis_output=analysis.model_copy(update={"gaps": ["Unspecified data settling"]}),
        change=lambda p: p.update(
            experimental_proposal(specification, ["review:0", "analysis_gap:0"])
        ),
    )
    run.workflow.experimental = True
    result = run.workflow.run(specification)
    assert len(result["cases"]) == 1
    assert result["cases"][0]["status"] == "passed"
    assert result["status"] == "partial"
    assert result["execution_mode"] == "experimental"
    assert result["engineering_acceptance"] == "pending"
    assert result["human_approved"] is False
    assert result["blocked_item_ids"] == [result["cases"][0]["plan_item_id"]]
    assert result["unexecuted_item_ids"] == []
    readiness = run.artifacts.read("readiness.json")
    assert all(issue["blocking"] for issue in readiness["issues"])
    assert readiness["items"][0]["status"] == "blocked"
    review_name = run.artifacts.read("result.json")["review_artifact"]
    assert run.artifacts.read(review_name) == unknown_observation_review().model_dump()
    assert not run.artifacts.exists("execution-gaps.task.json")
    requests = [
        r for r in run.requests if r["instructions"] == instructions.BUILD_EXPERIMENTAL_TESTBENCH
    ]
    proposal = run.artifacts.read("testbench.000.json")
    jsonschema.validate(proposal, requests[-1]["text"]["format"]["schema"])
    user_input = json.dumps(requests[0]["input"])
    assert "review_findings" in user_input
    assert "Identify checks that require settled data" in user_input
    count = len(run.requests)
    assert run.workflow.run(specification) == result
    assert len(run.requests) == count


def test_experimental_dependent_case_stays_blocked_while_independent_case_runs(
    harness, specification, verification_plan
):
    first = verification_plan.items[0]
    second = first.model_copy(update={"id": "SECOND"})
    blocked = experimental_proposal(specification, ["review:0"])
    blocked["issue_assessments"][0].update(
        disposition="needs_input", evidence=[], rationale="Setup depends on the unresolved rule."
    )
    blocked.update(
        status="needs_input",
        initial_inputs=[],
        steps=[],
        open_questions=["What guarantees the setup transaction is accepted?"],
    )
    run = harness(
        review=unknown_observation_review(),
        plan_output=verification_plan.model_copy(update={"items": [first, second]}),
        proposal_outputs={
            first.id: blocked,
            second.id: {
                **experimental_proposal(specification, ["review:0"]),
                "plan_item_id": second.id,
            },
        },
    )
    run.workflow.experimental = True
    result = run.workflow.run(specification)
    assert result["status"] == "partial"
    assert [case["status"] for case in result["cases"]] == ["needs_input", "passed"]
    assert result["blocked_item_ids"] == [first.id, second.id]
    assert result["unexecuted_item_ids"] == [first.id]
    assert not run.artifacts.exists("binding.000.json")
    assert run.artifacts.exists("binding.001.json")


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(issue_assessments=[]),
        lambda p: p["issue_assessments"].append(p["issue_assessments"][0]),
        lambda p: p["issue_assessments"][0].update(issue_id="review:invented"),
        lambda p: p["issue_assessments"][0].update(evidence=[]),
        lambda p: p["issue_assessments"][0].update(disposition="needs_input"),
        lambda p: p["issue_assessments"][0]["evidence"][0].update(quote="Invented rule"),
        lambda p: p["issue_assessments"][0]["evidence"][0].update(source_id="invented"),
    ],
)
def test_experimental_missing_or_invalid_issue_answers_cannot_execute(
    harness, specification, change
):
    def proposal(value):
        value.update(experimental_proposal(specification, ["review:0"]))
        change(value)

    run = harness(review=unknown_observation_review(), change=proposal)
    run.workflow.experimental = True
    with pytest.raises((ValueError, ModelResponseError)):
        run.workflow.run(specification)
    assert not run.artifacts.exists("testbench.000.json")
    assert not run.artifacts.exists("binding.000.json")
    assert not list(run.artifacts.root.glob("simulation-000-*"))


@pytest.mark.parametrize("same_block", [False, True])
def test_experimental_independence_requires_quotations_actually_read(
    harness, specification, same_block
):
    other = specification.blocks[0].model_copy(
        update={"id": "UNREAD", "text": "A source sentence beyond the read window."}
    )
    if same_block:
        other = other.model_copy(update={"id": specification.blocks[0].id})
        specification = specification.model_copy(
            update={
                "blocks": [
                    specification.blocks[0].model_copy(
                        update={
                            "text": specification.blocks[0].text + " padding" * 700 + other.text
                        }
                    )
                ]
            }
        )
    else:
        specification = specification.model_copy(update={"blocks": [*specification.blocks, other]})
    output = experimental_proposal(specification, ["review:0"])
    output["issue_assessments"][0]["evidence"] = [{"source_id": other.id, "quote": other.text}]
    run = harness(review=unknown_observation_review(), change=lambda p: p.update(output))
    run.workflow.experimental = True
    with pytest.raises(ModelResponseError, match="actually read"):
        run.workflow.run(specification)
    assert not run.artifacts.exists("binding.000.json")


def test_experimental_mode_cannot_be_changed_on_resume(harness, specification):
    run = harness(review=unknown_observation_review())
    assert run.workflow.run(specification)["status"] == "blocked"
    calls = len(run.requests)
    run.workflow.experimental = True
    with pytest.raises(FileExistsError, match="pipeline-execution"):
        run.workflow.run(specification)
    assert len(run.requests) == calls


def test_same_experimental_checks_pass_control_and_detect_fault(harness, specification):
    runs = []
    for rtl in (RTL, RTL.replace("pending <= 0", "pending <= 1")):
        run = harness(
            review=unknown_observation_review(),
            change=lambda p: p.update(experimental_proposal(specification, ["review:0"])),
            rtl=rtl,
        )
        run.workflow.experimental = True
        runs.append((run, run.workflow.run(specification)))
    assert [result["status"] for _, result in runs] == ["partial", "failed"]
    assert [result["cases"][0]["status"] for _, result in runs] == ["passed", "check_failed"]
    control = runs[0][0].artifacts.root / "testbench-000" / "testbench.sv"
    mutant = runs[1][0].artifacts.root / "testbench-000" / "testbench.sv"
    assert control.read_bytes() == mutant.read_bytes()


def test_gap_assessment_uses_existing_reviewer_source_and_kb_tools_with_same_budget(
    harness, specification, analysis
):
    analysis = analysis.model_copy(update={"gaps": ["Reset clearing is already specified"]})
    run = harness(analysis_output=analysis, gap_output=gap_note(specification))
    result = run.workflow.run(specification)
    assert result["status"] == "passed" and result["human_approved"] is False
    assert result["format"] == "verification-pipeline-result-v2"
    assert run.artifacts.read("result.json")["status"] == "needs_review"
    assert run.artifacts.read("analysis.json")["gaps"] == analysis.gaps
    assert run.artifacts.read("readiness.json")["issues"][0]["blocking"] is False
    assert read_spending(run.artifacts).attempts == 22
    task = run.artifacts.read("execution-gaps.task.json")
    assert task["inputs"]["role"] == "reviewer"
    assert task["inputs"]["stage"] == "execution.gaps"
    source_reads = [
        json.loads(p.read_text()) for p in run.artifacts.root.glob("source-access.*.json")
    ]
    assert any(
        r["task_id"] == task["task_id"] and r["tool"] == "get_source_blocks" for r in source_reads
    )
    assert run.workflow.run(specification) == result
    assert len(run.requests) == 22
    # Readiness is part of the task inputs and cannot silently change on resume.
    run.artifacts.path("readiness.json").write_text("{}")
    with pytest.raises(FileExistsError, match=r"readiness\.json"):
        run.workflow.run(specification)
    assert len(run.requests) == 22


def test_gap_classifier_has_no_fresh_budget(harness, specification, analysis):
    analysis = analysis.model_copy(update={"gaps": ["Reset clearing is already specified"]})
    run = harness(analysis_output=analysis, gap_output=gap_note(specification), max_model_calls=15)
    with pytest.raises(BudgetExceeded):
        run.workflow.run(specification)
    assert read_spending(run.artifacts).attempts == 15
    assert not run.artifacts.exists("execution-gaps.json")
    assert not run.artifacts.exists("testbench.000.task.json")


@pytest.mark.parametrize("same_block", [False, True])
def test_gap_evidence_must_have_been_read_not_merely_exist(
    harness, specification, analysis, same_block
):
    other = specification.blocks[0].model_copy(
        update={"id": "UNREAD", "text": "This sentence was not read by the agent."}
    )
    if same_block:
        other = other.model_copy(update={"id": specification.blocks[0].id})
        specification = specification.model_copy(
            update={
                "blocks": [
                    specification.blocks[0].model_copy(
                        update={
                            "text": specification.blocks[0].text + " padding" * 700 + other.text,
                        }
                    )
                ]
            }
        )
    else:
        specification = specification.model_copy(update={"blocks": [*specification.blocks, other]})
    output = gap_note(specification)
    output["gaps"][0]["evidence"] = [{"source_id": other.id, "quote": other.text}]
    run = harness(
        analysis_output=analysis.model_copy(update={"gaps": ["A scope note"]}), gap_output=output
    )
    with pytest.raises(ModelResponseError, match="actually read"):
        run.workflow.run(specification)
    assert not run.artifacts.exists("testbench.000.task.json")


@pytest.mark.parametrize("experimental", [False, True])
def test_known_global_blocker_avoids_unnecessary_gap_model_calls(
    harness, specification, analysis, experimental
):
    review = ScopedPlanReview.model_validate(
        {
            "findings": [
                {
                    "severity": "warning",
                    "target": "specification",
                    "kind": "ambiguity",
                    "recommended_action": "Resolve the common clock/reset definition.",
                    "scope": {
                        "kind": "global",
                        "rationale": "Every case depends on this setup.",
                        "evidence": [],
                    },
                    "description": "Clock definition is unresolved for every scenario",
                }
            ]
        }
    )
    run = harness(
        analysis_output=analysis.model_copy(update={"gaps": ["A scope note"]}), review=review
    )
    run.workflow.experimental = experimental
    result = run.workflow.run(specification)
    assert result["status"] == "blocked"
    assert len(run.requests) == 11
    assert not run.artifacts.exists("execution-gaps.task.json")
    assert not run.artifacts.exists("testbench.000.task.json")


def test_global_gap_remains_blocked_after_assessment(harness, specification, analysis):
    output = {
        "gaps": [
            {
                "gap_index": 0,
                "disposition": "block_global",
                "requirement_ids": [],
                "note_kind": None,
                "evidence": [],
                "rationale": "The source may omit a requirement.",
            }
        ]
    }
    run = harness(
        analysis_output=analysis.model_copy(update={"gaps": ["Possible omission"]}),
        gap_output=output,
    )
    result = run.workflow.run(specification)
    assert result["status"] == "blocked"
    assert len(run.requests) == 16
    assert not result["cases"]


def test_testbench_can_request_input_without_producing_executable_guess(harness, specification):
    def blocked(value):
        value.update(
            status="needs_input", initial_inputs=[], steps=[], open_questions=["Unknown latency"]
        )

    run = harness(change=blocked)
    result = run.workflow.run(specification)
    assert result["status"] == "blocked"
    assert result["cases"][0]["open_questions"] == ["Unknown latency"]
    assert not run.artifacts.exists("binding.000.json")


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(plan_item_id="fabricated"),
        lambda p: p.update(initial_inputs=[{"signal": "rst", "value": 2}]),
        lambda p: p.update(initial_inputs=[{"signal": "rst", "value": 2**64}]),
        lambda p: p["steps"][0]["checks"][0].update(value=-1),
        lambda p: p.update(
            initial_inputs=[{"signal": "rst", "value": 1}, {"signal": "rst", "value": 0}]
        ),
        lambda p: p["steps"][0]["checks"][0].update(expected_result_index=100),
        lambda p: p["steps"][0]["checks"][0].update(source_ids=["not-read"]),
        lambda p: p["steps"][0]["checks"][0].update(signal="undeclared_probe"),
        lambda p: p["steps"][0]["checks"][0].update(phase="arbitrary_time"),
        lambda p: p.update(rtl_source_ids=["not-read"]),
        lambda p: p["steps"][0]["checks"].clear(),
    ],
)
def test_invalid_model_proposals_never_reach_compilation(harness, specification, change):
    run = harness(change=change)
    with pytest.raises((ValueError, ModelResponseError)):
        run.workflow.run(specification)
    assert not run.artifacts.exists("binding.000.json")
    assert not list(run.artifacts.root.glob("simulation-000-*"))


def test_missing_required_turn_capacity_fails_before_any_model_call(harness, specification):
    run = harness(agent_max_turns=5)
    with pytest.raises(ValueError, match="turn limit"):
        run.workflow.run(specification)
    assert not run.requests


def test_changed_completed_evidence_is_rejected_without_repeating_inference(harness, specification):
    run = harness()
    result = run.workflow.run(specification)
    path = run.artifacts.root / result["cases"][0]["result"]
    path.write_text("{}")
    with pytest.raises(ValueError, match="evidence changed"):
        run.workflow.run(specification)
    assert len(run.requests) == 17


def test_simulator_interruption_reuses_agent_proposal_on_resume(
    harness, specification, monkeypatch
):
    from soc_verifier.workflows import verification

    run = harness()
    real_simulate = verification.simulate_testbench

    def interrupted(bundle, output, **kwargs):
        output.mkdir()
        raise RuntimeError("Interrupted before execution receipt")

    monkeypatch.setattr(verification, "simulate_testbench", interrupted)
    with pytest.raises(RuntimeError, match="Interrupted"):
        run.workflow.run(specification)
    assert run.artifacts.exists("testbench.000.completed.json")
    monkeypatch.setattr(verification, "simulate_testbench", real_simulate)
    result = run.workflow.run(specification)
    assert result["status"] == "passed" and len(run.requests) == 17
    assert "simulation-000-001/" in result["cases"][0]["result"]


@pytest.mark.parametrize("experimental", [False, True])
def test_cli_connects_from_source_without_authored_plan_or_binding(
    harness,
    specification,
    tmp_path,
    monkeypatch,
    experimental,
):
    run = harness(
        use_knowledge=False,
        change=(lambda p: p.update(experimental_proposal(specification, [])))
        if experimental
        else None,
    )
    inputs = ArtifactStore(tmp_path / "cli-inputs")
    inputs.write("source.json", specification)
    inputs.write("hardware.json", run.target)
    monkeypatch.setattr("soc_verifier.cli.Settings", lambda: run.settings)
    # Swap only the HTTP transport. Real AgentRuntime, SDK, tools and simulator stay in use.
    real_client = httpx.Client
    monkeypatch.setattr(
        "soc_verifier.cli.httpx.Client", lambda: real_client(transport=httpx.MockTransport(run.api))
    )
    args = [
        "verify",
        str(inputs.path("source.json")),
        "--hardware",
        str(inputs.path("hardware.json")),
        "--rtl",
        str(run.rtl),
    ]
    if experimental:
        args.append("--experimental")
    runner = CliRunner()
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    saved = next((run.settings.artifact_dir / "runs").iterdir())
    assert (saved / "pipeline-result.json").exists()
    assert len(run.requests) == 9
    resumed = runner.invoke(app, [*args, "--run-id", saved.name])
    assert resumed.exit_code == 0, resumed.output
    assert len(run.requests) == 9
    reported = runner.invoke(app, ["spend", saved.name])
    assert reported.exit_code == 0 and "Run completed: passed" in reported.output
    wrong_resume = runner.invoke(app, ["resume", saved.name])
    assert wrong_resume.exit_code == 1 and "verify" in wrong_resume.output
    if experimental:
        changed_mode = runner.invoke(app, [*args[:-1], "--run-id", saved.name])
        assert changed_mode.exit_code == 1
        assert len(run.requests) == 9


def test_proposal_schema_is_accepted_by_actual_sdk():
    from agents.agent_output import AgentOutputSchema

    schema = AgentOutputSchema(Proposal).json_schema()
    assert schema["additionalProperties"] is False


def test_compile_failure_is_unexecuted_not_a_pass(harness, specification):
    run = harness(rtl="invalid Verilog source")
    result = run.workflow.run(specification)
    assert result["status"] == "failed"
    assert result["unexecuted_item_ids"] == ["VPLAN-RST-001"]
    assert result["cases"][0]["status"] == "compile_failed"


def test_unsupported_plan_methods_remain_explicit(harness, specification, verification_plan):
    plan = verification_plan.model_copy(
        update={"items": [verification_plan.items[0].model_copy(update={"method": "inspection"})]}
    )
    run = harness(plan_output=plan)
    result = run.workflow.run(specification)
    assert result["status"] == "partial"
    assert result["unsupported_item_ids"] == ["VPLAN-RST-001"]
    assert result["unexecuted_item_ids"] == ["VPLAN-RST-001"]
    assert not run.artifacts.exists("testbench.000.task.json")


def test_missing_expected_result_mapping_is_rejected(harness, specification, verification_plan):
    plan = verification_plan.model_copy(
        update={
            "items": [
                verification_plan.items[0].model_copy(
                    update={
                        "expected_results": [
                            "Pending bits are zero",
                            "A second separate planned check",
                        ]
                    }
                )
            ]
        }
    )
    run = harness(plan_output=plan)
    with pytest.raises(ValueError, match="omits a planned expected result"):
        run.workflow.run(specification)
    assert not run.artifacts.exists("binding.000.json")
