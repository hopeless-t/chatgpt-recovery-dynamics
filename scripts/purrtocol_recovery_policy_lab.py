#!/usr/bin/env python3
"""Evaluate bounded recovery interventions without inventing a policy winner.

The lab reuses the connection-amplification model and asks which explicit
interventions restore the shared-capacity gate. Heterogeneous intervention
costs are intentionally not collapsed into one score.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import purrtocol_connection_amplification as amp

INPUT_SCHEMA = "purrtocol-recovery-policy-lab-input/v0"
OUTPUT_SCHEMA = "purrtocol-recovery-policy-lab/v0"
MAX_INTERVENTIONS = 32
POLICY_KEYS = {
    "fanout_connections_per_attempt",
    "failure_probability",
    "retry_multiplier",
    "connection_hold_seconds",
    "payload_bytes",
    "local_success_probability",
}
SCENARIO_KEYS = {
    "baseline_request_rate_rps",
    "shared_connection_capacity",
    "max_retry_depth",
}


class PolicyLabError(ValueError):
    pass


def require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyLabError(f"{field} must be an object")
    return value


def bounded_overrides(value: Any, allowed: set[str], field: str) -> dict[str, Any]:
    value = require_dict(value, field)
    unknown = set(value) - allowed
    if unknown:
        raise PolicyLabError(f"{field} contains unsupported keys: {sorted(unknown)}")
    return value


def model_one(
    scenario: dict[str, Any],
    policy: dict[str, Any],
    scenario_id: str,
) -> dict[str, Any]:
    doc = {
        "schema": amp.INPUT_SCHEMA,
        "scenario_id": scenario_id,
        "baseline_request_rate_rps": scenario["baseline_request_rate_rps"],
        "shared_connection_capacity": scenario["shared_connection_capacity"],
        "max_retry_depth": scenario["max_retry_depth"],
        "policies": [policy],
    }
    result = amp.build(doc)
    return result["policies"][0]


def compact_result(
    intervention_id: str,
    mechanism: str,
    policy_overrides: dict[str, Any],
    scenario_overrides: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "intervention_id": intervention_id,
        "mechanism": mechanism,
        "policy_overrides": policy_overrides,
        "scenario_overrides": scenario_overrides,
        "retry_branch_factor": row["retry_branch_factor"],
        "retry_shape": row["retry_shape"],
        "expected_attempt_multiplier": row["expected_attempt_multiplier"],
        "expected_concurrent_connections": row["expected_concurrent_connections"],
        "capacity_utilization": row["capacity_utilization"],
        "capacity_gate": row["connection_capacity_gate"],
        "payload_bytes": row["payload_bytes"],
        "local_success_probability": row["local_success_probability"],
    }


def build(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") != INPUT_SCHEMA:
        raise PolicyLabError(f"expected {INPUT_SCHEMA}")

    lab_id = str(doc.get("lab_id", "anonymous-policy-lab"))
    base_scenario = require_dict(doc.get("base_scenario"), "base_scenario")
    base_policy = require_dict(doc.get("base_policy"), "base_policy")
    for key in SCENARIO_KEYS:
        if key not in base_scenario:
            raise PolicyLabError(f"base_scenario missing {key}")
    if "policy_id" not in base_policy:
        raise PolicyLabError("base_policy missing policy_id")

    interventions = doc.get("interventions")
    if not isinstance(interventions, list) or not 1 <= len(interventions) <= MAX_INTERVENTIONS:
        raise PolicyLabError(f"interventions must contain 1..{MAX_INTERVENTIONS} entries")

    base_row = model_one(base_scenario, base_policy, f"{lab_id}:baseline")
    baseline = compact_result(
        "BASELINE",
        "no-intervention",
        {},
        {},
        base_row,
    )

    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for raw in interventions:
        if not isinstance(raw, dict):
            raise PolicyLabError("each intervention must be an object")
        intervention_id = raw.get("intervention_id")
        mechanism = raw.get("mechanism")
        if not isinstance(intervention_id, str) or not intervention_id.strip():
            raise PolicyLabError("intervention_id must be a non-empty string")
        intervention_id = intervention_id.strip()
        if intervention_id in ids:
            raise PolicyLabError("intervention_id values must be unique")
        ids.add(intervention_id)
        if not isinstance(mechanism, str) or not mechanism.strip():
            raise PolicyLabError("mechanism must be a non-empty string")

        policy_overrides = bounded_overrides(raw.get("policy_overrides", {}), POLICY_KEYS, "policy_overrides")
        scenario_overrides = bounded_overrides(raw.get("scenario_overrides", {}), SCENARIO_KEYS, "scenario_overrides")
        if not policy_overrides and not scenario_overrides:
            raise PolicyLabError("intervention must change at least one modeled field")

        scenario = copy.deepcopy(base_scenario)
        scenario.update(scenario_overrides)
        policy = copy.deepcopy(base_policy)
        policy.update(policy_overrides)
        policy["policy_id"] = intervention_id
        modeled = model_one(scenario, policy, f"{lab_id}:{intervention_id}")
        rows.append(compact_result(
            intervention_id,
            mechanism.strip(),
            policy_overrides,
            scenario_overrides,
            modeled,
        ))

    rows.sort(key=lambda row: row["intervention_id"])
    safe = [r["intervention_id"] for r in rows if r["capacity_gate"]["pass"]]
    unsafe = [r["intervention_id"] for r in rows if not r["capacity_gate"]["pass"]]

    return {
        "schema": OUTPUT_SCHEMA,
        "lab_id": lab_id,
        "evidence_status": "modeled_bounded_policy_lab",
        "selection_policy": "classify-capacity-safety-no-hidden-policy-winner",
        "baseline": baseline,
        "safe_interventions": safe,
        "unsafe_interventions": unsafe,
        "summary": {
            "interventions": len(rows),
            "safe": len(safe),
            "unsafe": len(unsafe),
        },
        "world_laws": {
            "capacity_gate_before_local_optimization": True,
            "heterogeneous_intervention_costs_not_scalarized": True,
            "safe_set_is_not_final_winner": True,
            "single_mitigation_may_be_insufficient": True,
            "modeled_policy_is_not_provider_topology": True,
        },
        "interventions": rows,
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
