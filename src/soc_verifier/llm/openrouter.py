"""Explicit OpenRouter routing and locally validated structured generation."""

import logging
from time import monotonic
from typing import Any

import httpx
from pydantic import BaseModel

from soc_verifier.settings import Settings

logger = logging.getLogger(__name__)


class ModelResponseError(RuntimeError):
    """The provider did not return a complete usable artifact."""


class OpenRouterLLM:
    def __init__(self, settings: Settings, client: httpx.Client) -> None:
        settings.require_llm()
        self.settings = settings
        self.client = client

    def generate[T: BaseModel](self, *, instruction: str, context: str, schema: type[T]) -> T:
        if len(instruction) + len(context) > self.settings.max_input_characters:
            raise ValueError("Input exceeds configured character limit; no request was sent")
        assert self.settings.openrouter_api_key is not None
        started = monotonic()
        response = self.client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.openrouter_api_key.get_secret_value()}",
                "X-OpenRouter-Title": "soc-verifier",
            },
            json={
                "model": self.settings.model,
                "messages": [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": context},
                ],
                "provider": {
                    "only": [self.settings.provider],
                    "allow_fallbacks": False,
                    "require_parameters": True,
                    "data_collection": "deny",
                    "zdr": True,
                },
                "max_tokens": self.settings.max_output_tokens,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "strict": True,
                        "schema": _strict_schema(schema.model_json_schema()),
                    },
                },
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise ModelResponseError("Provider returned an error envelope")
        choices = payload.get("choices", [])
        if not choices or choices[0].get("finish_reason") != "stop":
            raise ModelResponseError("Provider returned no complete generation")
        message = choices[0].get("message", {})
        if message.get("refusal") or not isinstance(message.get("content"), str):
            raise ModelResponseError("Provider refused or returned no text content")
        result = schema.model_validate_json(message["content"])
        # Metadata only: never log credentials, prompts, source text, or completions.
        logger.info(
            "llm_call model=%s provider=%s request_id=%s usage=%s elapsed_seconds=%.3f",
            payload.get("model"),
            payload.get("provider"),
            payload.get("id"),
            payload.get("usage", {}),
            monotonic() - started,
        )
        return result


def _strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Make defaulted fields explicit for endpoints requiring all keys in strict mode."""

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("default", None)
            if value.get("type") == "object":
                value["additionalProperties"] = False
                value["required"] = list(value.get("properties", {}))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)
    return schema
