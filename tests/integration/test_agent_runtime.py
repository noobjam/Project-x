"""Exercise the real Agents SDK and OpenAI client against a simulated OpenRouter API."""

import gzip
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

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


@pytest.mark.parametrize("compressed", [False, True])
def test_all_three_agents_run_through_sdk(
    tmp_path, specification, analysis, verification_plan, clean_review, compressed
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

    def wire_response(payload):
        response = respond(payload)
        if not compressed:
            return response
        return httpx.Response(
            200,
            headers={
                "content-type": "application/json",
                "content-encoding": "gzip",
                "transfer-encoding": "chunked",
            },
            stream=httpx.ByteStream(gzip.compress(response.content)),
        )

    api = API(wire_response)
    agents, client, artifacts = runtime(tmp_path, specification, api)
    with client:
        workflow = PlanningWorkflow(agents, artifacts, max_revisions=0)
        assert workflow.run()["status"] == "draft_ready"
        assert workflow.run()["status"] == "draft_ready"
    assert len(api.requests) == 6
    assert artifacts.read("result.json")["human_approved"] is False
    spending = read_spending(artifacts)
    assert spending.attempts == 6
    assert spending.reported == Decimal("0.0006")
    assert spending.unsettled_calls == 0


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


def test_reasoning_blocks_survive_multiple_tool_turns_without_cross_worker_leaks(
    tmp_path, specification, analysis, caplog
):
    from threading import Barrier

    from soc_verifier.providers.reporting import read_task_report

    barrier = Barrier(2)

    def details(label, turn):
        return [
            {"type": "reasoning.summary", "summary": f"synthetic-{label}-{turn}", "index": 0},
            {
                "type": "reasoning.encrypted",
                "data": f"opaque-{label}-{turn}",
                "id": "r",
                "format": "anthropic-claude-v1",
                "index": 1,
            },
        ]

    def respond(payload):
        label = next(m["content"] for m in payload["messages"] if m["role"] == "user")
        history = [m for m in payload["messages"] if m["role"] == "assistant"]
        for turn, message in enumerate(history):
            assert message["reasoning_details"] == details(label, turn)
            assert message["reasoning"] == f"private-reasoning-{label}-{turn}"
        if len(history) == 2:
            return completion({"content": analysis.model_dump_json()})
        if not history:
            barrier.wait(timeout=5)
        return completion(
            {
                "content": None,
                "reasoning_details": details(label, len(history)),
                "reasoning": f"private-reasoning-{label}-{len(history)}",
                # Both workers deliberately use the same IDs. Within a turn two tools
                # share one signed reasoning sequence, which must remain intact.
                "tool_calls": [
                    {
                        "id": f"call-{len(history)}-{i}",
                        "type": "function",
                        "function": {
                            "name": "get_source_blocks",
                            "arguments": '{"ids":["P00001"]}',
                        },
                    }
                    for i in range(2)
                ],
            },
            "tool_calls",
        )

    api = API(respond)
    agents, client, artifacts = runtime(tmp_path, specification, api)
    with client, ThreadPoolExecutor(max_workers=2) as workers, caplog.at_level(logging.INFO):
        futures = [
            workers.submit(
                agents.run,
                role="analyst",
                instruction=instructions.ANALYZE,
                context=label,
                schema=SpecAnalysis,
            )
            for label in ("left", "right")
        ]
        assert all(f.result() == analysis for f in futures)
    report = read_task_report(artifacts)
    assert len(report["tasks"]) == 2
    assert {r["model_calls"] for r in report["tasks"]} == {3}
    assert {r["invocations"] for r in report["tasks"]} == {1}
    assert {r["reported_usd"] for r in report["tasks"]} == {"0.0003"}
    assert report["reported_usd"] == "0.0006" and report["reserved_usd"] == "0"
    assert "opaque-" not in caplog.text and "private-reasoning-" not in caplog.text
    for path in artifacts.root.glob("cost-reserved.*.json"):
        record = artifacts.read(path.name)
        assert record["format"] == "task-reservation-v1"
        call = artifacts.read(f"call.{record['call_id']}.json")
        assert call["task_id"] == record["task_id"]
        assert call["invocation_id"] == record["invocation_id"]


def test_failed_invocation_resumes_same_task_with_separate_reservations(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    from soc_verifier.providers.reporting import read_task_report

    calls = 0

    def respond(payload):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("synthetic interruption")
        outputs = {
            "SpecAnalysis": analysis,
            "VerificationPlan": verification_plan,
            "PlanReview": clean_review,
        }
        title = payload["response_format"]["json_schema"]["schema"]["title"]
        return completion({"content": outputs[title].model_dump_json()})

    api = API(respond)
    agents, client, artifacts = runtime(tmp_path, specification, api)
    with client:
        workflow = PlanningWorkflow(agents, artifacts, max_revisions=0)
        with pytest.raises(httpx.ReadTimeout):
            workflow.run()
        failed_task = artifacts.read("analysis.task.json")["task_id"]
        workflow.run()
    report = read_task_report(artifacts)
    row = next(r for r in report["tasks"] if r["task_id"] == failed_task)
    assert row["invocations"] == 2 and row["failed_invocations"] == 1
    assert row["model_calls"] == 2 and row["unsettled_calls"] == 1
    assert row["reported_usd"] == "0.0001" and row["status"] == "completed"
    assert report["reported_usd"] == "0.0003"
    assert report["reserved_usd"] == artifacts.read("cost-reserved.00001.json")["reserved_usd"]


def test_explicit_snapshot_ignores_later_analysis_and_plan_revisions(
    tmp_path, specification, analysis, verification_plan, clean_review
):
    from soc_verifier.agents.tasks import (
        ArtifactReference,
        Task,
        TaskInputs,
        fingerprint,
        runtime_versions,
    )
    from soc_verifier.domain.models import PlanReview

    expected = analysis.requirements[0].statement

    def respond(payload):
        tool_messages = [m for m in payload["messages"] if m["role"] == "tool"]
        if not tool_messages:
            return completion(
                {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "snapshot-call",
                            "type": "function",
                            "function": {
                                "name": "get_requirements",
                                "arguments": json.dumps({"ids": [analysis.requirements[0].id]}),
                            },
                        }
                    ],
                },
                "tool_calls",
            )
        assert json.loads(tool_messages[0]["content"])["items"][0]["statement"] == expected
        return completion({"content": clean_review.model_dump_json()})

    agents, client, artifacts = runtime(tmp_path, specification, API(respond))
    artifacts.write("analysis.json", analysis)
    artifacts.write("plan.r000.json", verification_plan)
    task = Task.bind(
        artifacts,
        "snapshot-review.json",
        TaskInputs(
            role="reviewer",
            stage="review",
            assigned_ids=[],
            evidence={
                key: ArtifactReference.capture(artifacts, name)
                for key, name in {
                    "source": "specification.json",
                    "analysis": "analysis.json",
                    "plan": "plan.r000.json",
                }.items()
            },
            input_sha256=fingerprint("review"),
            instruction_sha256=fingerprint(instructions.REVIEW),
            schema_sha256=fingerprint(PlanReview.model_json_schema()),
            versions=runtime_versions(),
            configuration={"configuration": agents.configuration},
        ),
    )
    newer = analysis.model_copy(
        update={
            "requirements": [
                analysis.requirements[0].model_copy(
                    update={"statement": "Changed statement that must not enter the earlier task."}
                )
            ]
        }
    )
    artifacts.write("analysis.r001.json", newer)
    with client:
        result = agents.run(
            role="reviewer",
            instruction=instructions.REVIEW,
            context="review",
            schema=PlanReview,
            task=task.envelope,
        )
    assert result == clean_review


def test_ambiguous_reasoning_history_stops_before_another_paid_request(tmp_path, specification):
    from soc_verifier.providers.reporting import read_task_report

    def respond(_):
        response = source_lookup().json()
        response["choices"][0]["message"]["reasoning_details"] = [
            {"type": "reasoning.encrypted", "data": "synthetic-opaque"}
        ]
        return httpx.Response(200, json=response)

    api = API(respond)
    agents, client, artifacts = runtime(tmp_path, specification, api)
    with client, pytest.raises(ModelResponseError, match="preserve provider reasoning"):
        agents.run(
            role="analyst",
            instruction=instructions.ANALYZE,
            context="Inspect reset",
            schema=SpecAnalysis,
        )
    # The simulated provider reuses a tool ID across turns. The SDK collapses
    # that history; forwarding either signed block would guess its association.
    assert len(api.requests) == 2
    report = read_task_report(artifacts)
    assert report["tasks"][0]["failed_invocations"] == 1
    assert report["tasks"][0]["model_calls"] == 2
    assert report["reported_usd"] == "0.0002"


def knowledge_lookup(name, arguments):
    return completion(
        {
            "content": None,
            "tool_calls": [
                {
                    "id": name,
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)},
                }
            ],
        },
        "tool_calls",
    )


@pytest.mark.parametrize("source_accounting", [False, True])
def test_all_specialists_retrieve_frozen_knowledge_with_audited_sdk_tools(
    tmp_path,
    specification,
    analysis,
    verification_plan,
    clean_review,
    knowledge_snapshot,
    accounting_draft,
    source_accounting,
):
    from soc_verifier.agents.knowledge import read_knowledge_accesses
    from soc_verifier.agents.tasks import ArtifactReference

    outputs = {
        "SpecAnalysis": analysis,
        "AccountingDraft": accounting_draft,
        "VerificationPlan": verification_plan,
        "PlanReview": clean_review,
    }

    def respond(payload):
        names = {tool["function"]["name"] for tool in payload["tools"]}
        assert {"search_knowledge", "get_knowledge_entries"} <= names
        reader = next(
            t["function"]
            for t in payload["tools"]
            if t["function"]["name"] == "get_knowledge_entries"
        )
        assert reader["parameters"]["properties"]["ids"]["maxItems"] == 4
        messages = [m for m in payload["messages"] if m["role"] == "tool"]
        if not messages:
            assert "response_format" not in payload
            assert payload["tool_choice"] == {
                "type": "function",
                "function": {"name": "search_knowledge"},
            }
            return knowledge_lookup("search_knowledge", {"query": "reset"})
        if len(messages) == 1:
            assert "response_format" not in payload
            assert payload["tool_choice"] == {
                "type": "function",
                "function": {"name": "get_knowledge_entries"},
            }
            assert json.loads(messages[0]["content"])["items"][0]["status"] == "proposed"
            return knowledge_lookup("get_knowledge_entries", {"ids": ["K01"]})
        assert payload["tool_choice"] == "auto"
        assert json.loads(messages[-1]["content"])["items"][0]["text"] == (
            knowledge_snapshot.entries[0].text
        )
        name = payload["response_format"]["json_schema"]["schema"]["title"]
        return completion({"content": outputs[name].model_dump_json()})

    api = API(respond)
    agents, client, artifacts = runtime(
        tmp_path, specification, api, source_accounting=source_accounting
    )
    artifacts.write("knowledge.json", knowledge_snapshot)
    reference = ArtifactReference.capture(artifacts, "knowledge.json")
    with client:
        workflow = PlanningWorkflow(
            agents, artifacts, max_revisions=0, source_accounting=source_accounting
        )
        assert workflow.run()["status"] == "draft_ready"
        assert workflow.run()["status"] == "draft_ready"
        assert len(api.requests) == 9
        if source_accounting:
            report = artifacts.read("source-accounting.r000.json")
            assert report["semantic_acceptance"] == "unreviewed"
            assert report["unaccounted"] == []
            assert "Conditions:" in artifacts.read("analysis.json")["requirements"][0]["statement"]
        accesses = read_knowledge_accesses(artifacts)
        assert len(accesses) == 6
        assert {a["role"] for a in accesses} == {"analyst", "planner", "reviewer"}
        assert {a["tool"] for a in accesses} == {"search_knowledge", "get_knowledge_entries"}
        assert {a["snapshot_sha256"] for a in accesses} == {reference.sha256}
        for access in accesses:
            assert access["entry_ids"] == ["K01"]
            assert access["entry_hashes"] == {"K01": knowledge_snapshot.entries[0].sha256}
            assert access["task_id"] and access["invocation_id"]
        for path in artifacts.root.glob("*.task.json"):
            assert (
                artifacts.read(path.name)["inputs"]["evidence"]["knowledge"]
                == reference.model_dump()
            )
        # Editing or deleting the frozen snapshot cannot silently reuse completed work.
        artifacts.path("knowledge.json").write_text("{}")
        with pytest.raises(ValueError, match="inputs or versions changed"):
            workflow.run()
        assert len(api.requests) == 9
    assert read_spending(artifacts).reported == Decimal("0.0009")
    assert read_spending(artifacts).unsettled_calls == 0


@pytest.mark.parametrize("mode", ["skip", "search_only", "no_matches"])
def test_knowledge_cannot_be_silently_ignored(
    tmp_path, specification, analysis, knowledge_snapshot, mode
):
    def respond(payload):
        if mode != "skip" and not any(m["role"] == "tool" for m in payload["messages"]):
            query = "reset" if mode == "search_only" else "unmatched-topic"
            return knowledge_lookup("search_knowledge", {"query": query})
        if mode == "no_matches":
            assert payload["tool_choice"] == "auto"
        return completion({"content": analysis.model_dump_json()})

    api = API(respond)
    agents, client, artifacts = runtime(tmp_path, specification, api)
    artifacts.write("knowledge.json", knowledge_snapshot)
    with client:
        if mode == "no_matches":
            assert (
                agents.run(
                    role="analyst",
                    instruction=instructions.ANALYZE,
                    context="reset",
                    schema=SpecAnalysis,
                )
                == analysis
            )
        else:
            with pytest.raises(ModelResponseError, match="without consulting"):
                agents.run(
                    role="analyst",
                    instruction=instructions.ANALYZE,
                    context="reset",
                    schema=SpecAnalysis,
                )
    assert len(api.requests) == (1 if mode == "skip" else 2)
    assert read_spending(artifacts).unsettled_calls == 0
