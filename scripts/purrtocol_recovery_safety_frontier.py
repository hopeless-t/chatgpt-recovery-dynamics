#!/usr/bin/env python3
"""Enumerate bounded recovery-policy packages and expose a safety frontier.

A frontier entry is inclusion-minimal: the package is within the modeled shared
connection capacity, while no proper non-empty subset of that package is safe.
This is deliberately not a cheapest-policy claim. Heterogeneous intervention
costs are not scalarized.
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
from pathlib import Path
from typing import Any

import purrtocol_recovery_policy_lab as lab

INPUT_SCHEMA = "purrtocol-recovery-safety-frontier-input/v0"
OUTPUT_SCHEMA = "purrtocol-recovery-safety-frontier/v0"
MAX_LEVERS = 12
MAX_PACKAGE_SIZE = 6


class SafetyFrontierError(ValueError):
    pass


def require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SafetyFrontierError(f"{field} must be an object")
    return value


def normalize_lever(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SafetyFrontierError("each lever must be an object")
    lever_id = raw.get("lever_id")
    mechanism = raw.get("mechanism")
    if not isinstance(lever_id, str) or not lever_id.strip():
        raise SafetyFrontierError("lever_id must be a non-empty string")
    if not isinstance(mechanism, str) or not mechanism.strip():
        raise SafetyFrontierError("mechanism must be a non-empty string")
    policy_overrides = lab.bounded_overrides(
        raw.get("policy_overrides", {}), lab.POLICY_KEYS, "policy_overrides"
    )
    scenario_overrides = lab.bounded_overrides(
        raw.get("scenario_overrides", {}), lab.SCENARIO_KEYS, "scenario_overrides"
    )
    if not policy_overrides and not scenario_overrides:
        raise SafetyFrontierError("lever must change at least one modeled field")
    return {
        "lever_id": lever_id.strip(),
        "mechanism": mechanism.strip(),
        "policy_overrides": policy_overrides,
        "scenario_overrides": scenario_overrides,
    }


def merge_overrides(levers: tuple[dict[str, Any], ...], field: str) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    owner: dict[str, str] = {}
    for lever in levers:
        for key, value in lever[field].items():
            if key in merged:
                raise SafetyFrontierError(
                    f"package contains conflicting ownership for {field}.{key}: "
                    f"{owner[key]} and {lever['lever_id']}"
                )
            merged[key] = value
            owner[key] = lever["lever_id"]
    return merged


def evaluate_package(
    frontier_id: str,
    base_scenario: dict[str, Any],
    base_policy: dict[str, Any],
    levers: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    lever_ids = tuple(sorted(lever["lever_id"] for lever in levers))
    mechanisms = sorted(lever["mechanism"] for lever in levers)
    policy_overrides = merge_overrides(levers, "policy_overrides")
    scenario_overrides = merge_overrides(levers, "scenario_overrides")

    scenario = copy.deepcopy(base_scenario)
    scenario.update(scenario_overrides)
    policy = copy.deepcopy(base_policy)
    policy.update(policy_overrides)
    package_id = "+".join(lever_ids)
    policy["policy_id"] = package_id
    row = lab.model_one(scenario, policy, f"{frontier_id}:{package_id}")

    return {
        "package_id": package_id,
        "lever_ids": list(lever_ids),
        "mechanisms": mechanisms,
        "package_size": len(lever_ids),
        "policy_overrides": policy_overrides,
        "scenario_overrides": scenario_overrides,
        "retry_branch_factor": row["retry_branch_factor"],
        "retry_shape": row["retry_shape"],
        "expected_attempt_multiplier": row["expected_attempt_multiplier"],
        "expected_concurrent_connections": row["expected_concurrent_connections"],
        "capacity_utilization": row["capacity_utilization"],
        "capacity_gate": row["connection_capacity_gate"],
    }


def build(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") != INPUT_SCHEMA:
        raise SafetyFrontierError(f"expected {INPUT_SCHEMA}")

    frontier_id = str(doc.get("frontier_id", "anonymous-safety-frontier"))
    base_scenario = require_dict(doc.get("base_scenario"), "base_scenario")
    base_policy = require_dict(doc.get("base_policy"), "base_policy")
    for key in lab.SCENARIO_KEYS:
        if key not in base_scenario:
            raise SafetyFrontierError(f"base_scenario missing {key}")
    if "policy_id" not in base_policy:
        raise SafetyFrontierError("base_policy missing policy_id")

    raw_levers = doc.get("levers")
    if not isinstance(raw_levers, list) or not 1 <= len(raw_levers) <= MAX_LEVERS:
        raise SafetyFrontierError(f"levers must contain 1..{MAX_LEVERS} entries")
    levers = [normalize_lever(raw) for raw in raw_levers]
    ids = [lever["lever_id"] for lever in levers]
    if len(ids) != len(set(ids)):
        raise SafetyFrontierError("lever_id values must be unique")
    levers.sort(key=lambda lever: lever["lever_id"])

    max_package_size = doc.get("max_package_size", min(2, len(levers)))
    if (
        isinstance(max_package_size, bool)
        or not isinstance(max_package_size, int)
        or not 1 <= max_package_size <= min(MAX_PACKAGE_SIZE, len(levers))
    ):
        raise SafetyFrontierError(
            f"max_package_size must be an integer within [1,{min(MAX_PACKAGE_SIZE, len(levers))}]"
        )

    baseline_row = lab.model_one(base_scenario, base_policy, f"{frontier_id}:baseline")
    baseline = {
        "expected_concurrent_connections": baseline_row["expected_concurrent_connections"],
        "capacity_utilization": baseline_row["capacity_utilization"],
        "capacity_gate": baseline_row["connection_capacity_gate"],
    }

    packages: list[dict[str, Any]] = []
    for size in range(1, max_package_size + 1):
        for combo in itertools.combinations(levers, size):
            packages.append(evaluate_package(frontier_id, base_scenario, base_policy, combo))
    packages.sort(key=lambda row: (row["package_size"], row["package_id"]))

    safe_ids = {
        tuple(row["lever_ids"])
        for row in packages
        if row["capacity_gate"]["pass"]
    }
    minimal_safe: list[str] = []
    complementarity: list[str] = []
    for row in packages:
        if not row["capacity_gate"]["pass"]:
            continue
        lever_tuple = tuple(row["lever_ids"])
        has_safe_proper_subset = False
        for subset_size in range(1, len(lever_tuple)):
            if any(tuple(subset) in safe_ids for subset in itertools.combinations(lever_tuple, subset_size)):
                has_safe_proper_subset = True
                break
        if not has_safe_proper_subset:
            minimal_safe.append(row["package_id"])
        if len(lever_tuple) > 1 and all((lever_id,) not in safe_ids for lever_id in lever_tuple):
            complementarity.append(row["package_id"])

    safe_packages = [row["package_id"] for row in packages if row["capacity_gate"]["pass"]]
    unsafe_packages = [row["package_id"] for row in packages if not row["capacity_gate"]["pass"]]

    return {
        "schema": OUTPUT_SCHEMA,
        "frontier_id": frontier_id,
        "evidence_status": "modeled_bounded_safety_frontier",
        "selection_policy": "inclusion-minimal-capacity-safe-packages-no-cost-scalarization",
        "baseline": baseline,
        "levers": levers,
        "max_package_size": max_package_size,
        "minimal_safe_packages": minimal_safe,
        "complementarity_packages": complementarity,
        "safe_packages": safe_packages,
        "unsafe_packages": unsafe_packages,
        "summary": {
            "levers": len(levers),
            "packages_evaluated": len(packages),
            "safe_packages": len(safe_packages),
            "unsafe_packages": len(unsafe_packages),
            "minimal_safe_packages": len(minimal_safe),
            "complementarity_packages": len(complementarity),
        },
        "world_laws": {
            "inclusion_minimal_does_not_mean_cheapest": True,
            "heterogeneous_intervention_costs_not_scalarized": True,
            "unsafe_singletons_can_form_safe_packages": True,
            "conflicting_override_ownership_fails_closed": True,
            "frontier_is_modeled_not_provider_topology": True,
            "capacity_gate_precedes_policy_preference": True,
        },
        "packages": packages,
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
