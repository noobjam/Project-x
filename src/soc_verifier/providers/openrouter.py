"""OpenAI SDK transport with per-request accounting, diagnostics and fail-closed limits."""

import asyncio
import json
import logging
import re
from copy import deepcopy
from decimal import Decimal
from threading import Lock
from time import monotonic
from typing import Any

import httpx

from soc_verifier.agents.attempts import current_invocation
from soc_verifier.agents.base import ModelResponseError, OutputLimitError
from soc_verifier.agents.tasks import fingerprint
from soc_verifier.providers.budget import CallBudget
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore

logger = logging.getLogger(__name__)


class OpenRouterTransport(httpx.AsyncBaseTransport):
    def __init__(
        self, settings: Settings, client: httpx.Client, *, artifacts: ArtifactStore | None = None
    ) -> None:
        settings.require_agents()
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
                if pricing.get("overrides"):
                    raise ValueError("Tiered endpoint pricing is not supported by the cost bound")
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

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        # The caller owns the shared synchronous client. The SDK owns only this
        # async bridge; closing one agent's SDK client must not close other workers.
        return await asyncio.to_thread(self._send, request)

    def _send(self, request: httpx.Request) -> httpx.Response:
        invocation = current_invocation.get()
        if invocation is None:
            if self.artifacts is not None and self.artifacts.exists("execution.json"):
                raise ValueError("Model request has no task attribution")
            return self._send_request(request)
        invocation.calls += 1
        call_id = f"{invocation.invocation_id}.{invocation.calls:03d}"
        assert self.artifacts is not None
        self.artifacts.write(
            f"call.{call_id}.json",
            {
                "format": "agent-call-v1",
                **invocation.attribution(),
                "call_id": call_id,
                "turn": invocation.calls,
                "sdk_request_sha256": fingerprint(json.loads(request.content)),
            },
        )
        try:
            response = self._send_request(request)
        except Exception as error:
            self.artifacts.write(
                f"call.{call_id}.result.json",
                {
                    "format": "agent-call-result-v1",
                    "call_id": call_id,
                    "status": "failed",
                    "error_type": type(error).__name__,
                },
            )
            raise
        self.artifacts.write(
            f"call.{call_id}.result.json",
            {
                "format": "agent-call-result-v1",
                "call_id": call_id,
                "status": "returned",
            },
        )
        return response

    def _send_request(self, request: httpx.Request) -> httpx.Response:
        if str(request.url) != "https://openrouter.ai/api/v1/chat/completions":
            raise ValueError("Unexpected model endpoint")
        payload = json.loads(request.content)
        invocation = current_invocation.get()
        if invocation is not None and any(
            entry["reasoning_fields"] for entry in invocation.reasoning_history
        ):
            history = [
                m
                for m in payload.get("messages", [])
                if m.get("role") == "assistant" and m.get("tool_calls")
            ]
            if len(history) != len(invocation.reasoning_history):
                raise ModelResponseError("Tool history cannot preserve provider reasoning")
            for message, original in zip(history, invocation.reasoning_history, strict=True):
                if _tool_identity(message) != original["tool_identity"]:
                    raise ModelResponseError("Tool history changed during reasoning replay")
                message.update(deepcopy(original["reasoning_fields"]))
        context = json.dumps(payload.get("messages", []))
        instruction = ""
        if len(context) > self.settings.max_input_characters:
            raise ValueError("Input exceeds configured character limit; no request was sent")
        # Enforce routing even if an SDK setting tries to change it.
        payload["model"] = self.settings.model
        payload["provider"] = {
            "only": [self.settings.provider],
            "allow_fallbacks": False,
            "require_parameters": True,
            "data_collection": "deny",
            "zdr": True,
        }
        payload["max_tokens"] = self.settings.max_output_tokens
        output = payload.get("response_format", {}).get("json_schema")
        if output:
            output["schema"] = _strict_schema(output["schema"])
        for tool in payload.get("tools", []):
            if tool.get("type") == "function":
                tool["function"]["parameters"] = _strict_schema(tool["function"]["parameters"])
        budget = self._run_budget()
        attribution = None
        if invocation is not None:
            attribution = {
                **invocation.attribution(),
                "turn": invocation.calls,
                "call_id": f"{invocation.invocation_id}.{invocation.calls:03d}",
                "request_sha256": fingerprint(payload),
            }
        attempt = budget.reserve(attribution) if budget is not None else None
        started = monotonic()
        response = self.client.post(
            str(request.url),
            headers={
                key: value for key, value in request.headers.items() if key != "content-length"
            },
            json=payload,
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
        if isinstance(usage, dict):
            for category, keys in {
                "prompt_tokens_details": {"cached_tokens", "cache_write_tokens"},
                "completion_tokens_details": {"reasoning_tokens"},
            }.items():
                details = usage.get(category, {})
                if isinstance(details, dict):
                    safe_usage.update(
                        {
                            f"{category}.{key}": value
                            for key, value in details.items()
                            if key in keys and isinstance(value, (int, float))
                        }
                    )
        logger.info(
            "agent_model_call model=%s provider=%s request_id=%s usage=%s "
            "elapsed_seconds=%.3f task=%s",
            payload.get("model"),
            payload.get("provider"),
            payload.get("id"),
            safe_usage,
            monotonic() - started,
            invocation.task.task_id if invocation is not None else None,
        )
        if self.artifacts is not None and attempt is not None:
            # Keep rejected candidates and finish metadata as well as valid ones.
            # These diagnostics are never loaded as accepted domain artifacts.
            self.artifacts.write(
                f"model-output.{attempt:05d}.json",
                {
                    **(attribution or {}),
                    "request_id": payload.get("id"),
                    "schema": output["schema"].get("title", output.get("name")) if output else None,
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
        if choices[0].get("finish_reason") not in {"stop", "tool_calls"}:
            self._record_http_error(response, attempt, instruction, context)
            raise ModelResponseError("Provider returned no complete generation")
        message = choices[0].get("message", {})
        if (
            not isinstance(message, dict)
            or message.get("refusal")
            or (not isinstance(message.get("content"), str) and not message.get("tool_calls"))
        ):
            raise ModelResponseError("Provider refused or returned no text content")
        if invocation is not None and message.get("tool_calls"):
            fields = {}
            for key, expected_type in (
                ("reasoning_details", list),
                ("reasoning", str),
                ("reasoning_content", str),
            ):
                if message.get(key) is not None:
                    if not isinstance(message[key], expected_type):
                        raise ModelResponseError("Provider returned invalid reasoning metadata")
                    fields[key] = deepcopy(message[key])
            invocation.reasoning_history.append(
                {
                    "tool_identity": _tool_identity(message),
                    "reasoning_fields": fields,
                }
            )
        # Return a buffered response for the OpenAI SDK's typed parser. No retries
        # are performed here; every new network attempt must reserve its own cost.
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )

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
        sensitive = [self.settings.openrouter_api_key.get_secret_value(), instruction, context]
        # SDK requests contain a message history, including tool results. Preserve
        # the old redaction guarantee for individual message strings as well.
        try:
            messages = json.loads(context)
        except ValueError:
            messages = None
        if isinstance(messages, list):
            sensitive.extend(
                item["content"]
                for item in messages
                if isinstance(item, dict) and isinstance(item.get("content"), str)
            )

            def collect_text(value: Any) -> None:
                if isinstance(value, str):
                    sensitive.append(value)
                elif isinstance(value, dict):
                    for child in value.values():
                        collect_text(child)
                elif isinstance(value, list):
                    for child in value:
                        collect_text(child)

            for item in messages:
                if isinstance(item, dict):
                    for key in ("reasoning", "reasoning_content", "reasoning_details"):
                        collect_text(item.get(key))

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
        logger.error("agent_http_error %s", json.dumps(details, ensure_ascii=True))
        return details


def _tool_identity(message: dict[str, Any]) -> str:
    try:
        return fingerprint(
            [
                {
                    "id": call["id"],
                    "name": call["function"]["name"],
                    "arguments": call["function"]["arguments"],
                }
                for call in message["tool_calls"]
            ]
        )
    except (KeyError, TypeError):
        raise ModelResponseError("Provider returned invalid tool-call metadata") from None


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
