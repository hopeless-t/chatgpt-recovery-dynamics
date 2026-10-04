#!/usr/bin/env python3
"""NET-429-COMP-002: metamorphic swarm for scheduler × recovery confidence.

No network traffic is generated.

The swarm varies both scheduler pacing and hysteresis policy while checking
relations that must hold regardless of fixture values. The core ownership rule
is asymmetric and intentionally preserved:

- scheduler owns retry authorization, timing floors, identity and budget;
- hysteresis owns B/E/H recovery confidence;
- confidence may add conservative pacing while B/E;
- confidence may never create replay authority or shorten scheduler floors.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
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


COUNTS = (2, 3, 4)
DURATIONS = (0.0, 5.0)
BASE_PERIODS = (0.5, 1.0)
PROBE_PERIODS = (1.0, 5.0, 10.0)
SHIFT_S = 123.0


def relation(
    *,
    policy: CompositionPolicy,
    relation_name: str,
    passed: bool,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "policy": {
            "hysteresis": asdict(policy.hysteresis),
            "base_minimum_period_s": policy.base_minimum_period_s,
            "recovery_probe_period_s": policy.recovery_probe_period_s,
        },
        "relation": relation_name,
        "pass": bool(passed),
        "details": details,
    }


def exact_success_times(count: int, duration: float, *, base: float = 100.0) -> list[float]:
    return [
        base + duration * index / (count - 1)
        for index in range(count)
    ]


def unknown_post_decision(*, state: str, policy: CompositionPolicy, suffix: str) -> dict[str, Any]:
    minimum = (
        max(policy.base_minimum_period_s, policy.recovery_probe_period_s)
        if state in {"B", "E"}
        else policy.base_minimum_period_s
    )
    decision = decide(
        status=None,
        method="POST",
        operation_state="unknown",
        application_idempotency_contract=False,
        attempt_number=1,
        retry_budget=4,
        operation_id=f"comp-swarm-unknown-{suffix}-{state}",
        now_s=0.05,
        previous_start_s=0.0,
        minimum_period_s=minimum,
        retry_after=None,
        draft_ratelimit=None,
        local_base_s=0.25,
        local_cap_s=2.0,
        herd_jitter_fraction=0.0,
        now_datetime=dt.datetime(2026, 10, 4, tzinfo=dt.timezone.utc),
    )
    return decision.as_dict()


def build() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    generated_inputs: list[dict[str, Any]] = []

    for count in COUNTS:
        for duration in DURATIONS:
            for base_period in BASE_PERIODS:
                for probe_period in PROBE_PERIODS:
                    hysteresis = Policy(
                        confirmation_successes_required=count,
                        minimum_recovering_duration_s=duration,
                    )
                    policy = CompositionPolicy(
                        hysteresis=hysteresis,
                        base_minimum_period_s=base_period,
                        recovery_probe_period_s=probe_period,
                    )
                    policy.validate()
                    tag = f"c{count}-d{duration:g}-b{base_period:g}-p{probe_period:g}"
                    generated_inputs.append(
                        {
                            "tag": tag,
                            "confirmation_successes_required": count,
                            "minimum_recovering_duration_s": duration,
                            "base_minimum_period_s": base_period,
                            "recovery_probe_period_s": probe_period,
                        }
                    )

                    # 1) Blocked confidence may only make the next retry later,
                    # never earlier than the bare scheduler with the base floor.
                    bare_b = bare_429_decision(
                        start_s=10.0,
                        complete_s=10.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-b-{tag}",
                        minimum_period_s=base_period,
                        herd_jitter_fraction=0.0,
                    )
                    c = Controller.create(policy=policy, state="B")
                    comp_b = c.observe_429(
                        start_s=10.0,
                        complete_s=10.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-b-{tag}",
                        herd_jitter_fraction=0.0,
                    )
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="blocked_confidence_never_retries_earlier",
                            passed=(
                                comp_b["decision"]["action"] == bare_b.action
                                and comp_b["decision"]["next_start_s"]
                                >= bare_b.next_start_s
                                and comp_b["effective_minimum_period_s"]
                                >= base_period
                            ),
                            details={"bare": bare_b.as_dict(), "composed": comp_b},
                        )
                    )

                    # 2) Recovering confidence is also conservative. The 429
                    # first reclassifies E -> B, then scheduler timing is applied.
                    bare_e = bare_429_decision(
                        start_s=20.0,
                        complete_s=20.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-e-{tag}",
                        minimum_period_s=base_period,
                        herd_jitter_fraction=0.0,
                    )
                    c = Controller.create(policy=policy, state="E")
                    comp_e = c.observe_429(
                        start_s=20.0,
                        complete_s=20.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-e-{tag}",
                        herd_jitter_fraction=0.0,
                    )
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="recovering_confidence_never_retries_earlier",
                            passed=(
                                comp_e["before_confidence"] == "E"
                                and comp_e["after_confidence"] == "B"
                                and comp_e["decision"]["action"] == bare_e.action
                                and comp_e["decision"]["next_start_s"]
                                >= bare_e.next_start_s
                            ),
                            details={"bare": bare_e.as_dict(), "composed": comp_e},
                        )
                    )

                    # 3) A sufficiently stronger Retry-After floor remains
                    # authoritative and gives the same next-start time.
                    retry_after_s = max(base_period, probe_period) + 20.0
                    bare_ra = bare_429_decision(
                        start_s=30.0,
                        complete_s=30.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-ra-{tag}",
                        minimum_period_s=base_period,
                        retry_after=str(int(retry_after_s)),
                        herd_jitter_fraction=0.0,
                    )
                    c = Controller.create(policy=policy, state="E")
                    comp_ra = c.observe_429(
                        start_s=30.0,
                        complete_s=30.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-ra-{tag}",
                        retry_after=str(int(retry_after_s)),
                        herd_jitter_fraction=0.0,
                    )
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="strong_retry_after_remains_authoritative",
                            passed=(
                                comp_ra["decision"]["action"] == bare_ra.action
                                and comp_ra["decision"]["retry_after_floor_s"]
                                == bare_ra.retry_after_floor_s
                                and comp_ra["decision"]["next_start_s"]
                                == bare_ra.next_start_s
                            ),
                            details={"bare": bare_ra.as_dict(), "composed": comp_ra},
                        )
                    )

                    # 4) Confidence cannot override an exhausted retry budget.
                    budget_rows: dict[str, Any] = {}
                    budget_ok = True
                    for state in ("H", "E", "B"):
                        c = Controller.create(policy=policy, state=state)
                        row = c.observe_429(
                            start_s=40.0,
                            complete_s=40.01,
                            attempt_number=3,
                            retry_budget=3,
                            operation_id=f"comp-swarm-budget-{tag}-{state}",
                            retry_after="2",
                            herd_jitter_fraction=0.0,
                        )
                        budget_rows[state] = row
                        budget_ok = budget_ok and (
                            row["decision"]["action"] == "STOP_BUDGET"
                            and row["decision"]["next_start_s"] is None
                            and row["decision"]["budget_remaining_after_attempt"] == 0
                        )
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="confidence_never_overrides_budget_stop",
                            passed=budget_ok,
                            details=budget_rows,
                        )
                    )

                    # 5) Confidence cannot mint replay authority for an
                    # ambiguous non-idempotent operation.
                    reobserve_rows = {
                        state: unknown_post_decision(state=state, policy=policy, suffix=tag)
                        for state in ("H", "E", "B")
                    }
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="confidence_never_overrides_reobserve",
                            passed=all(
                                row["action"] == "REOBSERVE"
                                and row["next_start_s"] is None
                                for row in reobserve_rows.values()
                            ),
                            details=reobserve_rows,
                        )
                    )

                    # 6) Translating the entire scheduler clock preserves the
                    # decision and translates the next-start time equally.
                    c1 = Controller.create(policy=policy, state="B")
                    t1 = c1.observe_429(
                        start_s=50.0,
                        complete_s=50.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-shift-{tag}",
                        herd_jitter_fraction=0.0,
                    )
                    c2 = Controller.create(policy=policy, state="B")
                    t2 = c2.observe_429(
                        start_s=50.0 + SHIFT_S,
                        complete_s=50.05 + SHIFT_S,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-shift-{tag}",
                        herd_jitter_fraction=0.0,
                    )
                    translated = (
                        t2["decision"]["next_start_s"]
                        - t1["decision"]["next_start_s"]
                    )
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="time_translation_preserves_composition_semantics",
                            passed=(
                                t1["decision"]["action"] == t2["decision"]["action"]
                                and t1["after_confidence"] == t2["after_confidence"]
                                and abs(translated - SHIFT_S) < 1e-9
                            ),
                            details={"base": t1, "shifted": t2, "observed_shift_s": translated},
                        )
                    )

                    # 7) Raising only the recovery probe period cannot produce
                    # an earlier next retry.
                    stronger_probe_policy = CompositionPolicy(
                        hysteresis=hysteresis,
                        base_minimum_period_s=base_period,
                        recovery_probe_period_s=probe_period + 2.0,
                    )
                    c_lo = Controller.create(policy=policy, state="B")
                    lo = c_lo.observe_429(
                        start_s=60.0,
                        complete_s=60.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-probe-{tag}",
                        herd_jitter_fraction=0.0,
                    )
                    c_hi = Controller.create(policy=stronger_probe_policy, state="B")
                    hi = c_hi.observe_429(
                        start_s=60.0,
                        complete_s=60.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-probe-{tag}",
                        herd_jitter_fraction=0.0,
                    )
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="stronger_probe_floor_cannot_retry_earlier",
                            passed=(
                                hi["decision"]["action"] == lo["decision"]["action"]
                                and hi["decision"]["next_start_s"]
                                >= lo["decision"]["next_start_s"]
                            ),
                            details={"base": lo, "stronger_probe": hi},
                        )
                    )

                    # 8) Raising only the base scheduler floor cannot produce
                    # an earlier next retry.
                    stronger_base_policy = CompositionPolicy(
                        hysteresis=hysteresis,
                        base_minimum_period_s=base_period + 2.0,
                        recovery_probe_period_s=probe_period,
                    )
                    c_lo = Controller.create(policy=policy, state="B")
                    lo = c_lo.observe_429(
                        start_s=70.0,
                        complete_s=70.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-base-{tag}",
                        herd_jitter_fraction=0.0,
                    )
                    c_hi = Controller.create(policy=stronger_base_policy, state="B")
                    hi = c_hi.observe_429(
                        start_s=70.0,
                        complete_s=70.05,
                        attempt_number=1,
                        retry_budget=6,
                        operation_id=f"comp-swarm-base-{tag}",
                        herd_jitter_fraction=0.0,
                    )
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="stronger_base_floor_cannot_retry_earlier",
                            passed=(
                                hi["decision"]["action"] == lo["decision"]["action"]
                                and hi["decision"]["next_start_s"]
                                >= lo["decision"]["next_start_s"]
                            ),
                            details={"base": lo, "stronger_base": hi},
                        )
                    )

                    # 9) Exact count+duration is the first point at which the
                    # confidence plane may relax from E to H. Prior successes
                    # retain the recovery pacing floor.
                    c = Controller.create(policy=policy, state="B")
                    times = exact_success_times(count, duration)
                    success_rows: list[dict[str, Any]] = []
                    for index, complete_s in enumerate(times):
                        row = c.observe_success(
                            start_s=complete_s - 0.1,
                            complete_s=complete_s,
                        )
                        success_rows.append(row)
                    before_final = success_rows[:-1]
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="pacing_relaxes_only_at_healthy_threshold",
                            passed=(
                                all(row["after_confidence"] == "E" for row in before_final)
                                and all(
                                    row["effective_minimum_period_s"]
                                    == max(base_period, probe_period)
                                    for row in before_final
                                )
                                and success_rows[-1]["after_confidence"] == "H"
                                and success_rows[-1]["effective_minimum_period_s"]
                                == base_period
                                and success_rows[-1]["transition"]["failure_history_reset"]
                                is True
                            ),
                            details={"successes": success_rows},
                        )
                    )

                    # 10) A stricter confidence policy cannot relax pacing at
                    # the same event boundary where the base policy becomes H.
                    strict_policy = CompositionPolicy(
                        hysteresis=Policy(
                            confirmation_successes_required=count + 1,
                            minimum_recovering_duration_s=duration,
                        ),
                        base_minimum_period_s=base_period,
                        recovery_probe_period_s=probe_period,
                    )
                    strict = Controller.create(policy=strict_policy, state="B")
                    strict_rows = [
                        strict.observe_success(
                            start_s=complete_s - 0.1,
                            complete_s=complete_s,
                        )
                        for complete_s in times
                    ]
                    checks.append(
                        relation(
                            policy=policy,
                            relation_name="stricter_confidence_cannot_relax_pacing_earlier",
                            passed=(
                                success_rows[-1]["after_confidence"] == "H"
                                and strict_rows[-1]["after_confidence"] == "E"
                                and strict_rows[-1]["effective_minimum_period_s"]
                                == max(base_period, probe_period)
                                and strict_rows[-1]["transition"]["failure_history_reset"]
                                is False
                            ),
                            details={"base": success_rows, "stricter": strict_rows},
                        )
                    )

    payload = json.dumps(
        generated_inputs,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()

    families: dict[str, int] = {}
    for row in checks:
        families[row["relation"]] = families.get(row["relation"], 0) + 1
    failed = [row for row in checks if not row["pass"]]

    return {
        "schema": "http-429-recovery-composition-metamorphic-report/v1",
        "experiment_id": "NET-429-COMP-002",
        "classification": "deterministic_composition_metamorphic_lab_not_provider_behavior",
        "generator": {
            "id": "scheduler-confidence-metamorphic-kitten-swarm-v1",
            "deterministic": True,
            "policy_count": len(generated_inputs),
            "confirmation_counts": list(COUNTS),
            "minimum_recovering_durations_s": list(DURATIONS),
            "base_minimum_periods_s": list(BASE_PERIODS),
            "recovery_probe_periods_s": list(PROBE_PERIODS),
            "relation_checks": len(checks),
            "relation_families": families,
            "generated_input_sha256": digest,
        },
        "summary": {
            "relation_checks": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        "authority_boundary": {
            "scheduler_owns_retry_authorization": True,
            "hysteresis_owns_recovery_confidence": True,
            "confidence_can_create_replay_authority": False,
            "confidence_can_shorten_scheduler_floor": False,
        },
        "safety": {
            "network_access": False,
            "production_traffic": False,
            "operation_replay_authority": False,
        },
        "checks": checks,
        "interpretation": {
            "pass_means": (
                "Generated policy transformations preserved scheduler authority "
                "and conservative recovery-confidence pacing relations."
            ),
            "pass_does_not_mean": (
                "The tested fixture values are production recommendations, that "
                "providers expose these states, or that all possible compositions "
                "have been verified."
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
