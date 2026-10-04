#!/usr/bin/env python3
"""Audit phase ordering in the append-only RIL ledger.

This is an observation-only semantic audit. It preserves raw timestamps and raw
signed observation->first-change intervals, but separates cycles where a change
was intentionally made before the first new artifact observation. Those cycles
must not be interpreted as negative diagnosis latency.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "improvement_events.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def first(rows: list[dict[str, Any]], record_type: str) -> dict[str, Any] | None:
    return next((row for row in rows if row["record_type"] == record_type), None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()

    by_cycle: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in read_jsonl(LEDGER):
        by_cycle[event["cycle_id"]].append(event)

    cycles: list[dict[str, Any]] = []
    applicable_values: list[float] = []
    change_before_observation_ids: list[str] = []
    incomplete_ids: list[str] = []

    for cycle_id in sorted(by_cycle):
        rows = sorted(by_cycle[cycle_id], key=lambda row: row["seq"])
        observation = first(rows, "observation")
        change = first(rows, "change")
        if observation is None or change is None:
            incomplete_ids.append(cycle_id)
            continue

        raw_s = (
            parse_time(change["wall_time_utc"])
            - parse_time(observation["wall_time_utc"])
        ).total_seconds()

        if raw_s >= 0:
            phase_order = "OBSERVATION_BEFORE_OR_AT_FIRST_CHANGE"
            applicable = True
            applicable_values.append(raw_s)
        else:
            phase_order = "CHANGE_BEFORE_FIRST_OBSERVATION"
            applicable = False
            change_before_observation_ids.append(cycle_id)

        cycles.append(
            {
                "cycle_id": cycle_id,
                "first_observation_utc": observation["wall_time_utc"],
                "first_change_utc": change["wall_time_utc"],
                "raw_observation_to_first_change_s": raw_s,
                "phase_order": phase_order,
                "diagnosis_latency_applicable": applicable,
                "included_in_diagnosis_latency_aggregate": applicable,
            }
        )

    report = {
        "schema": "meta-phase-semantics-audit/v1",
        "classification": "raw_timestamp_preserving_phase_semantics_audit",
        "cycles": cycles,
        "aggregate": {
            "classified_cycle_count": len(cycles),
            "diagnosis_latency_sample_count": len(applicable_values),
            "change_before_first_observation_count": len(
                change_before_observation_ids
            ),
            "change_before_first_observation_cycle_ids": (
                change_before_observation_ids
            ),
            "median_applicable_observation_to_first_change_s": (
                statistics.median(applicable_values)
                if applicable_values
                else None
            ),
            "min_applicable_observation_to_first_change_s": (
                min(applicable_values) if applicable_values else None
            ),
            "incomplete_phase_cycle_ids": incomplete_ids,
        },
        "interpretation": {
            "negative_raw_interval_means": (
                "the first recorded change preceded the first new artifact "
                "observation; it is not a negative elapsed diagnosis time"
            ),
            "raw_timestamps_modified": False,
            "negative_intervals_clamped": False,
            "negative_intervals_absolute_valued": False,
            "recommended_analyzer_semantics": (
                "preserve the signed raw interval per cycle, mark diagnosis "
                "latency not applicable for CHANGE_BEFORE_FIRST_OBSERVATION, "
                "and exclude those cycles from diagnosis-latency aggregates"
            ),
        },
        "authority": {
            "changes_existing_analyzer": False,
            "changes_raw_ledger": False,
            "changes_frozen_critic_router_evaluation": False,
        },
    }

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
