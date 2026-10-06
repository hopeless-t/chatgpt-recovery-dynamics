#!/usr/bin/env python3
"""Bounded model of failure-triggered connection amplification.

This model separates payload size from recovery-time connection pressure. It is
not a claim about any provider's exact internal topology. Every retry cascade is
explicitly capped by max_retry_depth; no infinite-series result is used as an
operational truth.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

INPUT_SCHEMA = "purrtocol-connection-amplification-input/v0"
OUTPUT_SCHEMA = "purrtocol-connection-amplification/v0"
MAX_POLICIES = 32
MAX_RETRY_DEPTH = 16


class ModelError(ValueError):
    pass


def positive(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ModelError(f"{field} must be positive numeric")
    return float(value)


def nonnegative(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ModelError(f"{field} must be non-negative numeric")
    return float(value)


def probability(value: Any, field: str) -> float:
    value = nonnegative(value, field)
    if value > 1:
        raise ModelError(f"{field} must be within [0,1]")
    return value


def positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ModelError(f"{field} must be a positive integer")
    return value


def normalize_policy(row: dict[str, Any]) -> dict[str, Any]:
    policy_id = row.get("policy_id")
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise ModelError("policy_id must be a non-empty string")
    return {
        "policy_id": policy_id.strip(),
        "fanout_connections_per_attempt": positive(
            row.get("fanout_connections_per_attempt"), "fanout_connections_per_attempt"
        ),
        "failure_probability": probability(row.get("failure_probability"), "failure_probability"),
        "retry_multiplier": nonnegative(row.get("retry_multiplier"), "retry_multiplier"),
        "connection_hold_seconds": positive(row.get("connection_hold_seconds"), "connection_hold_seconds"),
        "payload_bytes": positive_int(row.get("payload_bytes"), "payload_bytes"),
        "local_success_probability": probability(
            row.get("local_success_probability"), "local_success_probability"
        ),
    }


def evaluate(policy: dict[str, Any], baseline_rate: float, capacity: float, depth: int) -> dict[str, Any]:
    branch_factor = policy["failure_probability"] * policy["retry_multiplier"]
    terms = [branch_factor ** k for k in range(depth + 1)]
    attempt_multiplier = sum(terms)
    attempt_rate = baseline_rate * attempt_multiplier
    connection_rate = attempt_rate * policy["fanout_connections_per_attempt"]
    concurrent_connections = connection_rate * policy["connection_hold_seconds"]
    utilization = concurrent_connections / capacity
    capacity_pass = concurrent_connections <= capacity

    return {
        **policy,
        "retry_branch_factor": round(branch_factor, 9),
        "retry_shape": "NON_DECAYING_BOUNDED" if branch_factor >= 1 else "DECAYING_BOUNDED",
        "retry_terms": [round(v, 9) for v in terms],
        "expected_attempt_multiplier": round(attempt_multiplier, 9),
        "expected_attempt_rate_rps": round(attempt_rate, 9),
        "expected_connection_open_rate_per_second": round(connection_rate, 9),
        "expected_concurrent_connections": round(concurrent_connections, 9),
        "capacity_utilization": round(utilization, 9),
        "connection_capacity_gate": {
            "pass": capacity_pass,
            "status": "WITHIN_CAPACITY" if capacity_pass else "CAPACITY_EXCEEDED",
            "margin_connections": round(capacity - concurrent_connections, 9),
        },
    }


def build(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") != INPUT_SCHEMA:
        raise ModelError(f"expected {INPUT_SCHEMA}")
    scenario_id = str(doc.get("scenario_id", "anonymous-scenario"))
    baseline_rate = positive(doc.get("baseline_request_rate_rps"), "baseline_request_rate_rps")
    capacity = positive(doc.get("shared_connection_capacity"), "shared_connection_capacity")
    depth = doc.get("max_retry_depth")
    if isinstance(depth, bool) or not isinstance(depth, int) or not 0 <= depth <= MAX_RETRY_DEPTH:
        raise ModelError(f"max_retry_depth must be an integer within [0,{MAX_RETRY_DEPTH}]")
    rows = doc.get("policies")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_POLICIES:
        raise ModelError(f"policies must contain 1..{MAX_POLICIES} entries")
    policies = [normalize_policy(row) for row in rows]
    ids = [row["policy_id"] for row in policies]
    if len(ids) != len(set(ids)):
        raise ModelError("policy_id values must be unique")

    evaluated = [evaluate(row, baseline_rate, capacity, depth) for row in policies]
    evaluated.sort(key=lambda row: row["policy_id"])
    safe = [row["policy_id"] for row in evaluated if row["connection_capacity_gate"]["pass"]]
    exceeded = [row["policy_id"] for row in evaluated if not row["connection_capacity_gate"]["pass"]]

    return {
        "schema": OUTPUT_SCHEMA,
        "scenario_id": scenario_id,
        "evidence_status": "modeled_bounded_scenario",
        "scenario": {
            "baseline_request_rate_rps": round(baseline_rate, 9),
            "shared_connection_capacity": round(capacity, 9),
            "max_retry_depth": depth,
        },
        "model_contract": {
            "finite_retry_depth_only": True,
            "infinite_series_used": False,
            "payload_bytes_diagnostic_only": True,
            "local_success_probability_diagnostic_only": True,
            "exact_provider_topology_claimed": False,
        },
        "world_laws": {
            "smaller_payload_does_not_imply_safer_recovery": True,
            "higher_local_success_does_not_imply_global_safety": True,
            "recovery_work_can_consume_shared_capacity": True,
            "capacity_gate_precedes_local_optimization": True,
        },
        "summary": {
            "policies": len(evaluated),
            "within_capacity": len(safe),
            "capacity_exceeded": len(exceeded),
        },
        "within_capacity": safe,
        "capacity_exceeded": exceeded,
        "policies": evaluated,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = build(doc)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
