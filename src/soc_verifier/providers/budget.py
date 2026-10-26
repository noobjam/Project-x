"""Persistent, conservative per-run cost reservations, safe across worker threads."""

from dataclasses import dataclass
from decimal import Decimal
from threading import Lock

from soc_verifier.storage.artifacts import ArtifactStore


class BudgetExceeded(RuntimeError):
    """No more model requests may be sent within this run's configured limits."""


@dataclass(frozen=True)
class Spending:
    attempts: int
    reported: Decimal
    reserved: Decimal
    unsettled_calls: int

    @property
    def committed(self) -> Decimal:
        return self.reported + self.reserved


def read_spending(artifacts: ArtifactStore) -> Spending:
    """Read the immutable ledger without calls or changes; unknown charges stay reserved."""
    attempts = unsettled_calls = 0
    reported = reserved = Decimal(0)
    for path in sorted(artifacts.root.glob("cost-reserved.*.json")):
        record = artifacts.read(path.name)
        number = int(record["attempt"])
        settled = f"cost-settled.{number:05d}.json"
        if artifacts.exists(settled):
            reported += Decimal(artifacts.read(settled)["cost_usd"])
        else:
            reserved += Decimal(record["reserved_usd"])
            unsettled_calls += 1
        attempts = max(attempts, number)
    return Spending(attempts, reported, reserved, unsettled_calls)


class CallBudget:
    def __init__(
        self,
        artifacts: ArtifactStore,
        *,
        max_cost: Decimal,
        max_calls: int,
        reservation: Decimal,
    ) -> None:
        if not reservation.is_finite() or reservation < 0:
            raise ValueError("Invalid provider cost reservation")
        self.artifacts = artifacts
        self.max_cost = max_cost
        self.max_calls = max_calls
        self.reservation = reservation
        self.lock = Lock()
        if artifacts.exists("budget-stopped.json"):
            raise BudgetExceeded("Run stopped after a provider pricing violation; start a new run")
        spending = read_spending(artifacts)
        self.count = spending.attempts
        self.committed = spending.committed

    def reserve(self) -> int:
        with self.lock:
            if self.count >= self.max_calls:
                raise BudgetExceeded("Run model-call limit reached; no request was sent")
            if self.committed + self.reservation > self.max_cost:
                raise BudgetExceeded(
                    "Run cost budget cannot cover another request; no request was sent"
                )
            attempt = self.count + 1
            self.artifacts.write(
                f"cost-reserved.{attempt:05d}.json",
                {
                    "attempt": attempt,
                    "reserved_usd": str(self.reservation),
                },
            )
            self.count = attempt
            self.committed += self.reservation
            return attempt

    def settle(self, attempt: int, cost: object) -> None:
        # Unknown charges keep the full reservation, including network failures.
        if not isinstance(cost, (int, float)) or isinstance(cost, bool):
            return
        actual = Decimal(str(cost))
        if not actual.is_finite() or actual < 0:
            return
        with self.lock:
            self.artifacts.write(
                f"cost-settled.{attempt:05d}.json",
                {
                    "attempt": attempt,
                    "cost_usd": str(actual),
                },
            )
            self.committed += actual - self.reservation
            if actual > self.reservation:
                # Endpoint pricing/capacity did not match billed usage. Fail closed.
                self.artifacts.write(
                    "budget-stopped.json",
                    {"attempt": attempt, "reason": "Provider exceeded advertised reservation"},
                )
                self.committed = max(self.committed, self.max_cost)
                raise BudgetExceeded(
                    "Provider exceeded its advertised cost reservation; run stopped"
                )
