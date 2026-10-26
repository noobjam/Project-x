import json
import logging
from unittest.mock import Mock

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from soc_verifier.domain.models import PlanReview
from soc_verifier.llm.budget import BudgetExceeded
from soc_verifier.llm.openrouter import ModelResponseError, OpenRouterLLM, _strict_schema
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore


def settings(**overrides):
    return Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("test-secret"),
        model="test/model",
        provider="test-endpoint",
        **overrides,
    )


def test_structured_request_routing_and_redacted_logging(caplog):
    def respond(request):
        payload = json.loads(request.content)
        assert request.headers["authorization"] == "Bearer test-secret"
        assert payload["provider"] == {
            "only": ["test-endpoint"],
            "allow_fallbacks": False,
            "require_parameters": True,
            "data_collection": "deny",
            "zdr": True,
        }
        schema = payload["response_format"]["json_schema"]
        assert schema["strict"] is True
        assert "schema_version" in schema["schema"]["required"]
        version = schema["schema"]["properties"]["schema_version"]
        assert version["enum"] == ["1.0"]
        assert "const" not in version
        return httpx.Response(
            200,
            json={
                "id": "request-123",
                "model": "test/model",
                "provider": "test-endpoint",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                "choices": [{"finish_reason": "stop", "message": {"content": '{"findings": []}'}}],
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(respond)) as client,
        caplog.at_level(logging.INFO),
    ):
        result = OpenRouterLLM(settings(), client).generate(
            instruction="review", context="proprietary-source-text", schema=PlanReview
        )
    assert result.findings == []
    assert "request-123" in caplog.text
    assert "test-secret" not in caplog.text
    assert "proprietary-source-text" not in caplog.text


@pytest.mark.parametrize(
    "response",
    [
        {"error": {"message": "failure"}},
        {"choices": []},
        {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]},
        {"choices": [{"finish_reason": "stop", "message": {"refusal": "no"}}]},
    ],
)
def test_incomplete_or_refused_responses_fail(response):
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response))
        ) as client,
        pytest.raises(ModelResponseError),
    ):
        OpenRouterLLM(settings(), client).generate(
            instruction="review", context="x", schema=PlanReview
        )


def test_schema_violation_fails_locally():
    response = {
        "choices": [{"finish_reason": "stop", "message": {"content": '{"findings": "wrong"}'}}]
    }
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response))
        ) as client,
        pytest.raises(ValidationError),
    ):
        OpenRouterLLM(settings(), client).generate(
            instruction="review", context="x", schema=PlanReview
        )


def test_rejected_candidate_is_saved_separately_for_diagnosis(tmp_path, monkeypatch):
    response = {
        "id": "paid-candidate",
        "usage": {"cost": 0.01},
        "choices": [{"finish_reason": "stop", "message": {"content": '{"findings": "invalid"}'}}],
    }
    artifacts = ArtifactStore(tmp_path)
    budget = Mock()
    budget.reserve.return_value = 1
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response))
    ) as client:
        llm = OpenRouterLLM(settings(), client, artifacts=artifacts)
        monkeypatch.setattr(llm, "_run_budget", lambda: budget)
        with pytest.raises(ValidationError):
            llm.generate(instruction="review", context="source", schema=PlanReview)
    saved = artifacts.read("model-output.00001.json")
    assert saved["request_id"] == "paid-candidate"
    assert saved["choices"][0]["message"]["content"] == '{"findings": "invalid"}'
    assert not artifacts.exists("review.json")
    budget.settle.assert_called_once_with(1, 0.01)


def test_input_limit_rejects_before_network():
    with httpx.Client() as client, pytest.raises(ValueError, match="character limit"):
        OpenRouterLLM(settings(max_input_characters=1000), client).generate(
            instruction="review", context="x" * 1001, schema=PlanReview
        )


def test_http_error_is_not_retried_implicitly():
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(429)

    with (
        httpx.Client(transport=httpx.MockTransport(respond)) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        OpenRouterLLM(settings(), client).generate(
            instruction="review", context="x", schema=PlanReview
        )
    assert len(calls) == 1


def test_http_error_records_reason_without_sensitive_payloads(tmp_path, caplog):
    response = httpx.Response(
        402,
        headers={"Retry-After": "10"},
        json={
            "error": {
                "code": 402,
                "message": "Insufficient credits test-secret private-source",
                "metadata": {
                    "reason": "weight_exceeds_budget",
                    "limit_source": "openrouter_credits",
                    "raw": "private-upstream-payload",
                },
            }
        },
    )
    artifacts = ArtifactStore(tmp_path)
    with httpx.Client() as client, caplog.at_level(logging.ERROR):
        llm = OpenRouterLLM(settings(), client, artifacts=artifacts)
        llm._record_http_error(response, 1, "review", "private-source")
    saved = artifacts.read("http-error.00001.json")
    assert saved["message"] == "Insufficient credits [REDACTED] [REDACTED]"
    assert saved["metadata"]["limit_source"] == "openrouter_credits"
    assert saved["retry-after"] == "10"
    for sensitive in ("test-secret", "private-source", "private-upstream-payload"):
        assert sensitive not in caplog.text
        assert sensitive not in json.dumps(saved)


@pytest.mark.parametrize("source", ["openrouter_in_flight_budget", "openrouter_credits", "unknown"])
def test_only_confirmed_inflight_rejection_releases_reservation(tmp_path, monkeypatch, source):
    response = httpx.Response(
        402,
        json={
            "error": {
                "code": 402,
                "message": "Unavailable",
                "metadata": {"limit_source": source, "reason": "in_flight_budget_exhausted"},
            }
        },
    )
    budget = Mock()
    budget.reserve.return_value = 1
    with httpx.Client(transport=httpx.MockTransport(lambda _: response)) as client:
        llm = OpenRouterLLM(settings(), client, artifacts=ArtifactStore(tmp_path))
        monkeypatch.setattr(llm, "_run_budget", lambda: budget)
        with pytest.raises(httpx.HTTPStatusError):
            llm.generate(instruction="review", context="source", schema=PlanReview)
    if source == "openrouter_in_flight_budget":
        budget.settle.assert_called_once_with(1, 0)
    else:
        budget.settle.assert_not_called()


@pytest.mark.parametrize("finish_reason", ["stop", "length"])
def test_invalid_paid_response_still_logs_safe_usage(caplog, finish_reason):
    response = {
        "id": "paid-invalid",
        "model": "test/model",
        "provider": "test-endpoint",
        "usage": {"prompt_tokens": 10, "cost": 0.001, "unexpected": "private-content"},
        "choices": [
            {
                "finish_reason": finish_reason,
                "message": {"content": '{"findings": "private-content"}'},
            }
        ],
    }
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response))
        ) as client,
        caplog.at_level(logging.INFO),
        pytest.raises((ValidationError, ModelResponseError)),
    ):
        OpenRouterLLM(settings(), client).generate(
            instruction="review", context="private-source", schema=PlanReview
        )
    assert "paid-invalid" in caplog.text and "0.001" in caplog.text
    assert "private-content" not in caplog.text
    assert "private-source" not in caplog.text
    assert "test-secret" not in caplog.text


@pytest.mark.parametrize(
    "response",
    [[], None, {"choices": [None]}, {"choices": [{"finish_reason": "stop", "message": None}]}],
)
def test_malformed_envelope_fails_cleanly(response):
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, content=json.dumps(response))
            )
        ) as client,
        pytest.raises(ModelResponseError),
    ):
        OpenRouterLLM(settings(), client).generate(
            instruction="review", context="x", schema=PlanReview
        )


def test_schema_conversion_preserves_property_named_default():
    result = _strict_schema(
        {
            "type": "object",
            "properties": {"default": {"type": "string", "default": "example", "const": "fixed"}},
        }
    )
    assert result["properties"]["default"] == {"type": "string", "enum": ["fixed"]}
    assert result["required"] == ["default"]


def test_output_limit_has_actionable_error():
    response = {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response))
        ) as client,
        pytest.raises(ModelResponseError, match="output token limit"),
    ):
        OpenRouterLLM(settings(), client).generate(
            instruction="review", context="x", schema=PlanReview
        )


@pytest.mark.parametrize("maximum, expected_posts", [(0.1, 0), (0.4, 1)])
def test_budget_stops_before_sending_paid_request(tmp_path, maximum, expected_posts):
    posts = []

    def respond(request):
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "endpoints": [
                            {
                                "tag": "test-endpoint",
                                "context_length": 100,
                                "max_completion_tokens": 1000,
                                "pricing": {"prompt": "0.001", "completion": "0.001"},
                            }
                        ]
                    }
                },
            )
        posts.append(request)
        return httpx.Response(
            200,
            json={
                "usage": {"cost": 0.01},
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"findings": []}'},
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        llm = OpenRouterLLM(
            settings(max_output_tokens=256, max_cost_usd=maximum, max_model_calls=1),
            client,
            artifacts=ArtifactStore(tmp_path),
        )
        if expected_posts:
            llm.generate(instruction="review", context="x", schema=PlanReview)
        with pytest.raises(BudgetExceeded):
            llm.generate(instruction="review", context="x", schema=PlanReview)
    assert len(posts) == expected_posts


@pytest.mark.parametrize("price_changed", [False, True])
def test_lower_output_limit_preserves_budget_and_checks_prices(tmp_path, price_changed):
    posts = []
    prompt_price = "0.001"

    def respond(request):
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "endpoints": [
                            {
                                "tag": "test-endpoint",
                                "context_length": 100,
                                "max_completion_tokens": 1000,
                                "pricing": {"prompt": prompt_price, "completion": "0.001"},
                            }
                        ]
                    }
                },
            )
        posts.append(json.loads(request.content)["max_tokens"])
        return httpx.Response(
            200,
            json={
                "usage": {"cost": 0.01},
                "choices": [{"finish_reason": "stop", "message": {"content": '{"findings": []}'}}],
            },
        )

    artifacts = ArtifactStore(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        original = OpenRouterLLM(settings(max_output_tokens=1000), client, artifacts=artifacts)
        original.generate(instruction="review", context="x", schema=PlanReview)
        pinned = artifacts.read("budget-pricing.json")
        if price_changed:
            prompt_price = "0.002"
        reduced = OpenRouterLLM(settings(max_output_tokens=256), client, artifacts=artifacts)
        if price_changed:
            with pytest.raises(FileExistsError):
                reduced.generate(instruction="review", context="x", schema=PlanReview)
            assert posts == [1000]
        else:
            reduced.generate(instruction="review", context="x", schema=PlanReview)
            assert posts == [1000, 256]
            assert (
                artifacts.read("cost-reserved.00002.json")["reserved_usd"]
                == pinned["reservation_usd"]
            )
        assert artifacts.read("budget-pricing.json") == pinned
