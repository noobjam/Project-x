"""Real Agents SDK tool loops with a synthetic, offline Responses endpoint."""

import json
import logging
from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr

from soc_verifier.agents import instructions
from soc_verifier.agents.base import ModelResponseError, OutputLimitError
from soc_verifier.agents.runtime import AgentRuntime
from soc_verifier.domain.models import VerificationPlan
from soc_verifier.providers.budget import BudgetExceeded, read_spending
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow

pytestmark = pytest.mark.integration


def response(output, **overrides):
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
                "input_tokens_details": {"cached_tokens": 10},
                "output_tokens_details": {"reasoning_tokens": 5},
                "cost": 0.0001,
            },
            **overrides,
        },
    )


def call(name, arguments, identifier="lookup-1"):
    return {
        "type": "function_call",
        "id": f"fc-{identifier}",
        "call_id": identifier,
        "name": name,
        "arguments": json.dumps(arguments),
        "status": "completed",
    }


def final(plan):
    return [
        {
            "type": "message",
            "id": "msg-plan",
            "role": "assistant",
            "status": "completed",
            "content": [{"type": "output_text", "text": plan.model_dump_json(), "annotations": []}],
        }
    ]


def setup_runtime(tmp_path, specification, respond, **overrides):
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
                                "pricing": {"prompt": "0.000001", "completion": "0.000002"},
                            }
                        ]
                    }
                },
            )
        assert request.url.path == "/api/v1/responses"
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["model"] == "openai/gpt-6.1-terra"
        assert payload["provider"] == {
            "only": ["test-endpoint"],
            "allow_fallbacks": False,
            "require_parameters": True,
            "data_collection": "deny",
            "zdr": True,
        }
        assert payload["store"] is False and payload["truncation"] == "disabled"
        assert payload["reasoning"] == {"effort": "medium"}
        assert payload["max_output_tokens"] == 256 and "max_tokens" not in payload
        assert "previous_response_id" not in payload
        assert "parallel_tool_calls" not in payload
        assert "reasoning.encrypted_content" in payload["include"]
        try:
            return respond(payload)
        except AssertionError as error:
            # Let the test report the synthetic protocol assertion through the SDK wrapper.
            raise RuntimeError(str(error)) from error

    settings = Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("test-only"),
        model="openai/gpt-6.1-terra",
        provider="test-endpoint",
        model_api="responses",
        max_output_tokens=256,
        **overrides,
    )
    artifacts = ArtifactStore(tmp_path)
    artifacts.write("specification.json", specification)
    client = httpx.Client(transport=httpx.MockTransport(api))
    return AgentRuntime(settings, client, artifacts=artifacts), client, artifacts, requests


def run(agents):
    return agents.run(
        role="planner",
        instruction=instructions.PLAN,
        context="Plan the reset requirement using source evidence.",
        schema=VerificationPlan,
    )


def test_responses_replays_encrypted_reasoning_and_tool_result(
    tmp_path, specification, verification_plan, caplog
):
    reasoning = {
        "id": "rs-1",
        "type": "reasoning",
        "summary": [],
        "encrypted_content": "opaque-synthetic",
    }
    lookup = call("get_source_blocks", {"ids": ["P00001"]})

    def respond(payload):
        assert {tool["name"] for tool in payload["tools"]} == {
            "search_spec",
            "get_source_blocks",
            "get_requirements",
        }
        schema = payload["text"]["format"]["schema"]
        assert "schema_version" in schema["required"]
        results = [item for item in payload["input"] if item.get("type") == "function_call_output"]
        if not results:
            return response([reasoning, lookup])
        assert (
            next(item for item in payload["input"] if item.get("type") == "reasoning")[
                "encrypted_content"
            ]
            == reasoning["encrypted_content"]
        )
        assert (
            next(item for item in payload["input"] if item.get("type") == "function_call")[
                "call_id"
            ]
            == lookup["call_id"]
        )
        assert results[0]["call_id"] == lookup["call_id"]
        assert json.loads(results[0]["output"])["items"][0]["text"] == specification.blocks[0].text
        return response(final(verification_plan))

    agents, client, artifacts, requests = setup_runtime(tmp_path, specification, respond)
    with client, caplog.at_level(logging.INFO, logger="soc_verifier"):
        assert run(agents) == verification_plan
    assert len(requests) == 2
    spending = read_spending(artifacts)
    assert spending.reported == Decimal("0.0002") and spending.unsettled_calls == 0
    assert "input_tokens" in caplog.text and "reasoning_tokens" in caplog.text
    assert "opaque-synthetic" not in caplog.text and specification.blocks[0].text not in caplog.text
    assert len(list(artifacts.root.glob("call.*.result.json"))) == 2


def test_responses_preserves_multiple_tool_results_in_one_turn(
    tmp_path, specification, verification_plan
):
    def respond(payload):
        results = [item for item in payload["input"] if item.get("type") == "function_call_output"]
        if not results:
            return response(
                [
                    call("search_spec", {"query": "reset"}, "search"),
                    call("get_source_blocks", {"ids": ["P00001"]}, "read"),
                ]
            )
        by_call = {item["call_id"]: json.loads(item["output"]) for item in results}
        assert set(by_call) == {"search", "read"}
        assert by_call["search"]["items"][0]["id"] == "P00001"
        assert by_call["read"]["items"][0]["text"] == specification.blocks[0].text
        return response(final(verification_plan))

    agents, client, artifacts, requests = setup_runtime(tmp_path, specification, respond)
    with client:
        assert run(agents) == verification_plan
    assert len(requests) == 2
    accesses = [artifacts.read(path.name) for path in artifacts.root.glob("source-access.*.json")]
    assert {record["tool"] for record in accesses} == {"search_spec", "get_source_blocks"}
    assert len(accesses) == 2


@pytest.mark.parametrize(
    "mode,error",
    [
        ("limit", OutputLimitError),
        ("refusal", ModelResponseError),
        ("failed", ModelResponseError),
        ("partial", ModelResponseError),
    ],
)
def test_responses_rejects_unusable_output_after_recording_charge(
    tmp_path, specification, verification_plan, mode, error
):
    def respond(_):
        output = final(verification_plan)
        if mode == "limit":
            return response(
                output, status="incomplete", incomplete_details={"reason": "max_output_tokens"}
            )
        if mode == "refusal":
            output[0]["content"] = [{"type": "refusal", "refusal": "synthetic"}]
        if mode == "partial":
            output[0]["status"] = "in_progress"
        return response(output, status="failed" if mode == "failed" else "completed")

    agents, client, artifacts, requests = setup_runtime(tmp_path, specification, respond)
    with client, pytest.raises(error):
        run(agents)
    assert len(requests) == 1
    assert read_spending(artifacts).reported == Decimal("0.0001")
    assert artifacts.read("model-output.00001.json")["api"] == "responses"
    assert not list(artifacts.root.glob("direct.*.completed.json"))


def test_responses_followup_obeys_call_limit(tmp_path, specification):
    agents, client, artifacts, requests = setup_runtime(
        tmp_path,
        specification,
        lambda _: response([call("search_spec", {"query": "reset"})]),
        max_model_calls=1,
    )
    with client, pytest.raises(BudgetExceeded):
        run(agents)
    assert len(requests) == 1 and read_spending(artifacts).attempts == 1


def test_terra_rejects_chat_agent_before_network(tmp_path, specification):
    settings = Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("test-only"),
        model="openai/gpt-6.1-terra",
        provider="test-endpoint",
    )
    with httpx.Client() as client, pytest.raises(ValueError, match=r"require.*responses"):
        AgentRuntime(settings, client, artifacts=ArtifactStore(tmp_path))


def test_planner_reads_knowledge_and_source_outside_inline_slice(
    tmp_path, specification, verification_plan, knowledge_snapshot
):
    detail = specification.blocks[0].model_copy(
        update={
            "id": "P00002",
            "section": "Reset timing",
            "text": "Reset duration is 7 cycles.",
        }
    )
    specification = specification.model_copy(update={"blocks": [*specification.blocks, detail]})
    # This is an adapter/consultation control, not a test of model reasoning quality.
    completed = verification_plan.model_copy(
        update={
            "items": [
                verification_plan.items[0].model_copy(
                    update={"environment_needs": ["Drive reset for 7 cycles (P00002)."]}
                )
            ]
        }
    )
    steps = [
        ("search_knowledge", {"query": "reset"}),
        ("get_knowledge_entries", {"ids": ["K01"]}),
        ("search_spec", {"query": "duration"}),
        ("get_source_blocks", {"ids": ["P00002"]}),
    ]

    def respond(payload):
        outputs = [i for i in payload["input"] if i.get("type") == "function_call_output"]
        count = len(outputs)
        if count < len(steps):
            name, args = steps[count]
            assert payload["tool_choice"] == {"type": "function", "name": name}
            assert "format" not in payload.get("text", {})
            return response([call(name, args, f"step-{count}")])
        assert payload["tool_choice"] == "auto"
        assert payload["text"]["format"]["type"] == "json_schema"
        assert (
            json.loads(outputs[1]["output"])["items"][0]["text"]
            == knowledge_snapshot.entries[0].text
        )
        assert json.loads(outputs[3]["output"])["items"][0]["text"] == detail.text
        return response(final(completed))

    agents, client, artifacts, requests = setup_runtime(
        tmp_path,
        specification,
        respond,
        planner_source_lookup=True,
        agent_max_turns=6,
    )
    artifacts.write("knowledge.json", knowledge_snapshot)
    artifacts.write("reference-answer.json", {"private": "excluded-reference-marker"})
    with client:
        assert run(agents) == completed
    assert len(requests) == 5
    assert detail.text not in json.dumps(requests[0])
    assert "excluded-reference-marker" not in json.dumps(requests)
    source_accesses = [artifacts.read(p.name) for p in artifacts.root.glob("source-access.*.json")]
    assert {r["tool"] for r in source_accesses} == {"search_spec", "get_source_blocks"}
    assert all(r["source_ids"] == ["P00002"] for r in source_accesses)
    assert all(
        r["task_id"] and r["invocation_id"] and r["snapshot_sha256"] for r in source_accesses
    )
    assert detail.text not in json.dumps(source_accesses)
    assert len(list(artifacts.root.glob("knowledge-access.*.json"))) == 2
    assert read_spending(artifacts).reported == Decimal("0.0005")


@pytest.mark.parametrize("mode", ["skip_search", "skip_read", "unrelated_read", "no_matches"])
def test_planner_cannot_bypass_source_consultation(
    tmp_path, specification, verification_plan, mode
):
    other = specification.blocks[0].model_copy(
        update={"id": "P00002", "text": "Unrelated context."}
    )
    specification = specification.model_copy(update={"blocks": [*specification.blocks, other]})

    def respond(payload):
        outputs = [i for i in payload["input"] if i.get("type") == "function_call_output"]
        if not outputs and mode != "skip_search":
            return response(
                [
                    call(
                        "search_spec",
                        {"query": "no-such-signal" if mode == "no_matches" else "interrupt"},
                    )
                ]
            )
        if len(outputs) == 1 and mode == "unrelated_read":
            return response([call("get_source_blocks", {"ids": ["P00002"]}, "unrelated")])
        return response(final(verification_plan))

    agents, client, artifacts, requests = setup_runtime(
        tmp_path, specification, respond, planner_source_lookup=True
    )
    with client:
        if mode == "no_matches":
            assert run(agents) == verification_plan
        else:
            with pytest.raises(ModelResponseError, match="consulting"):
                run(agents)
            assert not list(artifacts.root.glob("direct.*.completed.json"))
    assert read_spending(artifacts).attempts == len(requests)


def test_responses_workflow_all_roles_and_completed_resume(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    outputs = {
        "SpecAnalysis": analysis,
        "VerificationPlan": verification_plan,
        "ScopedPlanReview": clean_review,
    }

    def respond(payload):
        choice = payload.get("tool_choice")
        if isinstance(choice, dict):
            name = choice["name"]
            args = {"query": "reset"} if name == "search_spec" else {"ids": ["P00001"]}
            return response([call(name, args, name)])
        return response(final(outputs[payload["text"]["format"]["schema"]["title"]]))

    agents, client, artifacts, requests = setup_runtime(
        tmp_path,
        specification,
        respond,
        planner_source_lookup=True,
    )
    with client:
        workflow = PlanningWorkflow(agents, artifacts, max_revisions=0)
        assert workflow.run()["status"] == "draft_ready"
        assert workflow.run()["status"] == "draft_ready"
    assert len(requests) == 5
    assert artifacts.read("result.json")["human_approved"] is False
    assert read_spending(artifacts).unsettled_calls == 0


def test_consultation_turn_capacity_checked_before_any_request(
    tmp_path, specification, verification_plan, knowledge_snapshot
):
    agents, client, artifacts, requests = setup_runtime(
        tmp_path,
        specification,
        lambda _: response(final(verification_plan)),
        planner_source_lookup=True,
    )
    artifacts.write("knowledge.json", knowledge_snapshot)
    with client, pytest.raises(ValueError, match="turn limit"):
        run(agents)
    assert not requests and read_spending(artifacts).attempts == 0


def test_workflow_rejects_insufficient_planner_turns_before_extraction(
    tmp_path, specification, knowledge_snapshot
):
    def respond(_):
        raise AssertionError("Extraction must not start with an impossible planner configuration")

    agents, client, artifacts, requests = setup_runtime(
        tmp_path, specification, respond, planner_source_lookup=True
    )
    artifacts.write("knowledge.json", knowledge_snapshot)
    with client, pytest.raises(ValueError, match="turn limit"):
        PlanningWorkflow(agents, artifacts, max_revisions=0).run()
    assert not requests and read_spending(artifacts).attempts == 0
