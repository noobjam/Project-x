import json
import logging

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from soc_verifier.domain.models import PlanReview
from soc_verifier.llm.openrouter import ModelResponseError, OpenRouterLLM
from soc_verifier.settings import Settings


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
