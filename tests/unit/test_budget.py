from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from soc_verifier.providers.budget import BudgetExceeded, CallBudget, read_spending
from soc_verifier.storage.artifacts import ArtifactStore


def budget(tmp_path, **overrides):
    arguments = {"max_cost": Decimal("1"), "max_calls": 10, "reservation": Decimal("0.4")}
    return CallBudget(ArtifactStore(tmp_path), **(arguments | overrides))


def test_cost_reservations_prevent_overspend(tmp_path):
    ledger = budget(tmp_path)
    first = ledger.reserve()
    ledger.reserve()
    with pytest.raises(BudgetExceeded, match="cost budget"):
        ledger.reserve()
    ledger.settle(first, 0.1)
    assert ledger.reserve() == 3
    assert ledger.committed == Decimal("0.9")


def test_unknown_cost_remains_reserved_after_restart(tmp_path):
    ledger = budget(tmp_path)
    ledger.settle(ledger.reserve(), 0.1)
    ledger.reserve()  # interrupted request: charge unknown
    restored = budget(tmp_path)
    assert restored.committed == Decimal("0.5")
    restored.reserve()
    with pytest.raises(BudgetExceeded):
        restored.reserve()


def test_call_limit_survives_restart(tmp_path):
    ledger = budget(tmp_path, max_calls=1)
    ledger.settle(ledger.reserve(), 0.01)
    with pytest.raises(BudgetExceeded, match="model-call"):
        budget(tmp_path, max_calls=1).reserve()


def test_parallel_reservations_share_one_budget(tmp_path):
    ledger = budget(tmp_path)

    def reserve(_):
        try:
            return ledger.reserve()
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(reserve, range(8)))
    assert sum(value is not None for value in results) == 2
    assert ledger.committed == Decimal("0.8")


@pytest.mark.parametrize("cost", [None, "0.1", -1, float("nan"), True])
def test_invalid_billing_metadata_does_not_release_reservation(tmp_path, cost):
    ledger = budget(tmp_path)
    ledger.settle(ledger.reserve(), cost)
    assert ledger.committed == Decimal("0.4")


def test_pricing_violation_stays_blocked_on_resume(tmp_path):
    ledger = budget(tmp_path)
    with pytest.raises(BudgetExceeded, match="advertised"):
        ledger.settle(ledger.reserve(), 0.5)
    with pytest.raises(BudgetExceeded, match="pricing violation"):
        budget(tmp_path)


def test_spending_separates_reported_and_uncertain_charges_without_writing(tmp_path):
    ledger = budget(tmp_path)
    ledger.settle(ledger.reserve(), 0.125)
    ledger.settle(ledger.reserve(), 0)  # Rejected before inference, no charge.
    ledger.reserve()  # No usage yet: still reserved.
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    snapshot = read_spending(ArtifactStore(tmp_path))
    assert snapshot.attempts == 3
    assert snapshot.reported == Decimal("0.125")
    assert snapshot.reserved == Decimal("0.4")
    assert snapshot.unsettled_calls == 1
    assert snapshot.committed == budget(tmp_path).committed == Decimal("0.525")
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
