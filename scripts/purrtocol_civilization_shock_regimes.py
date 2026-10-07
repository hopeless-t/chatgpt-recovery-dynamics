#!/usr/bin/env python3
"""Project bounded recovery-policy frontiers across civilization environments.

This is a modeled world-building layer, not a claim about any provider's exact
infrastructure or real political/economic costs. It asks how the same finite set
of recovery levers changes viability as the environment changes.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import purrtocol_recovery_policy_lab as lab
import purrtocol_recovery_safety_frontier as frontier

INPUT_SCHEMA = "purrtocol-civilization-shock-regimes-input/v0"
OUTPUT_SCHEMA = "purrtocol-civilization-shock-regimes/v0"
MAX_ENVIRONMENTS = 12


class ShockRegimeError(ValueError):
    pass


def require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ShockRegimeError(f"{field} must be an object")
    return value


def classify_phase(result: dict[str, Any]) -> tuple[str, int | None]:
    if result["baseline"]["capacity_gate"]["pass"]:
        return "NO_INTERVENTION_REQUIRED", 0
    minimal = result["minimal_safe_packages"]
    if not minimal:
        return "FRONTIER_EMPTY_WITHIN_BOUND", None
    rows = {row["package_id"]: row for row in result["packages"]}
    minimum_size = min(rows[package_id]["package_size"] for package_id in minimal)
    if minimum_size == 1:
        return "SINGLE_LEVER_SUFFICIENT", 1
    return "COALITION_REQUIRED", minimum_size


def build(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") != INPUT_SCHEMA:
        raise ShockRegimeError(f"expected {INPUT_SCHEMA}")

    regime_lab_id = str(doc.get("regime_lab_id", "anonymous-shock-regime-lab"))
    base_scenario = require_dict(doc.get("base_scenario"), "base_scenario")
    base_policy = require_dict(doc.get("base_policy"), "base_policy")
    for key in lab.SCENARIO_KEYS:
        if key not in base_scenario:
            raise ShockRegimeError(f"base_scenario missing {key}")
    if "policy_id" not in base_policy:
        raise ShockRegimeError("base_policy missing policy_id")

    levers = doc.get("levers")
    if not isinstance(levers, list) or not levers:
        raise ShockRegimeError("levers must be a non-empty list")
    max_package_size = doc.get("max_package_size", min(2, len(levers)))

    environments = doc.get("environments")
    if not isinstance(environments, list) or not 1 <= len(environments) <= MAX_ENVIRONMENTS:
        raise ShockRegimeError(f"environments must contain 1..{MAX_ENVIRONMENTS} entries")

    seen: set[str] = set()
    regime_rows: list[dict[str, Any]] = []
    for index, raw in enumerate(environments):
        if not isinstance(raw, dict):
            raise ShockRegimeError("each environment must be an object")
        environment_id = raw.get("environment_id")
        if not isinstance(environment_id, str) or not environment_id.strip():
            raise ShockRegimeError("environment_id must be a non-empty string")
        environment_id = environment_id.strip()
        if environment_id in seen:
            raise ShockRegimeError("environment_id values must be unique")
        seen.add(environment_id)

        overrides = lab.bounded_overrides(
            raw.get("scenario_overrides", {}), lab.SCENARIO_KEYS, "scenario_overrides"
        )
        scenario = copy.deepcopy(base_scenario)
        scenario.update(overrides)
        frontier_doc = {
            "schema": frontier.INPUT_SCHEMA,
            "frontier_id": f"{regime_lab_id}:{environment_id}",
            "base_scenario": scenario,
            "base_policy": copy.deepcopy(base_policy),
            "max_package_size": max_package_size,
            "levers": copy.deepcopy(levers),
        }
        modeled = frontier.build(frontier_doc)
        phase, required_size = classify_phase(modeled)
        regime_rows.append({
            "ordinal": index,
            "environment_id": environment_id,
            "scenario": scenario,
            "frontier_phase": phase,
            "minimum_required_package_size": required_size,
            "baseline": modeled["baseline"],
            "minimal_safe_packages": modeled["minimal_safe_packages"],
            "complementarity_packages": modeled["complementarity_packages"],
            "safe_packages": modeled["safe_packages"],
            "unsafe_packages": modeled["unsafe_packages"],
            "summary": modeled["summary"],
            "packages": modeled["packages"],
        })

    transitions: list[dict[str, Any]] = []
    for previous, current in zip(regime_rows, regime_rows[1:]):
        transitions.append({
            "from_environment": previous["environment_id"],
            "to_environment": current["environment_id"],
            "from_phase": previous["frontier_phase"],
            "to_phase": current["frontier_phase"],
            "phase_changed": previous["frontier_phase"] != current["frontier_phase"],
            "minimum_package_size_before": previous["minimum_required_package_size"],
            "minimum_package_size_after": current["minimum_required_package_size"],
        })

    return {
        "schema": OUTPUT_SCHEMA,
        "regime_lab_id": regime_lab_id,
        "evidence_status": "modeled_bounded_civilization_regimes",
        "selection_policy": "capacity-gated-frontier-phase-no-cost-scalarization",
        "environment_count": len(regime_rows),
        "world_laws": {
            "policy_viability_is_environment_dependent": True,
            "single_lever_can_become_coalition_only": True,
            "bounded_frontier_can_disappear_under_stronger_shock": True,
            "frontier_empty_within_bound_is_not_global_impossibility": True,
            "safe_package_is_not_universal_winner": True,
            "heterogeneous_intervention_costs_not_scalarized": True,
            "modeled_regime_is_not_provider_topology": True,
        },
        "phase_sequence": [row["frontier_phase"] for row in regime_rows],
        "phase_transitions": transitions,
        "environments": regime_rows,
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
    print(json.dumps({
        "environment_count": result["environment_count"],
        "phase_sequence": result["phase_sequence"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
