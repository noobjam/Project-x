"""Stateless Responses wire contract; accounting remains in the shared transport."""

from typing import Any

from soc_verifier.agents.base import ModelResponseError, OutputLimitError


def prepare_responses(payload: dict[str, Any], max_output_tokens: int) -> dict[str, Any] | None:
    """Keep the full local tool history, local function tools and explicit output bounds."""
    if set(payload) - {
        "model",
        "provider",
        "instructions",
        "input",
        "tools",
        "tool_choice",
        "parallel_tool_calls",
        "include",
        "reasoning",
        "text",
        "store",
        "truncation",
        "max_output_tokens",
        "metadata",
        "previous_response_id",
        "conversation",
        "stream",
        "background",
    }:
        raise ValueError("Unsupported Responses request fields")
    if any(
        payload.get(key) for key in ("previous_response_id", "conversation", "stream", "background")
    ):
        raise ValueError("Only stateless, non-streaming Responses requests are supported")
    if any(tool.get("type") != "function" for tool in payload.get("tools", [])):
        raise ValueError("Only local function tools are supported")
    for item in payload.get("input", []):
        if not isinstance(item, dict) or item.get("type") not in {
            None,
            "message",
            "function_call",
            "function_call_output",
            "reasoning",
        }:
            raise ValueError("Only local text and function history are supported")
        content = item.get("content", "")
        if not isinstance(content, str) and (
            not isinstance(content, list)
            or any(
                not isinstance(part, dict) or part.get("type") not in {"input_text", "output_text"}
                for part in content
            )
        ):
            raise ValueError("Only text input is supported")
        if item.get("type") == "function_call_output" and not isinstance(item.get("output"), str):
            raise ValueError("Only text function output is supported")
    payload["store"] = False
    payload["truncation"] = "disabled"
    payload["max_output_tokens"] = max_output_tokens
    choice = payload.get("tool_choice")
    text = payload.get("text", {})
    if choice == "required" or (isinstance(choice, dict) and choice.get("type") == "function"):
        text.pop("format", None)
    output: dict[str, Any] | None = text.get("format")
    return output if output and output.get("type") == "json_schema" else None


def validate_response(payload: dict[str, Any]) -> None:
    """Reject partial/refused generations after their actual usage has been recorded."""
    if payload.get("status") == "incomplete":
        details = payload.get("incomplete_details")
        if isinstance(details, dict) and details.get("reason") == "max_output_tokens":
            raise OutputLimitError(
                "Provider reached the output token limit; generation is incomplete"
            )
        raise ModelResponseError("Provider returned an incomplete response")
    if payload.get("error") or payload.get("status") != "completed":
        raise ModelResponseError("Provider returned no complete generation")
    output = payload.get("output")
    if (
        not isinstance(output, list)
        or not output
        or any(not isinstance(item, dict) for item in output)
    ):
        raise ModelResponseError("Provider returned no complete generation")
    has_content = False
    for item in output:
        if item.get("status") not in {None, "completed"}:
            raise ModelResponseError("Provider returned an incomplete output item")
        if item.get("type") == "function_call":
            if not all(
                isinstance(item.get(key), str) and item[key]
                for key in ("name", "call_id", "arguments")
            ):
                raise ModelResponseError("Provider returned invalid tool-call metadata")
            has_content = True
        elif item.get("type") == "message":
            content = item.get("content")
            if not isinstance(content, list) or any(not isinstance(part, dict) for part in content):
                raise ModelResponseError("Provider returned invalid message content")
            if any(part.get("type") == "refusal" for part in content):
                raise ModelResponseError("Provider refused the request")
            has_content |= any(
                part.get("type") == "output_text"
                and isinstance(part.get("text"), str)
                and bool(part["text"])
                for part in content
            )
        elif item.get("type") != "reasoning":
            raise ModelResponseError("Provider returned an unsupported output item")
    if not has_content:
        raise ModelResponseError("Provider returned no text or tool calls")
