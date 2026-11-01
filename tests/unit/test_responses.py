import json
import logging

import httpx
import pytest
from pydantic import SecretStr

from soc_verifier.providers.openrouter import OpenRouterTransport
from soc_verifier.providers.responses import prepare_responses
from soc_verifier.settings import Settings


@pytest.mark.parametrize(
    "changes",
    [
        {"previous_response_id": "remote-state"},
        {"conversation": "remote-state"},
        {"stream": True},
        {"background": True},
        {"tools": [{"type": "web_search"}]},
        {"plugins": [{"id": "web"}]},
        {
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "input_image", "image_url": "https://example.com"}],
                }
            ]
        },
        {"input": [{"type": "function_call_output", "output": [{"type": "image"}]}]},
    ],
)
def test_responses_rejects_remote_state_and_unaccounted_input(changes):
    with pytest.raises(ValueError):
        prepare_responses({"input": [], "tools": [], **changes}, 256)


def test_responses_error_redacts_instruction_tool_text_and_opaque_reasoning(caplog):
    secret = "private-response-secret"

    def api(request):
        data = json.loads(request.content)
        message = " / ".join(
            [
                data["instructions"],
                data["input"][0]["encrypted_content"],
                data["input"][1]["output"],
                secret,
            ]
        )
        return httpx.Response(400, json={"error": {"message": message}})

    settings = Settings(
        _env_file=None,
        openrouter_api_key=SecretStr(secret),
        model="test/model",
        provider="test-endpoint",
        model_api="responses",
    )
    with httpx.Client(transport=httpx.MockTransport(api)) as client, caplog.at_level(logging.ERROR):
        transport = OpenRouterTransport(settings, client)
        with pytest.raises(httpx.HTTPStatusError):
            transport._send(
                httpx.Request(
                    "POST",
                    "https://openrouter.ai/api/v1/responses",
                    json={
                        "instructions": "private-instruction",
                        "input": [
                            {"type": "reasoning", "encrypted_content": "private-reasoning"},
                            {
                                "type": "function_call_output",
                                "call_id": "call-1",
                                "output": "private-tool-text",
                            },
                        ],
                    },
                )
            )
    assert "[REDACTED]" in caplog.text
    assert all(
        value not in caplog.text
        for value in [secret, "private-instruction", "private-reasoning", "private-tool-text"]
    )
