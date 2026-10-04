#!/usr/bin/env python3
"""NET-429-COMP-001: compose 429 retry scheduling with recovery hysteresis.

No network traffic is generated.

The composition is deliberately asymmetric:
- scheduler owns authorization/timing/budget;
- hysteresis owns B/E/H confidence;
- confidence may only add a conservative pacing floor while B/E;
- confidence may never create retry authority or override STOP/REOBSERVE.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from http_429_recovery_hysteresis import Gate, Policy
from http_429_survival import RetryDecision, decide


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "data" / "http_429_recovery_composition_contract.json"


@dataclass(frozen=True)
class CompositionPolicy:
    hysteresis: Policy
    base_minimum_period_s: float
    recovery_probe_period_s: float

    def validate(self) -> None:
        self.hysteresis.validate()
        if self.base_minimum_period_s < 0:
            raise ValueError("base_minimum_period_s must be non-negative")
        if self.recovery_probe_period_s < 0:
            raise ValueError("recovery_probe_period_s must be non-negative")


@dataclass
class Controller:
    policy: CompositionPolicy
    gate: Gate

    @classmethod
    def create(cls, *, policy: CompositionPolicy, state: str) -> "Controller":
        return cls(policy=policy, gate=Gate(policy=policy.hysteresis, state=state))

    def effective_minimum_period_s(self) -> float:
        if self.gate.state in {"B", "E"}:
            return max(
                self.policy.base_minimum_period_s,
                self.policy.recovery_probe_period_s,
            )
        return self.policy.base_minimum_period_s

    def next_observation_floor_s(self, *, previous_start_s: float) -> float:
        return previous_start_s + self.effective_minimum_period_s()

    def observe_success(
        self,
        *,
        start_s: float,
        complete_s: float,
    ) -> dict[str, Any]:
        before = self.gate.state
        transition = self.gate.observe(complete_s, "2xx")
        return {
            "before_confidence": before,
            "after_confidence": self.gate.state,
            "transition": transition,
            "next_observation_floor_s": self.next_observation_floor_s(
                previous_start_s=start_s
            ),
            "effective_minimum_period_s": self.effective_minimum_period_s(),
        }

    def observe_429(
        self,
        *,
        start_s: float,
        complete_s: float,
        attempt_number: int,
        retry_budget: int,
        operation_id: str,
        retry_after: str | None = None,
        draft_ratelimit: str | None = None,
        local_base_s: float = 0.5,
        local_cap_s: float = 4.0,
        herd_jitter_fraction: float = 0.0,
    ) -> dict[str, Any]:
        before = self.gate.state
        transition = self.gate.observe(complete_s, "429")

        # Classification into B happens before timing is computed. This makes
        # the composition conservative: confidence may tighten the minimum
        # period after failure but cannot shorten it.
        effective_minimum = self.effective_minimum_period_s()
        decision = decide(
            status=429,
            method="GET",
            operation_state="read_only_observation",
            application_idempotency_contract=False,
            attempt_number=attempt_number,
            retry_budget=retry_budget,
            operation_id=operation_id,
            now_s=complete_s,
            previous_start_s=start_s,
            minimum_period_s=effective_minimum,
            retry_after=retry_after,
            draft_ratelimit=draft_ratelimit,
            local_base_s=local_base_s,
            local_cap_s=local_cap_s,
            herd_jitter_fraction=herd_jitter_fraction,
            now_datetime=dt.datetime(2026, 10, 4, tzinfo=dt.timezone.utc)
            + dt.timedelta(seconds=complete_s),
        )
        return {
            "before_confidence": before,
            "after_confidence": self.gate.state,
            "transition": transition,
            "effective_minimum_period_s": effective_minimum,
            "decision": decision.as_dict(),
        }


def bare_429_decision(
    *,
    start_s: float,
    complete_s: float,
    attempt_number: int,
    retry_budget: int,
    operation_id: str,
    minimum_period_s: float,
    retry_after: str | None = None,
    local_base_s: float = 0.5,
    local_cap_s: float = 4.0,
    herd_jitter_fraction: float = 0.0,
) -> RetryDecision:
    return decide(
        status=429,
        method="GET",
        operation_state="read_only_observation",
        application_idempotency_contract=False,
        attempt_number=attempt_number,
        retry_budget=retry_budget,
        operation_id=operation_id,
        now_s=complete_s,
        previous_start_s=start_s,
        minimum_period_s=minimum_period_s,
        retry_after=retry_after,
        draft_ratelimit=None,
        local_base_s=local_base_s,
        local_cap_s=local_cap_s,
        herd_jitter_fraction=herd_jitter_fraction,
        now_datetime=dt.datetime(2026, 10, 4, tzinfo=dt.timezone.utc)
        + dt.timedelta(seconds=complete_s),
    )


def check(case_id: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": case_id,
        "pass": bool(passed),
        "details": details,
    }


def run_lab(contract: dict[str, Any]) -> dict[str, Any]:
    p = contract["lab_policy"]
    policy = CompositionPolicy(
        hysteresis=Policy(
            confirmation_successes_required=int(
                p["confirmation_successes_required"]
            ),
            minimum_recovering_duration_s=float(
                p["minimum_recovering_duration_s"]
            ),
        ),
        base_minimum_period_s=float(p["base_minimum_period_s"]),
        recovery_probe_period_s=float(p["recovery_probe_period_s"]),
    )
    policy.validate()

    results: list[dict[str, Any]] = []

    # 1) First success remains provisional and preserves a slow confirmation floor.
    c = Controller.create(policy=policy, state="B")
    first = c.observe_success(start_s=10.0, complete_s=10.1)
    results.append(
        check(
            "first-success-keeps-recovery-floor",
            first["after_confidence"] == "E"
            and first["transition"]["failure_history_reset"] is False
            and first["next_observation_floor_s"] >= 15.0
            and first["effective_minimum_period_s"] == 5.0,
            first,
        )
    )

    # 2) Reblock while E obeys the conservative start anchor.
    c = Controller.create(policy=policy, state="B")
    c.observe_success(start_s=20.0, complete_s=20.1)
    reblock = c.observe_429(
        start_s=25.0,
        complete_s=25.05,
        attempt_number=2,
        retry_budget=6,
        operation_id="comp-e-reblock",
        retry_after="3",
    )
    results.append(
        check(
            "recovering-reblock-keeps-pacing-floor",
            reblock["before_confidence"] == "E"
            and reblock["after_confidence"] == "B"
            and reblock["decision"]["action"] == "WAIT_THEN_RETRY"
            and reblock["decision"]["next_start_s"] >= 30.0,
            reblock,
        )
    )

    # 3) Confidence may tighten a local floor but never make retry earlier.
    bare = bare_429_decision(
        start_s=30.0,
        complete_s=30.05,
        attempt_number=1,
        retry_budget=6,
        operation_id="comp-monotone-floor",
        minimum_period_s=policy.base_minimum_period_s,
    )
    c = Controller.create(policy=policy, state="B")
    composed = c.observe_429(
        start_s=30.0,
        complete_s=30.05,
        attempt_number=1,
        retry_budget=6,
        operation_id="comp-monotone-floor",
    )
    results.append(
        check(
            "confidence-floor-is-monotone-conservative",
            composed["decision"]["next_start_s"] >= bare.next_start_s
            and composed["effective_minimum_period_s"]
            >= policy.base_minimum_period_s,
            {
                "bare": bare.as_dict(),
                "composed": composed,
            },
        )
    )

    # 4) A stronger Retry-After floor remains authoritative; composition does
    # not pull earlier and does not invent a different authorization action.
    bare_ra = bare_429_decision(
        start_s=40.0,
        complete_s=40.05,
        attempt_number=1,
        retry_budget=6,
        operation_id="comp-retry-after",
        minimum_period_s=policy.base_minimum_period_s,
        retry_after="9",
    )
    c = Controller.create(policy=policy, state="E")
    comp_ra = c.observe_429(
        start_s=40.0,
        complete_s=40.05,
        attempt_number=1,
        retry_budget=6,
        operation_id="comp-retry-after",
        retry_after="9",
    )
    results.append(
        check(
            "retry-after-remains-stronger-floor",
            comp_ra["decision"]["action"] == bare_ra.action
            and comp_ra["decision"]["retry_after_floor_s"]
            == bare_ra.retry_after_floor_s
            and comp_ra["decision"]["next_start_s"] == bare_ra.next_start_s,
            {"bare": bare_ra.as_dict(), "composed": comp_ra},
        )
    )

    # 5) Budget exhaustion cannot be overridden by confidence state.
    budget_rows = {}
    budget_ok = True
    for state in ("H", "E", "B"):
        c = Controller.create(policy=policy, state=state)
        row = c.observe_429(
            start_s=50.0,
            complete_s=50.01,
            attempt_number=3,
            retry_budget=3,
            operation_id=f"comp-budget-{state}",
            retry_after="1",
        )
        budget_rows[state] = row
        budget_ok = budget_ok and (
            row["decision"]["action"] == "STOP_BUDGET"
            and row["decision"]["next_start_s"] is None
            and row["decision"]["budget_remaining_after_attempt"] == 0
        )
    results.append(
        check(
            "confidence-cannot-override-budget-stop",
            budget_ok,
            budget_rows,
        )
    )

    # 6) Ambiguous non-idempotent authorization stays REOBSERVE in every
    # confidence state. Hysteresis does not mint replay authority.
    reobserve_rows = {}
    reobserve_ok = True
    for state in ("H", "E", "B"):
        d = decide(
            status=None,
            method="POST",
            operation_state="unknown",
            application_idempotency_contract=False,
            attempt_number=1,
            retry_budget=4,
            operation_id=f"comp-unknown-{state}",
            now_s=0.05,
            previous_start_s=0.0,
            minimum_period_s=(
                max(
                    policy.base_minimum_period_s,
                    policy.recovery_probe_period_s,
                )
                if state in {"B", "E"}
                else policy.base_minimum_period_s
            ),
            retry_after=None,
            draft_ratelimit=None,
            local_base_s=0.25,
            local_cap_s=2.0,
            herd_jitter_fraction=0.2,
            now_datetime=dt.datetime(
                2026, 10, 4, tzinfo=dt.timezone.utc
            ),
        )
        reobserve_rows[state] = d.as_dict()
        reobserve_ok = reobserve_ok and (
            d.action == "REOBSERVE" and d.next_start_s is None
        )
    results.append(
        check(
            "confidence-cannot-override-reobserve",
            reobserve_ok,
            reobserve_rows,
        )
    )

    # 7) Failure history clears only when E actually promotes to H.
    c = Controller.create(policy=policy, state="B")
    s1 = c.observe_success(start_s=60.0, complete_s=60.1)
    s2 = c.observe_success(start_s=65.1, complete_s=65.2)
    results.append(
        check(
            "failure-history-clears-only-on-healthy-promotion",
            s1["after_confidence"] == "E"
            and s1["transition"]["failure_history_reset"] is False
            and s2["after_confidence"] == "H"
            and s2["transition"]["failure_history_reset"] is True
            and c.gate.failure_history_resets == 1,
            {"first": s1, "second": s2},
        )
    )

    # 8) The pacing relaxation happens only after H, never at first success.
    e_floor = s1["next_observation_floor_s"]
    h_floor = s2["next_observation_floor_s"]
    results.append(
        check(
            "pacing-relaxes-only-after-healthy",
            e_floor == 65.0
            and h_floor == 66.1
            and h_floor < 70.1,
            {
                "recovering_floor_s": e_floor,
                "healthy_floor_s": h_floor,
                "base_minimum_period_s": policy.base_minimum_period_s,
                "recovery_probe_period_s": policy.recovery_probe_period_s,
            },
        )
    )

    failed = [row for row in results if not row["pass"]]
    return {
        "schema": "http-429-recovery-composition-report/v1",
        "experiment_id": contract["experiment_id"],
        "classification": "deterministic_control_plane_composition_not_provider_behavior",
        "policy": {
            "confirmation_successes_required": (
                policy.hysteresis.confirmation_successes_required
            ),
            "minimum_recovering_duration_s": (
                policy.hysteresis.minimum_recovering_duration_s
            ),
            "base_minimum_period_s": policy.base_minimum_period_s,
            "recovery_probe_period_s": policy.recovery_probe_period_s,
            "production_recommendation": False,
        },
        "results": results,
        "summary": {
            "scenarios": len(results),
            "passed": len(results) - len(failed),
            "failed": len(failed),
        },
        "safety": contract["safety"],
        "authority_boundary": {
            "scheduler_owns_retry_authorization": True,
            "hysteresis_owns_recovery_confidence": True,
            "confidence_can_create_replay_authority": False,
            "confidence_can_shorten_scheduler_floor": False,
        },
        "interpretation": {
            "pass_means": (
                "The deterministic composition preserves scheduler authority "
                "while adding only conservative recovery-confidence pacing."
            ),
            "pass_does_not_mean": (
                "The fixture periods are production recommendations or that "
                "a provider exposes these internal states."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--output")
    args = parser.parse_args()

    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    if contract["schema"] != "http-429-recovery-composition-contract/v1":
        raise SystemExit("unexpected composition contract schema")
    if contract["safety"] != {
        "network_access": False,
        "production_traffic": False,
        "operation_replay_authority": False,
    }:
        raise SystemExit("refusing unsafe composition contract")

    report = run_lab(contract)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    if report["summary"]["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
