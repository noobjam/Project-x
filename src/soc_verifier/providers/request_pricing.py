"""Explicit local request estimate for text-only Responses tool loops."""

import json
from decimal import Decimal
from typing import Any


def pricing_bound(endpoint: dict[str, Any], model: str) -> dict[str, Any]:
    pricing = endpoint["pricing"]
    allowed = {
        "prompt",
        "completion",
        "input_cache_read",
        "input_cache_write",
        "web_search",
        "discount",
        "overrides",
    }
    if set(pricing) - allowed or pricing.get("discount", 0) != 0:
        raise ValueError("Unrecognized endpoint fee")
    overrides = pricing.get("overrides", [])
    if not isinstance(overrides, list):
        raise ValueError("Invalid endpoint pricing tiers")
    tiers = [pricing]
    for override in overrides:
        if (
            not isinstance(override, dict)
            or set(override)
            - {"min_prompt_tokens", "prompt", "completion", "input_cache_read", "input_cache_write"}
            or type(override.get("min_prompt_tokens")) is not int
            or override["min_prompt_tokens"] < 0
        ):
            raise ValueError("Unknown endpoint pricing tier")
        tiers.append({**pricing, **override})
    inputs = [
        Decimal(str(tier[key]))
        for tier in tiers
        for key in ("prompt", "input_cache_read", "input_cache_write")
        if key in tier
    ]
    outputs = [Decimal(str(tier["completion"])) for tier in tiers]
    if "prompt" not in pricing or any(
        not rate.is_finite() or rate < 0 for rate in inputs + outputs
    ):
        raise ValueError("Invalid endpoint pricing")
    capacity, maximum = endpoint["context_length"], endpoint.get("max_completion_tokens")
    if (
        type(capacity) is not int
        or capacity <= 0
        or (maximum is not None and (type(maximum) is not int or maximum <= 0))
    ):
        raise ValueError("Invalid endpoint token limits")
    return {
        "format": "responses-pricing-v1",
        "model": model,
        "provider": endpoint["tag"],
        "pricing": pricing,
        "context_capacity": capacity,
        "max_completion_tokens": maximum,
        "input_rate": str(max(inputs)),
        "output_rate": str(max(outputs)),
    }


def estimate_request(payload: dict[str, Any], pricing: dict[str, Any]) -> dict[str, Any]:
    # Includes instructions, tools, output schema, opaque reasoning and all follow-up data.
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    input_tokens = 2 * len(encoded) + 8192
    output_tokens = payload["max_output_tokens"]
    maximum = pricing["max_completion_tokens"]
    if (
        type(output_tokens) is not int
        or output_tokens <= 0
        or input_tokens + output_tokens > pricing["context_capacity"]
        or (maximum is not None and output_tokens > maximum)
    ):
        raise ValueError("Request estimate exceeds provider token limits")
    return {
        "format": "responses-request-estimate-v1",
        "input_utf8_bytes": len(encoded),
        "estimated_input_tokens": input_tokens,
        "output_token_limit": output_tokens,
        "exact_provider_token_count": False,
        "provider_enforced_dollar_cap": False,
        "reservation_usd": str(
            input_tokens * Decimal(pricing["input_rate"])
            + output_tokens * Decimal(pricing["output_rate"])
        ),
    }
