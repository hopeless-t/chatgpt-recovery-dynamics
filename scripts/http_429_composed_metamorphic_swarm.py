#!/usr/bin/env python3
"""NET-429-COMP-002: metamorphic swarm for scheduler × hysteresis composition.

State/control-plane only. No network traffic.

This expands NET-429-COMP-001 from one fixture policy to a deterministic grid
and checks relations rather than memorized outputs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

from http_429_recovery_composition import (
    CompositionPolicy,
    Controller,
    bare_429_decision,
)
from http_429_recovery_hysteresis import Policy
from http_429_survival import decide


COUNTS = (2, 3)
DURATIONS = (0.0, 5.0)
BASE_PERIODS = (0.5, 2.0)
RECOVERY_PERIODS = (1.0, 5.0)
RELATIONS = (
    "first_success_preserves_composed_floor",
    "429_decision_independent_of_prior_confidence",
    "confidence_floor_monotone_vs_bare_scheduler",
    "strong_retry_after_remains_authoritative",
    "budget_stop_orthogonal_to_confidence",
    "reobserve_orthogonal_to_confidence",
    "pacing_relaxes_only_after_healthy",
    "stricter_recovery_period_cannot_start_earlier",
)


def key_decision(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": row["action"],
        "next_start_s": row["next_start_s"],
        "retry_after_floor_s": row["retry_after_floor_s"],
        "local_backoff_s": row["local_backoff_s"],
        "budget_remaining_after_attempt": row[
            "budget_remaining_after_attempt"
        ],
        "standards_used": row["standards_used"],
    }


def relation(
    policy: CompositionPolicy,
    name: str,
    passed: bool,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "policy": {
            "confirmation_successes_required": (
                policy.hysteresis.confirmation_successes_required
            ),
            "minimum_recovering_duration_s": (
                policy.hysteresis.minimum_recovering_duration_s
            ),
            "base_minimum_period_s": policy.base_minimum_period_s,
            "recovery_probe_period_s": policy.recovery_probe_period_s,
        },
        "relation": name,
        "pass": bool(passed),
        "details": details,
    }


def promotion_sequence(
    policy: CompositionPolicy,
    *,
    base_start_s: float = 100.0,
) -> tuple[list[dict[str, Any]], Controller]:
    count = policy.hysteresis.confirmation_successes_required
    duration = policy.hysteresis.minimum_recovering_duration_s
    first_complete = base_start_s + 0.1
    complete_times = [
        first_complete + duration * i / (count - 1)
        for i in range(count)
    ]
    controller = Controller.create(policy=policy, state="B")
    rows: list[dict[str, Any]] = []
    for complete_s in complete_times:
        start_s = complete_s - 0.1
        rows.append(
            controller.observe_success(
                start_s=start_s,
                complete_s=complete_s,
            )
        )
    return rows, controller


def build() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    policy_inputs: list[dict[str, Any]] = []

    for count in COUNTS:
        for duration in DURATIONS:
            for base_period in BASE_PERIODS:
                for recovery_period in RECOVERY_PERIODS:
                    policy = CompositionPolicy(
                        hysteresis=Policy(
                            confirmation_successes_required=count,
                            minimum_recovering_duration_s=duration,
                        ),
                        base_minimum_period_s=base_period,
                        recovery_probe_period_s=recovery_period,
                    )
                    policy.validate()
                    descriptor = {
                        "confirmation_successes_required": count,
                        "minimum_recovering_duration_s": duration,
                        "base_minimum_period_s": base_period,
                        "recovery_probe_period_s": recovery_period,
                    }
                    policy_inputs.append(descriptor)
                    effective = max(base_period, recovery_period)

                    # 1) First success stays E and uses the composed conservative floor.
                    c = Controller.create(policy=policy, state="B")
                    first = c.observe_success(start_s=10.0, complete_s=10.1)
                    expected_floor = 10.0 + effective
                    checks.append(
                        relation(
                            policy,
                            "first_success_preserves_composed_floor",
                            (
                                first["after_confidence"] == "E"
                                and first["transition"]["failure_history_reset"]
                                is False
                                and first["effective_minimum_period_s"]
                                == effective
                                and math.isclose(
                                    first["next_observation_floor_s"],
                                    expected_floor,
                                    rel_tol=0.0,
                                    abs_tol=1e-12,
                                )
                            ),
                            {
                                "observed_floor_s": first[
                                    "next_observation_floor_s"
                                ],
                                "expected_floor_s": expected_floor,
                            },
                        )
                    )

                    # 2) A 429 classifies to B first; scheduler output is therefore
                    # independent of whether confidence was H/E/B beforehand.
                    decisions = {}
                    for initial in ("H", "E", "B"):
                        c = Controller.create(policy=policy, state=initial)
                        row = c.observe_429(
                            start_s=20.0,
                            complete_s=20.05,
                            attempt_number=1,
                            retry_budget=6,
                            operation_id="comp-meta-confidence",
                            herd_jitter_fraction=0.0,
                        )
                        decisions[initial] = {
                            "after_confidence": row["after_confidence"],
                            "decision": key_decision(row["decision"]),
                        }
                    canonical = decisions["B"]["decision"]
                    checks.append(
                        relation(
                            policy,
                            "429_decision_independent_of_prior_confidence",
                            (
                                all(
                                    row["after_confidence"] == "B"
                                    for row in decisions.values()
                                )
                                and all(
                                    row["decision"] == canonical
                                    for row in decisions.values()
                                )
                            ),
                            decisions,
                        )
                    )

                    # 3) Confidence pacing may only delay beyond the bare scheduler.
                    bare = bare_429_decision(
                        start_s=30.0,
                        complete_s=30.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id="comp-meta-monotone",
                        minimum_period_s=base_period,
                        herd_jitter_fraction=0.0,
                    )
                    c = Controller.create(policy=policy, state="B")
                    composed = c.observe_429(
                        start_s=30.0,
                        complete_s=30.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id="comp-meta-monotone",
                        herd_jitter_fraction=0.0,
                    )
                    checks.append(
                        relation(
                            policy,
                            "confidence_floor_monotone_vs_bare_scheduler",
                            (
                                composed["decision"]["action"] == bare.action
                                and composed["decision"]["next_start_s"]
                                >= bare.next_start_s
                            ),
                            {
                                "bare": bare.as_dict(),
                                "composed": composed["decision"],
                            },
                        )
                    )

                    # 4) A Retry-After larger than both local periods stays the
                    # authoritative floor and yields the same start in both paths.
                    retry_after = str(int(math.ceil(effective)) + 10)
                    bare_ra = bare_429_decision(
                        start_s=40.0,
                        complete_s=40.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id="comp-meta-ra",
                        minimum_period_s=base_period,
                        retry_after=retry_after,
                        herd_jitter_fraction=0.0,
                    )
                    c = Controller.create(policy=policy, state="E")
                    comp_ra = c.observe_429(
                        start_s=40.0,
                        complete_s=40.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id="comp-meta-ra",
                        retry_after=retry_after,
                        herd_jitter_fraction=0.0,
                    )
                    checks.append(
                        relation(
                            policy,
                            "strong_retry_after_remains_authoritative",
                            (
                                comp_ra["decision"]["action"] == bare_ra.action
                                and comp_ra["decision"][
                                    "retry_after_floor_s"
                                ] == bare_ra.retry_after_floor_s
                                and math.isclose(
                                    comp_ra["decision"]["next_start_s"],
                                    bare_ra.next_start_s,
                                    rel_tol=0.0,
                                    abs_tol=1e-12,
                                )
                            ),
                            {
                                "retry_after_s": float(retry_after),
                                "bare": bare_ra.as_dict(),
                                "composed": comp_ra["decision"],
                            },
                        )
                    )

                    # 5) Budget exhaustion wins in all confidence states.
                    budget_rows = {}
                    budget_ok = True
                    for initial in ("H", "E", "B"):
                        c = Controller.create(policy=policy, state=initial)
                        row = c.observe_429(
                            start_s=50.0,
                            complete_s=50.01,
                            attempt_number=3,
                            retry_budget=3,
                            operation_id=f"comp-meta-budget-{initial}",
                            retry_after="1",
                            herd_jitter_fraction=0.0,
                        )
                        d = row["decision"]
                        budget_rows[initial] = d
                        budget_ok = budget_ok and (
                            d["action"] == "STOP_BUDGET"
                            and d["next_start_s"] is None
                            and d["budget_remaining_after_attempt"] == 0
                        )
                    checks.append(
                        relation(
                            policy,
                            "budget_stop_orthogonal_to_confidence",
                            budget_ok,
                            budget_rows,
                        )
                    )

                    # 6) Ambiguous non-idempotent authorization remains REOBSERVE.
                    reobserve_rows = {}
                    reobserve_ok = True
                    for initial in ("H", "E", "B"):
                        minimum = (
                            effective if initial in {"E", "B"} else base_period
                        )
                        d = decide(
                            status=None,
                            method="POST",
                            operation_state="unknown",
                            application_idempotency_contract=False,
                            attempt_number=1,
                            retry_budget=4,
                            operation_id=f"comp-meta-unknown-{initial}",
                            now_s=0.05,
                            previous_start_s=0.0,
                            minimum_period_s=minimum,
                            retry_after=None,
                            draft_ratelimit=None,
                            local_base_s=0.25,
                            local_cap_s=2.0,
                            herd_jitter_fraction=0.2,
                            now_datetime=dt.datetime(
                                2026, 10, 4, tzinfo=dt.timezone.utc
                            ),
                        )
                        reobserve_rows[initial] = d.as_dict()
                        reobserve_ok = reobserve_ok and (
                            d.action == "REOBSERVE"
                            and d.next_start_s is None
                        )
                    checks.append(
                        relation(
                            policy,
                            "reobserve_orthogonal_to_confidence",
                            reobserve_ok,
                            reobserve_rows,
                        )
                    )

                    # 7) The slow recovery floor is present after first success and
                    # relaxes to base cadence only after promotion to H.
                    promotion_rows, controller = promotion_sequence(policy)
                    first_row = promotion_rows[0]
                    final_row = promotion_rows[-1]
                    first_start = 100.0
                    final_complete = (
                        100.1
                        + policy.hysteresis.minimum_recovering_duration_s
                    )
                    final_start = final_complete - 0.1
                    checks.append(
                        relation(
                            policy,
                            "pacing_relaxes_only_after_healthy",
                            (
                                first_row["after_confidence"] == "E"
                                and math.isclose(
                                    first_row["next_observation_floor_s"],
                                    first_start + effective,
                                    rel_tol=0.0,
                                    abs_tol=1e-12,
                                )
                                and final_row["after_confidence"] == "H"
                                and math.isclose(
                                    final_row["next_observation_floor_s"],
                                    final_start + base_period,
                                    rel_tol=0.0,
                                    abs_tol=1e-12,
                                )
                                and controller.gate.failure_history_resets == 1
                            ),
                            {
                                "states": [
                                    row["after_confidence"]
                                    for row in promotion_rows
                                ],
                                "first_floor_s": first_row[
                                    "next_observation_floor_s"
                                ],
                                "healthy_floor_s": final_row[
                                    "next_observation_floor_s"
                                ],
                            },
                        )
                    )

                    # 8) Tightening only recovery-probe pacing cannot make the next
                    # provisional observation earlier.
                    stricter = CompositionPolicy(
                        hysteresis=Policy(
                            confirmation_successes_required=count,
                            minimum_recovering_duration_s=duration,
                        ),
                        base_minimum_period_s=base_period,
                        recovery_probe_period_s=recovery_period + 3.0,
                    )
                    stricter.validate()
                    c1 = Controller.create(policy=policy, state="B")
                    c2 = Controller.create(policy=stricter, state="B")
                    loose = c1.observe_success(
                        start_s=70.0,
                        complete_s=70.1,
                    )
                    strict = c2.observe_success(
                        start_s=70.0,
                        complete_s=70.1,
                    )
                    checks.append(
                        relation(
                            policy,
                            "stricter_recovery_period_cannot_start_earlier",
                            strict["next_observation_floor_s"]
                            >= loose["next_observation_floor_s"],
                            {
                                "base_floor_s": loose[
                                    "next_observation_floor_s"
                                ],
                                "strict_floor_s": strict[
                                    "next_observation_floor_s"
                                ],
                                "strict_recovery_probe_period_s": (
                                    stricter.recovery_probe_period_s
                                ),
                            },
                        )
                    )

    canonical = {
        "policies": policy_inputs,
        "relations": list(RELATIONS),
    }
    digest = hashlib.sha256(
        json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    failed = [row for row in checks if not row["pass"]]
    families: dict[str, int] = {}
    for row in checks:
        families[row["relation"]] = families.get(row["relation"], 0) + 1

    return {
        "schema": "http-429-composed-metamorphic-report/v1",
        "experiment_id": "NET-429-COMP-002",
        "classification": "deterministic_control_plane_metamorphic_lab_not_provider_behavior",
        "generator": {
            "id": "composed-metamorphic-kitten-swarm-v1",
            "deterministic": True,
            "policy_count": len(policy_inputs),
            "relation_checks": len(checks),
            "relation_families": families,
            "policy_axes": {
                "confirmation_successes_required": list(COUNTS),
                "minimum_recovering_duration_s": list(DURATIONS),
                "base_minimum_period_s": list(BASE_PERIODS),
                "recovery_probe_period_s": list(RECOVERY_PERIODS),
            },
            "generated_input_sha256": digest,
        },
        "summary": {
            "relation_checks": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        "checks": checks,
        "safety": {
            "network_access": False,
            "production_traffic": False,
            "operation_replay_authority": False,
        },
        "interpretation": {
            "pass_means": (
                "Scheduler and hysteresis composition preserved eight "
                "predeclared authority/timing relations across sixteen policies."
            ),
            "pass_does_not_mean": (
                "Any tested timing/count value is a production recommendation "
                "or that a provider exposes the modeled confidence state."
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
