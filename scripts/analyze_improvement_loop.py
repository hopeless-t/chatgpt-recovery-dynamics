#!/usr/bin/env python3
"""Analyze the repository improvement loop as a second-order control system."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "improvement_events.jsonl"
POLICY = ROOT / "data" / "meta_improvement_loop_policy.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds(a: dict[str, Any], b: dict[str, Any]) -> float:
    return (parse_time(b["wall_time_utc"]) - parse_time(a["wall_time_utc"])).total_seconds()


def median_or_none(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def first(rows: list[dict[str, Any]], record_type: str) -> dict[str, Any] | None:
    return next((row for row in rows if row["record_type"] == record_type), None)


def last_before(
    rows: list[dict[str, Any]],
    record_type: str,
    before: dict[str, Any],
) -> dict[str, Any] | None:
    candidates = [
        row
        for row in rows
        if row["record_type"] == record_type
        and parse_time(row["wall_time_utc"]) <= parse_time(before["wall_time_utc"])
    ]
    return candidates[-1] if candidates else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()

    events = read_jsonl(LEDGER)
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    by_cycle: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_cycle[event["cycle_id"]].append(event)

    cycles = []
    violations = []

    for cycle_id in sorted(by_cycle):
        rows = sorted(by_cycle[cycle_id], key=lambda row: row["seq"])
        start = first(rows, "cycle_start")
        observation = first(rows, "observation")
        verification = first(rows, "verification")
        promotion = first(rows, "promotion")
        end = first(rows, "cycle_end")

        if not all((start, observation, verification, promotion, end)):
            violations.append(f"{cycle_id}: incomplete lifecycle")
            continue

        change = last_before(rows, "change", verification)
        if change is None:
            violations.append(f"{cycle_id}: no change before verification")
            continue

        if parse_time(verification["wall_time_utc"]) > parse_time(promotion["wall_time_utc"]):
            violations.append(f"{cycle_id}: promotion preceded verification")

        promotion_censored = bool(
            promotion.get("details", {}).get("timing_censor_after_verification", False)
        )

        first_change = first(rows, "change")
        counts = Counter(row["record_type"] for row in rows)
        failed_observations = sum(
            1
            for row in rows
            if row["record_type"] == "observation"
            and row.get("details", {}).get("conclusion") == "failure"
        )
        observations_after_first_change = 0
        if first_change is not None:
            first_change_time = parse_time(first_change["wall_time_utc"])
            observations_after_first_change = sum(
                1
                for row in rows
                if row["record_type"] == "observation"
                and parse_time(row["wall_time_utc"]) > first_change_time
            )

        cycles.append(
            {
                "cycle_id": cycle_id,
                "target": start["target"],
                "duration_s": seconds(start, end),
                "duration_included_in_latency_aggregate": not promotion_censored,
                "observation_to_first_change_s": seconds(observation, first_change),
                "last_change_to_verification_s": seconds(change, verification),
                "verification_to_promotion_s": seconds(verification, promotion),
                "verification_to_promotion_included_in_latency_aggregate": not promotion_censored,
                "timing_censor_after_verification": promotion_censored,
                "record_counts": dict(counts),
                "failed_observations": failed_observations,
                "observations_after_first_change": observations_after_first_change,
                "multiple_changes": counts["change"] > 1,
                "verified_before_promotion": (
                    parse_time(verification["wall_time_utc"])
                    <= parse_time(promotion["wall_time_utc"])
                ),
            }
        )

    if not cycles:
        raise SystemExit("no complete improvement cycles")

    durations = [
        c["duration_s"]
        for c in cycles
        if c["duration_included_in_latency_aggregate"]
    ]
    observe_change = [c["observation_to_first_change_s"] for c in cycles]
    change_verify = [c["last_change_to_verification_s"] for c in cycles]
    verify_promote = [
        c["verification_to_promotion_s"]
        for c in cycles
        if c["verification_to_promotion_included_in_latency_aggregate"]
    ]

    workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))
    audit_files = [
        ROOT / "scripts" / "audit_repository_state.py",
        ROOT / "scripts" / "analyze_improvement_loop.py",
    ]
    observatory_python_bytes = sum(
        path.stat().st_size for path in audit_files if path.exists()
    )

    aggregate = {
        "completed_cycles": len(cycles),
        "median_cycle_duration_s": statistics.median(durations),
        "mean_cycle_duration_s": statistics.fmean(durations),
        "min_cycle_duration_s": min(durations),
        "max_cycle_duration_s": max(durations),
        "median_observation_to_first_change_s": statistics.median(observe_change),
        "median_last_change_to_verification_s": statistics.median(change_verify),
        "median_verification_to_promotion_s": statistics.median(verify_promote),
        "fraction_cycles_with_multiple_changes": (
            sum(c["multiple_changes"] for c in cycles) / len(cycles)
        ),
        "fraction_cycles_with_failed_observations": (
            sum(c["failed_observations"] > 0 for c in cycles) / len(cycles)
        ),
        "verified_before_promotion_ratio": (
            sum(c["verified_before_promotion"] for c in cycles) / len(cycles)
        ),
        "timing_censored_cycles": sum(
            c["timing_censor_after_verification"] for c in cycles
        ),
        "latency_aggregate_cycle_count": len(durations),
        "promotion_latency_sample_count": len(verify_promote),
    }

    signals = []
    diag_rhs = 2 * (
        aggregate["median_last_change_to_verification_s"]
        + aggregate["median_verification_to_promotion_s"]
    )
    if aggregate["median_observation_to_first_change_s"] > diag_rhs:
        signals.append(
            {
                "rule": "diagnosis_dominates",
                "status": "TRIGGERED",
                "evidence": {
                    "median_observation_to_first_change_s": aggregate[
                        "median_observation_to_first_change_s"
                    ],
                    "two_x_downstream_median_s": diag_rhs,
                },
                "recommendation": (
                    "Improve critic localization/task routing before reducing verification."
                ),
            }
        )

    if aggregate["median_last_change_to_verification_s"] > 180:
        signals.append(
            {
                "rule": "verification_dominates",
                "status": "TRIGGERED",
                "evidence": {
                    "median_last_change_to_verification_s": aggregate[
                        "median_last_change_to_verification_s"
                    ]
                },
                "recommendation": (
                    "Investigate parallelism/caching/staging without weakening merge gates."
                ),
            }
        )

    if aggregate["median_verification_to_promotion_s"] > 180:
        signals.append(
            {
                "rule": "promotion_lag_dominates",
                "status": "TRIGGERED",
                "evidence": {
                    "median_verification_to_promotion_s": aggregate[
                        "median_verification_to_promotion_s"
                    ]
                },
                "recommendation": (
                    "Reduce promotion friction only after required verification completes."
                ),
            }
        )

    if aggregate["fraction_cycles_with_multiple_changes"] >= 0.25:
        signals.append(
            {
                "rule": "rework_signal",
                "status": "TRIGGERED",
                "evidence": {
                    "fraction_cycles_with_multiple_changes": aggregate[
                        "fraction_cycles_with_multiple_changes"
                    ]
                },
                "recommendation": (
                    "Add cheaper intermediate validation near the failure source."
                ),
            }
        )

    budget = policy["soft_design_budgets"]
    observer_warning = (
        len(workflows) > budget["github_workflows_warning_above"]
        or observatory_python_bytes
        > budget["observatory_python_bytes_warning_above"]
    )
    if observer_warning:
        signals.append(
            {
                "rule": "observer_growth_warning",
                "status": "TRIGGERED",
                "evidence": {
                    "github_workflows": len(workflows),
                    "observatory_python_bytes": observatory_python_bytes,
                },
                "recommendation": (
                    "Audit duplicate measurement/projection cost before adding more observers."
                ),
            }
        )

    if aggregate["verified_before_promotion_ratio"] != 1.0:
        violations.append("not every promotion had prior verification")

    result = {
        "schema": "meta-improvement-loop-report/v1",
        "classification": "repository_process_telemetry_not_quality_score",
        "cycles": cycles,
        "aggregate": aggregate,
        "observer_footprint": {
            "github_workflows": len(workflows),
            "observatory_python_bytes": observatory_python_bytes,
        },
        "triggered_tuning_signals": signals,
        "violations": violations,
        "anti_goodhart": policy["anti_goodhart"],
        "interpretation": {
            "single_overall_score": "FORBIDDEN",
            "speed": "diagnostic only",
            "timing_censoring": (
                "Explicitly marked external orchestration pauses remain visible in raw cycle rows "
                "but are excluded from aggregate cycle/promotion latency statistics."
            ),
            "current_tuning_direction": (
                "Use triggered signals to choose bounded improvements while preserving immutable guardrails."
            ),
        },
    }

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")

    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
