"""Exercise the real Agents SDK and OpenAI client against a simulated OpenRouter API."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from pydantic import SecretStr

from soc_verifier.agents import instructions
from soc_verifier.agents.base import ModelResponseError, OutputLimitError
from soc_verifier.agents.runtime import AgentRuntime
from soc_verifier.domain.models import SpecAnalysis
from soc_verifier.providers.budget import BudgetExceeded, read_spending
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow

pytestmark = pytest.mark.integration


def completion(message, finish="stop"):
    return httpx.Response(
        200,
        json={
            "id": "synthetic-request",
            "model": "test/model",
            "object": "chat.completion",
            "created": 1,
            "provider": "test-endpoint",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
                "cost": 0.0001,
                "prompt_tokens_details": {"cached_tokens": 30},
                "completion_tokens_details": {"reasoning_tokens": 5},
            },
            "choices": [
                {"index": 0, "finish_reason": finish, "message": {"role": "assistant", **message}}
            ],
        },
    )


def source_lookup():
    return completion(
        {
            "content": None,
            "tool_calls": [
                {
                    "id": "lookup-1",
                    "type": "function",
                    "function": {
                        "name": "get_source_blocks",
                        "arguments": json.dumps({"ids": ["P00001"]}),
                    },
                }
            ],
        },
        "tool_calls",
    )


class API:
    def __init__(self, respond):
        self.respond = respond
        self.requests = []

    def __call__(self, request):
        assert request.url.host == "openrouter.ai"
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "endpoints": [
                            {
                                "tag": "test-endpoint",
                                "context_length": 1000,
                                "max_completion_tokens": 1000,
                                "pricing": {"prompt": "0.000001", "completion": "0.000002"},
                                "supported_parameters": ["tools", "response_format"],
                            }
                        ]
                    }
                },
            )
        payload = json.loads(request.content)
        self.requests.append(payload)
        assert payload["model"] == "test/model"
        assert payload["provider"]["only"] == ["test-endpoint"]
        assert request.headers["authorization"] == "Bearer test-only"
        return self.respond(payload)


def runtime(tmp_path, specification, api, **overrides):
    artifacts = ArtifactStore(tmp_path)
    artifacts.write("specification.json", specification)
    settings = Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("test-only"),
        model="test/model",
        provider="test-endpoint",
        max_output_tokens=256,
        **overrides,
    )
    client = httpx.Client(transport=httpx.MockTransport(api))
    return AgentRuntime(settings, client, artifacts=artifacts), client, artifacts


def test_sdk_agent_executes_tool_then_uses_result(tmp_path, specification, analysis, caplog):
    def respond(payload):
        assert {tool["function"]["name"] for tool in payload["tools"]} == {
            "search_spec",
            "get_source_blocks",
        }
        tool_messages = [m for m in payload["messages"] if m["role"] == "tool"]
        if not tool_messages:
            return source_lookup()
        evidence = json.loads(tool_messages[0]["content"])
        assert evidence["items"][0]["id"] == "P00001"
        assert "reset" in evidence["items"][0]["text"].lower()
        return completion({"content": analysis.model_dump_json()})

    api = API(respond)
    agents, client, artifacts = runtime(tmp_path, specification, api)
    with client, caplog.at_level(logging.INFO, logger="soc_verifier"):
        result = agents.run(
            role="analyst",
            instruction=instructions.ANALYZE,
            context="Inspect reset evidence",
            schema=SpecAnalysis,
        )
    assert result == analysis
    assert len(api.requests) == 2
    spending = read_spending(artifacts)
    assert spending.attempts == 2 and spending.unsettled_calls == 0
    assert float(spending.reported) == pytest.approx(0.0002)
    assert "agent_tool name=get_source_blocks" in caplog.text
    assert "cached_tokens" in caplog.text and "reasoning_tokens" in caplog.text
    assert specification.blocks[0].text not in caplog.text
    assert "test-only" not in caplog.text


def test_all_three_agents_run_through_sdk(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    outputs = {
        "SpecAnalysis": analysis,
        "VerificationPlan": verification_plan,
        "PlanReview": clean_review,
    }
    expected_tools = {"SpecAnalysis": 2, "VerificationPlan": 3, "PlanReview": 4}

    def respond(payload):
        name = payload["response_format"]["json_schema"]["schema"]["title"]
        assert len(payload["tools"]) == expected_tools[name]
        calls = {
            "SpecAnalysis": ("search_spec", {"query": "reset"}),
            "VerificationPlan": ("get_requirements", {"ids": [analysis.requirements[0].id]}),
            "PlanReview": ("get_plan_items", {"ids": [verification_plan.items[0].id]}),
        }
        if payload["messages"][-1]["role"] != "tool":
            tool_name, arguments = calls[name]
            return completion(
                {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments),
                            },
                        }
                    ],
                },
                "tool_calls",
            )
        assert json.loads(payload["messages"][-1]["content"])["items"]
        return completion({"content": outputs[name].model_dump_json()})

    api = API(respond)
    agents, client, artifacts = runtime(tmp_path, specification, api)
    with client:
        workflow = PlanningWorkflow(agents, artifacts, max_revisions=0)
        assert workflow.run()["status"] == "draft_ready"
        assert workflow.run()["status"] == "draft_ready"
    assert len(api.requests) == 6
    assert artifacts.read("result.json")["human_approved"] is False


def test_tool_followup_input_limit_is_checked_before_billing(tmp_path, specification):
    block = specification.blocks[0].model_copy(update={"text": "reset " * 500})
    specification = specification.model_copy(update={"blocks": [block]})
    api = API(lambda _: source_lookup())
    agents, client, artifacts = runtime(tmp_path, specification, api, max_input_characters=1000)
    with client, pytest.raises(ValueError, match="character limit"):
        agents.run(
            role="analyst", instruction="Inspect evidence", context="reset", schema=SpecAnalysis
        )
    assert len(api.requests) == 1
    assert read_spending(artifacts).attempts == 1


def test_parallel_agents_share_budget_without_closing_each_others_client(
    tmp_path, specification, analysis
):
    api = API(lambda _: completion({"content": analysis.model_dump_json()}))
    agents, client, artifacts = runtime(tmp_path, specification, api)
    with client, ThreadPoolExecutor(max_workers=2) as workers:
        futures = [
            workers.submit(
                agents.run,
                role="analyst",
                instruction=instructions.ANALYZE,
                context="Inspect reset",
                schema=SpecAnalysis,
            )
            for _ in range(2)
        ]
        assert all(future.result() == analysis for future in futures)
    assert len(api.requests) == 2
    assert read_spending(artifacts).attempts == 2
    assert read_spending(artifacts).unsettled_calls == 0


@pytest.mark.parametrize("limit", ["turns", "calls", "cost"])
def test_tool_loops_are_bounded_and_accounted(tmp_path, specification, limit):
    api = API(lambda _: source_lookup())
    config = {
        "turns": {"agent_max_turns": 2},
        "calls": {"max_model_calls": 2},
        "cost": {"max_cost_usd": 0.00001},
    }[limit]
    agents, client, artifacts = runtime(tmp_path, specification, api, **config)
    error = ModelResponseError if limit == "turns" else BudgetExceeded
    with client, pytest.raises(error):
        PlanningWorkflow(agents, artifacts, max_revisions=0).run()
    assert len(api.requests) == (0 if limit == "cost" else 2)
    assert read_spending(artifacts).attempts == len(api.requests)
    assert not artifacts.exists("analysis.json")


@pytest.mark.parametrize("failure", ["http", "length", "schema", "network"])
def test_sdk_failure_does_not_retry_or_publish(tmp_path, specification, failure):
    def respond(_):
        if failure == "http":
            return httpx.Response(429, json={"error": {"message": "Rate limited"}})
        if failure == "network":
            raise httpx.ReadTimeout("synthetic network failure")
        return completion(
            {"content": '{"requirements": "invalid"}'}, "length" if failure == "length" else "stop"
        )

    api = API(respond)
    agents, client, artifacts = runtime(tmp_path, specification, api)
    expected = {
        "http": httpx.HTTPStatusError,
        "length": OutputLimitError,
        "schema": ModelResponseError,
        "network": httpx.ReadTimeout,
    }[failure]
    with client, pytest.raises(expected):
        PlanningWorkflow(agents, artifacts, max_revisions=0).run()
    assert len(api.requests) == 1
    assert not artifacts.exists("analysis.json")
    assert read_spending(artifacts).unsettled_calls == (1 if failure in {"http", "network"} else 0)
