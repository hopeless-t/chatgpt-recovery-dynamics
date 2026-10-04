#!/usr/bin/env python3
"""NET-429-HYS-001: executable recovery hysteresis state machine.

This layer does not schedule retries and does not generate network traffic.
It classifies recovery confidence after observations already exist.

B --first 2xx--> E
E --stable confirmation--> H
E --429--> B

The confirmation count/window are policy parameters, not provider claims.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "data" / "http_429_recovery_hysteresis_contract.json"
DEFAULT_SCENARIOS = ROOT / "data" / "http_429_recovery_hysteresis_scenarios.json"


@dataclass
class Policy:
    confirmation_successes_required: int
    minimum_recovering_duration_s: float

    def validate(self) -> None:
        if self.confirmation_successes_required < 2:
            raise ValueError("confirmation_successes_required must be >= 2")
        if self.minimum_recovering_duration_s < 0:
            raise ValueError("minimum_recovering_duration_s must be >= 0")


@dataclass
class Gate:
    policy: Policy
    state: str
    recovering_since_s: float | None = None
    recovering_successes: int = 0
    failure_history_active: bool = False
    failure_history_resets: int = 0

    def __post_init__(self) -> None:
        if self.state not in {"H", "E", "B"}:
            raise ValueError(f"invalid initial state: {self.state}")
        if self.state in {"B", "E"}:
            self.failure_history_active = True

    def observe(self, at_s: float, outcome: str) -> dict[str, Any]:
        if at_s < 0:
            raise ValueError("observation time must be non-negative")
        if outcome not in {"2xx", "429"}:
            raise ValueError(f"unsupported outcome: {outcome}")

        before = self.state
        reset = False
        promoted = False
        recovering_duration_s: float | None = None
        reason = ""

        if outcome == "429":
            self.state = "B"
            self.recovering_since_s = None
            self.recovering_successes = 0
            self.failure_history_active = True
            reason = "throttling returns or keeps recovery in Blocked"

        elif self.state == "H":
            self.state = "H"
            reason = "established Healthy success remains Healthy"

        elif self.state == "B":
            self.state = "E"
            self.recovering_since_s = at_s
            self.recovering_successes = 1
            self.failure_history_active = True
            reason = "first success after Blocked is provisional Recovering"

        else:
            assert self.state == "E"
            assert self.recovering_since_s is not None
            self.recovering_successes += 1
            duration = at_s - self.recovering_since_s
            recovering_duration_s = duration
            count_ok = (
                self.recovering_successes
                >= self.policy.confirmation_successes_required
            )
            duration_ok = (
                duration >= self.policy.minimum_recovering_duration_s
            )
            if count_ok and duration_ok:
                self.state = "H"
                self.failure_history_active = False
                self.failure_history_resets += 1
                reset = True
                promoted = True
                reason = (
                    "confirmation count and recovering-duration conditions "
                    "both satisfied"
                )
                self.recovering_since_s = None
                self.recovering_successes = 0
            else:
                self.state = "E"
                reason = (
                    "success observed but stable-confirmation conditions "
                    "are not both satisfied"
                )

        return {
            "at_s": at_s,
            "outcome": outcome,
            "from_state": before,
            "to_state": self.state,
            "recovering_since_s": self.recovering_since_s,
            "recovering_successes": self.recovering_successes,
            "recovering_duration_s": recovering_duration_s,
            "failure_history_active": self.failure_history_active,
            "failure_history_reset": reset,
            "promoted_to_healthy": promoted,
            "reason": reason,
        }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_case(case: dict[str, Any], policy: Policy) -> dict[str, Any]:
    gate = Gate(policy=policy, state=case["initial_state"])
    transitions: list[dict[str, Any]] = []
    previous_time = -1.0

    for event in case["events"]:
        at_s = float(event["at_s"])
        if at_s < previous_time:
            raise ValueError(
                f"{case['scenario_id']}: event times must be monotonic"
            )
        previous_time = at_s
        transitions.append(gate.observe(at_s, event["outcome"]))

    observed_states = [row["to_state"] for row in transitions]
    expected = case["expect"]

    errors: list[str] = []
    if observed_states != expected["states"]:
        errors.append(
            f"states {observed_states!r} != {expected['states']!r}"
        )
    if gate.state != expected["final_state"]:
        errors.append(
            f"final_state {gate.state!r} != {expected['final_state']!r}"
        )
    if gate.failure_history_resets != expected["failure_history_resets"]:
        errors.append(
            "failure_history_resets "
            f"{gate.failure_history_resets} != "
            f"{expected['failure_history_resets']}"
        )

    return {
        "scenario_id": case["scenario_id"],
        "initial_state": case["initial_state"],
        "transitions": transitions,
        "observed_states": observed_states,
        "final_state": gate.state,
        "failure_history_resets": gate.failure_history_resets,
        "pass": not errors,
        "errors": errors,
    }


def structural_assertions(report: dict[str, Any]) -> None:
    by_id = {row["scenario_id"]: row for row in report["results"]}

    first = by_id["first-success-is-recovering"]
    assert first["transitions"][0]["from_state"] == "B"
    assert first["transitions"][0]["to_state"] == "E"
    assert first["transitions"][0]["failure_history_reset"] is False

    rebound = by_id["rebound-before-confirmation"]
    assert rebound["observed_states"] == ["E", "B"]
    assert rebound["failure_history_resets"] == 0

    early = by_id["count-met-window-not-met"]
    assert early["observed_states"] == ["E", "E"]

    promoted = by_id["window-met-count-met-promotes"]
    assert promoted["observed_states"] == ["E", "H"]
    assert promoted["transitions"][-1]["failure_history_reset"] is True
    assert promoted["failure_history_resets"] == 1

    reblocked = by_id["promote-then-reblock"]
    assert reblocked["observed_states"] == ["E", "H", "B"]
    assert reblocked["failure_history_resets"] == 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS))
    parser.add_argument("--output")
    args = parser.parse_args()

    contract = load_json(Path(args.contract))
    scenarios = load_json(Path(args.scenarios))

    if contract["schema"] != "http-429-recovery-hysteresis-contract/v1":
        raise SystemExit("unexpected contract schema")
    if scenarios["schema"] != "http-429-recovery-hysteresis-scenarios/v1":
        raise SystemExit("unexpected scenario schema")
    if contract["experiment_id"] != scenarios["experiment_id"]:
        raise SystemExit("experiment id mismatch")
    if scenarios["safety"] != {
        "network_scope": "none_state_machine_only",
        "production_traffic": False,
    }:
        raise SystemExit("refusing non-local/non-state-machine scenario surface")

    p = scenarios["lab_policy"]
    policy = Policy(
        confirmation_successes_required=int(
            p["confirmation_successes_required"]
        ),
        minimum_recovering_duration_s=float(
            p["minimum_recovering_duration_s"]
        ),
    )
    policy.validate()

    results = [run_case(case, policy) for case in scenarios["cases"]]
    report = {
        "schema": "http-429-recovery-hysteresis-report/v1",
        "experiment_id": contract["experiment_id"],
        "classification": (
            "deterministic_state_machine_lab_not_provider_behavior"
        ),
        "policy": {
            "confirmation_successes_required": (
                policy.confirmation_successes_required
            ),
            "minimum_recovering_duration_s": (
                policy.minimum_recovering_duration_s
            ),
            "production_recommendation": False,
        },
        "results": results,
        "summary": {
            "scenarios": len(results),
            "passed": sum(row["pass"] for row in results),
            "failed": sum(not row["pass"] for row in results),
        },
        "invariants": {
            "first_success_after_blocked_is_recovering": True,
            "first_success_resets_failure_history": False,
            "recovering_429_returns_blocked": True,
            "healthy_requires_configured_stability_confirmation": True,
            "failure_history_reset_only_on_e_to_h": True,
        },
        "safety": {
            "production_traffic": False,
            "network_access": False,
            "operation_replay_authority": False,
        },
        "interpretation": {
            "pass_means": (
                "The executable state-machine fixture preserves the "
                "repository's recovery-hysteresis invariants."
            ),
            "pass_does_not_mean": (
                "The fixture thresholds are correct for any production "
                "provider or that the observed 8/8 rebound is universal."
            ),
        },
    }
    structural_assertions(report)

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    if report["summary"]["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
