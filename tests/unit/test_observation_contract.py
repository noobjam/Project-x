"""Observation selection is separate from permission to choose HDL expressions."""

import pytest

from soc_verifier.domain.hardware import HardwareTarget
from soc_verifier.domain.testbench_proposal import TestbenchProposal as LegacyProposal


def test_old_hardware_format_does_not_silently_gain_internal_probes():
    with pytest.raises(ValueError, match="hardware-target-v2"):
        HardwareTarget.model_validate(
            {
                "format": "hardware-target-v1",
                "top_module": "sample",
                "clock": "clk",
                "parameters": {},
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "q", "direction": "output", "width": 1},
                ],
                "probes": [{"name": "state", "path": "hidden.state", "width": 1}],
            }
        )


@pytest.mark.parametrize("phase", ["pre_edge", "post_edge"])
def test_legacy_proposal_keeps_post_edge_semantics(phase):
    data = {
        "format": "testbench-proposal-v1",
        "plan_item_id": "P",
        "status": "ready",
        "rationale": "Historical reader control",
        "initial_inputs": [],
        "rtl_source_ids": ["rtl-0"],
        "open_questions": [],
        "steps": [
            {
                "description": "Observe",
                "inputs": [],
                "cycles": 1,
                "checks": [
                    {
                        "signal": "q",
                        "value": 0,
                        "phase": phase,
                        "source_ids": ["S1"],
                        "expected_result_index": 0,
                    }
                ],
            }
        ],
    }
    if phase == "pre_edge":
        with pytest.raises(ValueError, match="testbench-proposal-v2"):
            LegacyProposal.model_validate(data)
    else:
        assert LegacyProposal.model_validate(data).format == "testbench-proposal-v1"
