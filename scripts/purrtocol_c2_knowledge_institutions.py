#!/usr/bin/env python3
"""Bounded Purrtocol Civilization C2 knowledge/institution simulator.

Simulation/projection only. This does not predict real political systems. It is a
deterministic counterfactual harness for education, knowledge persistence,
institutional response, underground learning, reform, stagnation, and revolt.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCHEMA = "purrtocol-c2-knowledge-institutions/v0"
MAX_SEASONS = 120

POLICIES: dict[str, dict[str, float]] = {
    "OPEN_UNIVERSITY": {
        "access": 0.85,
        "repression": 0.05,
        "capture_drift": -0.015,
        "elite_access": 0.75,
    },
    "CONTROLLED_SCHOOLING": {
        "access": 0.42,
        "repression": 0.18,
        "capture_drift": 0.0,
        "elite_access": 0.80,
    },
    "ELITE_ACADEMY": {
        "access": 0.12,
        "repression": 0.34,
        "capture_drift": 0.015,
        "elite_access": 0.90,
    },
    "ABOLISH_SCHOOLS": {
        "access": 0.02,
        "repression": 0.62,
        "capture_drift": 0.025,
        "elite_access": 0.68,
    },
    "REFORM_COMPACT": {
        "access": 0.68,
        "repression": 0.08,
        "capture_drift": -0.035,
        "elite_access": 0.75,
    },
}


@dataclass
class State:
    citizen_knowledge: float = 0.22
    elite_knowledge: float = 0.58
    productivity: float = 0.48
    elite_capture: float = 0.72
    legitimacy: float = 0.68
    organization: float = 0.12
    underground: float = 0.01
    repression: float = 0.08
    education_access: float = 0.55
    season: int = 0


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def choose_policy(state: State, cfg: dict[str, Any]) -> tuple[str, float]:
    threat = state.citizen_knowledge * state.organization * state.elite_capture
    legitimacy_crisis = max(0.0, 0.52 - state.legitimacy)
    stagnation = max(0.0, 0.50 - state.productivity)

    # Reform is an endogenous response, not a guaranteed mercy branch. It only
    # exists when the scenario allows an adaptive ruling coalition.
    if cfg.get("adaptive_reform", True) and (
        legitimacy_crisis > 0.04
        or state.underground > 0.30
        or (threat > 0.11 and state.legitimacy < 0.62)
    ):
        return "REFORM_COMPACT", threat

    if threat > float(cfg.get("abolish_threshold", 0.22)) and state.elite_capture > 0.58:
        return "ABOLISH_SCHOOLS", threat
    if threat > float(cfg.get("restrict_threshold", 0.12)):
        return "ELITE_ACADEMY", threat
    if stagnation > 0.12:
        return "CONTROLLED_SCHOOLING", threat
    return str(cfg.get("default_policy", "OPEN_UNIVERSITY")), threat


def advance(state: State, policy: str) -> State:
    p = POLICIES[policy]
    access = p["access"]
    repression = p["repression"]

    # Formal education raises knowledge, but accumulated knowledge has memory.
    # Repression can slow it; it cannot set a learned population back to zero.
    learning = access * (0.055 + 0.03 * state.productivity)
    retention = 0.985 if state.citizen_knowledge > 0.50 else 0.97
    repression_loss = repression * 0.018
    underground_gain = state.underground * (0.035 + 0.025 * state.citizen_knowledge)
    citizen_knowledge = clamp(
        state.citizen_knowledge * retention + learning + underground_gain - repression_loss
    )

    # Closing schools can create a shadow education network, but only when a
    # society already has enough knowledge to reproduce teachers/materials.
    closure = max(0.0, 0.40 - access)
    underground = clamp(
        state.underground
        + closure * repression * (0.035 + 0.08 * state.citizen_knowledge)
        - access * 0.012
        - (1.0 - repression) * 0.004
    )

    organization = clamp(
        state.organization * 0.92
        + citizen_knowledge * 0.055
        + underground * 0.11
        - repression * 0.045
    )

    productivity_target = clamp(
        0.25 + 0.50 * citizen_knowledge + 0.18 * state.elite_knowledge - 0.18 * repression
    )
    productivity = clamp(0.82 * state.productivity + 0.18 * productivity_target)

    elite_capture = clamp(
        state.elite_capture
        + p["capture_drift"]
        - max(0.0, 0.42 - productivity) * 0.03
    )

    legitimacy_delta = (
        0.035 * (productivity - 0.45)
        - 0.045 * max(0.0, elite_capture - 0.65)
        - 0.04 * repression
        - 0.02 * max(0.0, underground - 0.25)
    )
    if policy == "REFORM_COMPACT":
        legitimacy_delta += 0.08
    legitimacy = clamp(state.legitimacy + legitimacy_delta)

    elite_knowledge = clamp(state.elite_knowledge * 0.985 + p["elite_access"] * 0.025)

    return State(
        citizen_knowledge=citizen_knowledge,
        elite_knowledge=elite_knowledge,
        productivity=productivity,
        elite_capture=elite_capture,
        legitimacy=legitimacy,
        organization=organization,
        underground=underground,
        repression=repression,
        education_access=access,
        season=state.season + 1,
    )


def revolutionary_pressure(state: State) -> float:
    grievance = clamp(
        0.55 * state.elite_capture
        + 0.35 * state.repression
        + 0.25 * max(0.0, 0.50 - state.productivity)
        - 0.50 * state.legitimacy
    )
    return clamp(
        state.organization * (0.45 + state.citizen_knowledge)
        + state.underground * 0.35
        + grievance * 0.35
    )


def classify_outcome(state: State, revolution: bool) -> str:
    if revolution:
        return "REVOLUTION"
    if (
        state.elite_capture > 0.80
        and state.legitimacy < 0.20
        and state.organization < 0.20
        and state.productivity < 0.46
    ):
        return "AUTHORITARIAN_STAGNATION"
    if state.productivity < 0.33 and state.citizen_knowledge < 0.30:
        return "GENERAL_STAGNATION"
    if state.elite_capture <= 0.56 and state.legitimacy > 0.52:
        return "REFORMED_ORDER"
    if state.elite_capture > 0.68 and state.legitimacy > 0.50:
        return "ELITE_STABILITY"
    return "UNRESOLVED"


def run_scenario(scenario_id: str, cfg: dict[str, Any], seasons: int) -> dict[str, Any]:
    state = State(**cfg.get("initial", {}))
    ledger: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    previous_policy: str | None = None
    revolution = False

    for _ in range(seasons):
        policy, threat = choose_policy(state, cfg)
        if policy != previous_policy:
            events.append({
                "season": state.season,
                "event": "POLICY_TRANSITION",
                "policy": policy,
                "threat": round(threat, 4),
            })
        next_state = advance(state, policy)
        pressure = revolutionary_pressure(next_state)

        if previous_policy != "ABOLISH_SCHOOLS" and policy == "ABOLISH_SCHOOLS":
            events.append({
                "season": next_state.season,
                "event": "FORMAL_SCHOOL_SYSTEM_ABOLISHED",
                "citizen_knowledge_at_abolition": round(next_state.citizen_knowledge, 4),
                "underground_at_abolition": round(next_state.underground, 4),
            })
        if state.underground < 0.20 <= next_state.underground:
            events.append({
                "season": next_state.season,
                "event": "UNDERGROUND_EDUCATION_NETWORK",
                "underground": round(next_state.underground, 4),
            })

        row = {
            "season": next_state.season,
            "policy": policy,
            "elite_threat": round(threat, 4),
            "revolutionary_pressure": round(pressure, 4),
            **{k: round(v, 4) if isinstance(v, float) else v for k, v in asdict(next_state).items()},
        }
        ledger.append(row)
        state = next_state
        previous_policy = policy

        if (
            pressure >= float(cfg.get("revolution_threshold", 0.66))
            and state.organization > 0.38
            and state.legitimacy < 0.46
        ):
            revolution = True
            events.append({
                "season": state.season,
                "event": "REVOLUTION_TRIGGERED",
                "revolutionary_pressure": round(pressure, 4),
            })
            break

    outcome = classify_outcome(state, revolution)
    policy_counts: dict[str, int] = {}
    for row in ledger:
        policy_counts[row["policy"]] = policy_counts.get(row["policy"], 0) + 1

    return {
        "scenario_id": scenario_id,
        "outcome": outcome,
        "seasons_run": len(ledger),
        "policy_counts": policy_counts,
        "final_state": {k: round(v, 4) if isinstance(v, float) else v for k, v in asdict(state).items()},
        "events": events,
        "ledger": ledger,
    }


def default_scenarios() -> dict[str, dict[str, Any]]:
    return {
        "late-abolition-after-knowledge-boom": {
            "default_policy": "OPEN_UNIVERSITY",
            "abolish_threshold": 0.16,
            "restrict_threshold": 0.09,
            "adaptive_reform": False,
        },
        "adaptive-reform-before-break": {
            "default_policy": "OPEN_UNIVERSITY",
            "abolish_threshold": 0.26,
            "restrict_threshold": 0.17,
            "adaptive_reform": True,
        },
        "early-knowledge-lockdown": {
            "default_policy": "ELITE_ACADEMY",
            "abolish_threshold": 0.09,
            "restrict_threshold": 0.05,
            "adaptive_reform": False,
            "initial": {
                "citizen_knowledge": 0.12,
                "elite_knowledge": 0.65,
                "productivity": 0.50,
                "elite_capture": 0.80,
                "legitimacy": 0.72,
                "organization": 0.06,
                "underground": 0.005,
                "repression": 0.10,
                "education_access": 0.15,
                "season": 0,
            },
        },
    }


def build(seasons: int) -> dict[str, Any]:
    scenarios = {
        scenario_id: run_scenario(scenario_id, cfg, seasons)
        for scenario_id, cfg in default_scenarios().items()
    }
    return {
        "schema": SCHEMA,
        "evidence_status": "simulation",
        "seasons_requested": seasons,
        "scenarios": scenarios,
        "world_laws": {
            "knowledge_is_not_revolution": True,
            "education_can_raise_productivity_and_organization": True,
            "abolition_cannot_erase_accumulated_knowledge": True,
            "late_suppression_can_feed_underground_learning": True,
            "early_suppression_can_trade_revolution_risk_for_stagnation": True,
            "reform_can_reduce_capture_without_erasing_knowledge": True,
            "no_policy_is_universal_winner": True,
            "simulation_is_not_political_prediction": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", type=int, default=60)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not 1 <= args.seasons <= MAX_SEASONS:
        parser.error(f"seasons must be between 1 and {MAX_SEASONS}")
    result = build(args.seasons)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v["outcome"] for k, v in result["scenarios"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
