import json
from decimal import Decimal

import pytest

from soc_verifier.providers.request_pricing import estimate_request, pricing_bound


def endpoint(**pricing):
    return {
        "tag": "synthetic",
        "context_length": 1_000_000,
        "max_completion_tokens": 1000,
        "pricing": {"prompt": "0.000001", "completion": "0.000002", **pricing},
    }


def test_response_bound_accounts_for_tools_schema_history_and_worst_tier():
    prices = pricing_bound(
        endpoint(
            input_cache_write="0.00000125",
            overrides=[
                {
                    "min_prompt_tokens": 100000,
                    "prompt": "0.000002",
                    "completion": "0.000003",
                    "input_cache_write": "0.0000025",
                }
            ],
        ),
        "test/model",
    )
    assert prices["input_rate"] == "0.0000025" and prices["output_rate"] == "0.000003"
    initial = {
        "instructions": "Inspect evidence",
        "input": [{"role": "user", "content": "reset"}],
        "max_output_tokens": 256,
        "tools": [{"type": "function", "parameters": {"description": "x" * 2000}}],
        "text": {"format": {"schema": {"description": "y" * 2000}}},
    }
    first = estimate_request(initial, prices)
    assert first["input_utf8_bytes"] == len(
        json.dumps(initial, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )
    assert first["exact_provider_token_count"] is False
    followup = {
        **initial,
        "input": [*initial["input"], {"type": "function_call_output", "output": "ß" * 3000}],
    }
    later = estimate_request(followup, prices)
    assert Decimal(later["reservation_usd"]) > Decimal(first["reservation_usd"])
    assert later["provider_enforced_dollar_cap"] is False
    with pytest.raises(ValueError, match="token limits"):
        estimate_request({**initial, "max_output_tokens": 1001}, prices)


@pytest.mark.parametrize(
    "changes",
    [
        {"request": "0.01"},
        {"discount": 1},
        {"prompt": "NaN"},
        {"completion": "-1"},
        {"overrides": [{"region": "unknown", "min_prompt_tokens": 100}]},
    ],
)
def test_unrecognized_or_invalid_pricing_fails_before_request(changes):
    with pytest.raises(ValueError):
        pricing_bound(endpoint(**changes), "test/model")
