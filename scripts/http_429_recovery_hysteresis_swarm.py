#!/usr/bin/env python3
"""NET-429-HYS-002: deterministic metamorphic swarm for Recovery Hysteresis.

This state-machine-only experiment generates no network traffic.

It stresses relations across a grid of hysteresis policies instead of relying
only on the frozen eight-case fixture from NET-429-HYS-001.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from http_429_recovery_hysteresis import Gate, Policy


COUNTS = (2, 3, 4)
DURATIONS = (0.0, 2.0, 5.0, 10.0)
BASE_S = 10.0


def run(policy: Policy, events: list[dict[str, Any]], *, initial: str = "B") -> dict[str, Any]:
    gate = Gate(policy=policy, state=initial)
    transitions = [gate.observe(float(e["at_s"]), e["outcome"]) for e in events]
    return {
        "states": [row["to_state"] for row in transitions],
        "resets": gate.failure_history_resets,
        "final_state": gate.state,
        "failure_history_active": gate.failure_history_active,
        "promotions": sum(bool(row["promoted_to_healthy"]) for row in transitions),
        "transitions": transitions,
    }


def promotion_events(count: int, duration: float, *, shift: float = 0.0) -> list[dict[str, Any]]:
    start = BASE_S + shift
    if count < 2:
        raise ValueError("count must be >= 2")
    # Evenly place confirmations from start through the exact duration boundary.
    # duration=0 intentionally permits equal timestamps; monotonicity still holds.
    times = [
        start + duration * index / (count - 1)
        for index in range(count)
    ]
    return [{"at_s": t, "outcome": "2xx"} for t in times]


def relation(
    *,
    policy: Policy,
    relation_name: str,
    passed: bool,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "policy": asdict(policy),
        "relation": relation_name,
        "pass": bool(passed),
        "details": details,
    }


def build() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    generated_inputs: list[dict[str, Any]] = []

    for count in COUNTS:
        for duration in DURATIONS:
            policy = Policy(
                confirmation_successes_required=count,
                minimum_recovering_duration_s=duration,
            )
            policy.validate()

            # 1) First post-Blocked success is always provisional Recovering.
            first_events = [{"at_s": BASE_S, "outcome": "2xx"}]
            first = run(policy, first_events)
            generated_inputs.append(
                {"policy": asdict(policy), "family": "first_success", "events": first_events}
            )
            checks.append(
                relation(
                    policy=policy,
                    relation_name="first_success_is_recovering",
                    passed=(
                        first["states"] == ["E"]
                        and first["resets"] == 0
                        and first["failure_history_active"] is True
                    ),
                    details={
                        "observed_states": first["states"],
                        "resets": first["resets"],
                    },
                )
            )

            # 2) A 429 during Recovering always returns to Blocked.
            rebound_events = [
                {"at_s": BASE_S, "outcome": "2xx"},
                {"at_s": BASE_S + 0.5, "outcome": "429"},
            ]
            rebound = run(policy, rebound_events)
            generated_inputs.append(
                {"policy": asdict(policy), "family": "rebound", "events": rebound_events}
            )
            checks.append(
                relation(
                    policy=policy,
                    relation_name="recovering_429_rebounds_to_blocked",
                    passed=(
                        rebound["states"] == ["E", "B"]
                        and rebound["resets"] == 0
                        and rebound["failure_history_active"] is True
                    ),
                    details={
                        "observed_states": rebound["states"],
                        "resets": rebound["resets"],
                    },
                )
            )

            # 3) Exact count+duration boundary promotes once and only once.
            exact_events = promotion_events(count, duration)
            exact = run(policy, exact_events)
            generated_inputs.append(
                {"policy": asdict(policy), "family": "exact_boundary", "events": exact_events}
            )
            expected_prefix = ["E"] * (count - 1) + ["H"]
            checks.append(
                relation(
                    policy=policy,
                    relation_name="exact_boundary_promotes_once",
                    passed=(
                        exact["states"] == expected_prefix
                        and exact["resets"] == 1
                        and exact["promotions"] == 1
                        and exact["failure_history_active"] is False
                    ),
                    details={
                        "observed_states": exact["states"],
                        "expected_states": expected_prefix,
                        "resets": exact["resets"],
                    },
                )
            )

            # 4) Raising the confirmation-count threshold cannot promote earlier.
            stricter_count = Policy(
                confirmation_successes_required=count + 1,
                minimum_recovering_duration_s=duration,
            )
            strict_count_result = run(stricter_count, exact_events)
            checks.append(
                relation(
                    policy=policy,
                    relation_name="stricter_count_cannot_promote_earlier",
                    passed=(
                        exact["final_state"] == "H"
                        and strict_count_result["final_state"] == "E"
                        and strict_count_result["resets"] == 0
                    ),
                    details={
                        "base_final": exact["final_state"],
                        "strict_policy": asdict(stricter_count),
                        "strict_final": strict_count_result["final_state"],
                    },
                )
            )

            # 5) Raising the duration threshold cannot promote earlier.
            stricter_duration = Policy(
                confirmation_successes_required=count,
                minimum_recovering_duration_s=duration + 1.0,
            )
            strict_duration_result = run(stricter_duration, exact_events)
            checks.append(
                relation(
                    policy=policy,
                    relation_name="stricter_duration_cannot_promote_earlier",
                    passed=(
                        exact["final_state"] == "H"
                        and strict_duration_result["final_state"] == "E"
                        and strict_duration_result["resets"] == 0
                    ),
                    details={
                        "base_final": exact["final_state"],
                        "strict_policy": asdict(stricter_duration),
                        "strict_final": strict_duration_result["final_state"],
                    },
                )
            )

            # 6) Translating all observation times preserves the state sequence.
            shifted_events = promotion_events(count, duration, shift=123.0)
            shifted = run(policy, shifted_events)
            checks.append(
                relation(
                    policy=policy,
                    relation_name="time_translation_preserves_semantics",
                    passed=(
                        shifted["states"] == exact["states"]
                        and shifted["resets"] == exact["resets"]
                        and shifted["promotions"] == exact["promotions"]
                    ),
                    details={
                        "base_states": exact["states"],
                        "shifted_states": shifted["states"],
                        "shift_s": 123.0,
                    },
                )
            )

            # 7) Once Healthy is established, further successes do not reset
            # failure history a second time.
            post_h_events = exact_events + [
                {
                    "at_s": exact_events[-1]["at_s"] + 1.0,
                    "outcome": "2xx",
                }
            ]
            post_h = run(policy, post_h_events)
            checks.append(
                relation(
                    policy=policy,
                    relation_name="post_healthy_success_does_not_reset_again",
                    passed=(
                        post_h["final_state"] == "H"
                        and post_h["resets"] == 1
                        and post_h["promotions"] == 1
                    ),
                    details={
                        "observed_states": post_h["states"],
                        "resets": post_h["resets"],
                    },
                )
            )

    payload = json.dumps(
        generated_inputs,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()

    failed = [row for row in checks if not row["pass"]]
    families: dict[str, int] = {}
    for row in checks:
        families[row["relation"]] = families.get(row["relation"], 0) + 1

    return {
        "schema": "http-429-recovery-hysteresis-metamorphic-report/v1",
        "experiment_id": "NET-429-HYS-002",
        "classification": "deterministic_state_machine_metamorphic_lab_not_provider_behavior",
        "generator": {
            "id": "hysteresis-metamorphic-kitten-swarm-v1",
            "deterministic": True,
            "policy_count": len(COUNTS) * len(DURATIONS),
            "confirmation_counts": list(COUNTS),
            "minimum_recovering_durations_s": list(DURATIONS),
            "relation_checks": len(checks),
            "relation_families": families,
            "generated_input_sha256": digest,
        },
        "summary": {
            "relation_checks": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        "checks": checks,
        "safety": {
            "production_traffic": False,
            "network_access": False,
            "operation_replay_authority": False,
        },
        "interpretation": {
            "pass_means": (
                "The executable hysteresis gate preserves seven predeclared "
                "relations across a deterministic 12-policy grid."
            ),
            "pass_does_not_mean": (
                "Any tested count/duration threshold is a production recommendation "
                "or that provider recovery follows this state machine."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    if report["summary"]["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
