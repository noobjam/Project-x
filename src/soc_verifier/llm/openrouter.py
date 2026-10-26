"""Explicit OpenRouter routing and locally validated structured generation."""

import json
import logging
import re
from decimal import Decimal
from threading import Lock
from time import monotonic
from typing import Any

import httpx
from pydantic import BaseModel

from soc_verifier.llm.base import ModelResponseError, OutputLimitError
from soc_verifier.llm.budget import CallBudget
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore

logger = logging.getLogger(__name__)


class OpenRouterLLM:
    def __init__(
        self, settings: Settings, client: httpx.Client, *, artifacts: ArtifactStore | None = None
    ) -> None:
        settings.require_llm()
        self.settings = settings
        self.client = client
        self.artifacts = artifacts
        self.budget: CallBudget | None = None
        self.budget_lock = Lock()

    def _run_budget(self) -> CallBudget | None:
        if self.artifacts is None:
            return None
        with self.budget_lock:
            if self.budget is None:
                response = self.client.get(
                    f"https://openrouter.ai/api/v1/models/{self.settings.model}/endpoints",
                    timeout=30,
                )
                response.raise_for_status()
                endpoints = response.json()["data"]["endpoints"]
                endpoint = next(
                    (item for item in endpoints if item["tag"] == self.settings.provider), None
                )
                if endpoint is None:
                    raise ValueError("Pinned provider endpoint not found; no generation was sent")
                pricing = endpoint["pricing"]
                prompt_rate, completion_rate = (
                    Decimal(pricing["prompt"]),
                    Decimal(pricing["completion"]),
                )
                capacity = endpoint["context_length"]
                if not isinstance(capacity, int) or capacity <= 0:
                    raise ValueError(
                        "Provider context capacity is unavailable; cannot reserve cost"
                    )
                if any(not rate.is_finite() or rate < 0 for rate in (prompt_rate, completion_rate)):
                    raise ValueError("Provider pricing is invalid; cannot reserve cost")
                maximum = endpoint.get("max_completion_tokens")
                if maximum is not None and self.settings.max_output_tokens > maximum:
                    raise ValueError("Configured output tokens exceed the provider limit")
                reservation = (
                    capacity * prompt_rate + self.settings.max_output_tokens * completion_rate
                )
                if self.artifacts.exists("budget-pricing.json"):
                    pinned = self.artifacts.read("budget-pricing.json")
                    pinned_reservation = Decimal(pinned["reservation_usd"])
                    if reservation > pinned_reservation:
                        raise ValueError("Request exceeds the pinned cost bound; start a new run")
                    # A lower output ceiling keeps the original conservative bound.
                    # Price/model/context changes still fail the immutable write below.
                    reservation = pinned_reservation
                # Pin the pricing bound. Changed pricing on resume requires a new run.
                self.artifacts.write(
                    "budget-pricing.json",
                    {
                        "model": self.settings.model,
                        "provider": self.settings.provider,
                        "prompt_rate": str(prompt_rate),
                        "completion_rate": str(completion_rate),
                        "context_capacity": capacity,
                        "reservation_usd": str(reservation),
                    },
                )
                self.budget = CallBudget(
                    self.artifacts,
                    max_cost=Decimal(str(self.settings.max_cost_usd)),
                    max_calls=self.settings.max_model_calls,
                    reservation=reservation,
                )
            return self.budget

    def generate[T: BaseModel](self, *, instruction: str, context: str, schema: type[T]) -> T:
        if len(instruction) + len(context) > self.settings.max_input_characters:
            raise ValueError("Input exceeds configured character limit; no request was sent")
        assert self.settings.openrouter_api_key is not None
        budget = self._run_budget()
        attempt = budget.reserve() if budget is not None else None
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
        if response.is_error:
            details = self._record_http_error(response, attempt, instruction, context)
            metadata = details.get("metadata", {})
            if (
                response.status_code == 402
                and metadata.get("limit_source") == "openrouter_in_flight_budget"
                and metadata.get("reason") == "in_flight_budget_exhausted"
                and budget is not None
                and attempt is not None
            ):
                # This specific admission rejection occurs before provider inference.
                # Other HTTP/transport failures retain their uncertain reservation.
                budget.settle(attempt, 0)
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError:
            raise ModelResponseError("Provider returned invalid JSON") from None
        if not isinstance(payload, dict):
            raise ModelResponseError("Provider returned an invalid response envelope")
        # Record billed work before validating the completion. Never log response text.
        usage = payload.get("usage")
        if budget is not None and attempt is not None:
            budget.settle(attempt, usage.get("cost") if isinstance(usage, dict) else None)
        safe_usage = (
            {
                key: value
                for key, value in usage.items()
                if key in {"prompt_tokens", "completion_tokens", "total_tokens", "cost"}
                and isinstance(value, (int, float))
            }
            if isinstance(usage, dict)
            else {}
        )
        logger.info(
            "llm_call model=%s provider=%s request_id=%s usage=%s elapsed_seconds=%.3f",
            payload.get("model"),
            payload.get("provider"),
            payload.get("id"),
            safe_usage,
            monotonic() - started,
        )
        if self.artifacts is not None and attempt is not None:
            # Keep rejected candidates and finish metadata as well as valid ones.
            # These diagnostics are never loaded as accepted domain artifacts.
            self.artifacts.write(
                f"model-output.{attempt:05d}.json",
                {
                    "request_id": payload.get("id"),
                    "schema": schema.__name__,
                    "max_output_tokens": self.settings.max_output_tokens,
                    "choices": payload.get("choices"),
                },
            )
        if "error" in payload:
            self._record_http_error(response, attempt, instruction, context)
            raise ModelResponseError("Provider returned an error envelope")
        choices = payload.get("choices", [])
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ModelResponseError("Provider returned no complete generation")
        if choices[0].get("finish_reason") == "length":
            raise OutputLimitError(
                "Provider reached the output token limit; generation is incomplete"
            )
        if choices[0].get("finish_reason") != "stop":
            self._record_http_error(response, attempt, instruction, context)
            raise ModelResponseError("Provider returned no complete generation")
        message = choices[0].get("message", {})
        if (
            not isinstance(message, dict)
            or message.get("refusal")
            or not isinstance(message.get("content"), str)
        ):
            raise ModelResponseError("Provider refused or returned no text content")
        return schema.model_validate_json(message["content"])

    def _record_http_error(
        self, response: httpx.Response, attempt: int | None, instruction: str, context: str
    ) -> dict[str, Any]:
        """Retain actionable API errors, excluding raw upstream payloads and credentials."""
        details: dict[str, Any] = {"status": response.status_code, "attempt": attempt}
        try:
            payload = response.json()
        except ValueError:
            payload = None
        error = payload.get("error") if isinstance(payload, dict) else None
        choices = payload.get("choices") if isinstance(payload, dict) else None
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            details["finish_reason"] = choices[0].get("finish_reason")
            error = error or choices[0].get("error")
        if isinstance(error, dict):
            for key in ("code", "message"):
                if isinstance(error.get(key), (str, int)):
                    details[key] = error[key]
            metadata = error.get("metadata")
            if isinstance(metadata, dict):
                details["metadata"] = {
                    key: value
                    for key, value in metadata.items()
                    if key in {"reason", "limit_source", "remedy_hint", "provider_code"}
                    and isinstance(value, (str, int))
                }
        for header in ("retry-after", "x-request-id"):
            if header in response.headers:
                details[header] = response.headers[header]
        assert self.settings.openrouter_api_key is not None
        sensitive = (self.settings.openrouter_api_key.get_secret_value(), instruction, context)

        def redact(value: Any) -> Any:
            if isinstance(value, str):
                for text in sensitive:
                    if text:
                        value = value.replace(text, "[REDACTED]")
                return re.sub(r"sk-or-[A-Za-z0-9_-]+", "[REDACTED]", value)
            if isinstance(value, dict):
                return {key: redact(item) for key, item in value.items()}
            return value

        details = redact(details)
        if self.artifacts is not None and attempt is not None:
            self.artifacts.write(f"http-error.{attempt:05d}.json", details)
        logger.error("llm_http_error %s", json.dumps(details, ensure_ascii=True))
        return details


def _strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Normalize schema keywords, preserving property names and literal values."""

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("default", None)
            if "const" in value:
                value["enum"] = [value.pop("const")]
            if value.get("type") == "object":
                value["additionalProperties"] = False
                value["required"] = list(value.get("properties", {}))
            for key, child in value.items():
                # These dictionaries map arbitrary user names to schemas; their keys
                # are not schema keywords (a property can itself be named 'default').
                if key in {"properties", "$defs", "definitions", "patternProperties"}:
                    for definition in child.values():
                        visit(definition)
                elif key not in {"enum", "examples"}:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)
    return schema
