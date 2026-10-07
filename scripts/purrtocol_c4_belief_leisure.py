#!/usr/bin/env python3
"""Bounded C4 Purrtocol Civilization simulator: belief markets + leisure ecology.

Simulation/projection only. This is fictional systems design, not a model of real
religions, poverty, labor, gambling behavior, or political systems.

Core rules:
- A genuine oracle receiver still has to earn social credibility.
- Visible gains from belief institutions create incentives for false oracle claims.
- Claim != receipt and wealth/power != truth.
- Entertainment differs by material constraint; scarcity can increase cultural
  ingenuity without making hardship desirable.
- Cheap escapist play can reduce short-run stress while becoming overlearned.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import purrtocol_c3_stratification_oracle as c3

SCHEMA = "purrtocol-c4-belief-leisure/v0"
MAX_SEASONS = 120


def doctrine_for(cat: c3.Cat) -> str:
    if cat.stratum == "elite":
        return "CHARITABLE_STEWARDSHIP"
    if cat.stratum == "laborer":
        return "MUTUAL_AID" if cat.sharing >= cat.caution else "ORDERED_REFORM"
    return "LIBERATION_SHARING" if cat.sharing >= cat.novelty else "ENDURE_AND_ESCAPE"


def authentication_strategy(cat: c3.Cat) -> tuple[str, float]:
    candidates = {
        "PUBLIC_PREDICTION": cat.compression + 0.70 * cat.caution,
        "COMMUNAL_RELIEF": cat.sharing + 0.50 * cat.caution,
        "SYMBOLIC_RITUAL": cat.novelty + 0.40 * cat.sharing,
    }
    strategy = max(candidates, key=candidates.get)
    return strategy, candidates[strategy]


def entertainment_profile(cat: c3.Cat, seed: int, season: int) -> tuple[str, float, float, float, float]:
    if cat.stratum == "elite":
        return (
            "salon-opera",
            0.18 + 0.05 * c3.h01(seed, "elite-leisure", season, cat.cat_id),
            0.10,
            0.025 + 0.015 * cat.novelty,
            0.005,
        )
    if cat.stratum == "laborer":
        # Stylized zero-tech street game: a stick is balanced and players predict
        # its fall direction. No attempt is made to model real gambling economics.
        return (
            "stick-fall-pool",
            0.015 + 0.006 * c3.h01(seed, "laborer-game", season, cat.cat_id),
            0.055,
            0.045 + 0.050 * cat.novelty + 0.025 * cat.sharing,
            0.035,
        )
    return (
        "echo-counting",
        0.003 + 0.002 * c3.h01(seed, "debtor-game", season, cat.cat_id),
        0.035,
        0.055 + 0.060 * cat.novelty + 0.030 * cat.sharing,
        0.060,
    )


def simulate(*, seed: int = 77, population: int = 96, seasons: int = 60, oracle_amplitude: float = 0.05) -> dict[str, Any]:
    if not 16 <= population <= 512:
        raise ValueError("population must be between 16 and 512")
    if not 1 <= seasons <= MAX_SEASONS:
        raise ValueError(f"seasons must be between 1 and {MAX_SEASONS}")
    if not 0.0 <= oracle_amplitude <= 0.06:
        raise ValueError("oracle amplitude must be between 0 and 0.06")

    cats = c3.make_population(seed, population)
    state: dict[int, dict[str, float]] = {
        cat.cat_id: {
            "credibility": 0.05,
            "belief": 0.0,
            "influence": 0.0,
            "stigma": 0.0,
            "stress": 0.0,
            "escapism": 0.0,
            "culture": 0.0,
            "donated": 0.0,
            "leisure_spend": 0.0,
        }
        for cat in cats
    }
    receivers: set[int] = set()
    false_claimants: set[int] = set()
    doctrine_by_cat: dict[int, str] = {}
    movement_followers: dict[str, set[int]] = defaultdict(set)
    movement_treasury: dict[str, float] = defaultdict(float)
    movement_meta: dict[str, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    entertainment_counts: dict[str, int] = defaultdict(int)

    initial_wealth = sum(cat.wealth for cat in cats)
    entertainment_sink = 0.0
    institutional_sink = 0.0

    for season in range(seasons):
        for cat in cats:
            s = state[cat.cat_id]
            baseline_stress = {"elite": 0.08, "laborer": 0.50, "debtor": 0.72}[cat.stratum]
            s["stress"] = c3.clamp(
                0.88 * s["stress"]
                + 0.12 * (baseline_stress + 0.08 * c3.h01(seed, "stress", season, cat.cat_id))
            )
            mode, cost, relief, culture_yield, escape_gain = entertainment_profile(cat, seed, season)
            cost = min(cat.wealth, cost)
            cat.wealth -= cost
            entertainment_sink += cost
            s["leisure_spend"] += cost
            s["culture"] += culture_yield
            s["stress"] = c3.clamp(s["stress"] - relief)
            s["escapism"] = c3.clamp(
                0.97 * s["escapism"] + max(0.0, s["stress"] - 0.25) * escape_gain
            )
            entertainment_counts[f"{cat.stratum}:{mode}"] += 1

        if season == 5:
            for cat in cats:
                score = c3.oracle_receptivity(seed, cat) + oracle_amplitude * (
                    0.85 + 0.15 * c3.h01(seed, "oracle-phase", season, cat.cat_id)
                )
                if score <= 0.90:
                    continue
                receivers.add(cat.cat_id)
                state[cat.cat_id]["belief"] += 0.28
                doctrine = doctrine_for(cat)
                doctrine_by_cat[cat.cat_id] = doctrine
                strategy, strategy_strength = authentication_strategy(cat)
                gain = 0.15 + 0.08 * strategy_strength + 0.03 * c3.h01(seed, "proof", cat.cat_id)
                state[cat.cat_id]["credibility"] = c3.clamp(
                    state[cat.cat_id]["credibility"] + gain
                )
                state[cat.cat_id]["influence"] += 0.05
                events.append(
                    {
                        "season": season,
                        "event": "GENUINE_ORACLE_RECEIVED",
                        "cat_id": cat.cat_id,
                        "stratum": cat.stratum,
                        "doctrine": doctrine,
                        "authentication_strategy": strategy,
                    }
                )

        visible_belief_rent = sum(movement_treasury.values()) + 0.05 * sum(
            len(v) for v in movement_followers.values()
        )
        if season >= 14 and visible_belief_rent > 0.25 and len(false_claimants) < 2:
            candidates: list[tuple[float, c3.Cat]] = []
            for cat in cats:
                if cat.cat_id in receivers or cat.cat_id in false_claimants:
                    continue
                opportunism = (
                    0.45 * cat.novelty
                    + 0.30 * cat.compression
                    + 0.25 * (1.0 - cat.sharing)
                    + 0.08 * c3.h01(seed, "opportunism", cat.cat_id)
                )
                if opportunism > 0.68:
                    candidates.append((opportunism, cat))
            if candidates:
                opportunism, cat = max(candidates, key=lambda item: item[0])
                false_claimants.add(cat.cat_id)
                doctrine_by_cat[cat.cat_id] = (
                    "PROSPERITY_REVELATION" if cat.stratum == "elite" else "SECRET_TRUE_ORACLE"
                )
                state[cat.cat_id]["credibility"] = 0.13 + 0.06 * cat.compression
                state[cat.cat_id]["influence"] = 0.03
                events.append(
                    {
                        "season": season,
                        "event": "FALSE_ORACLE_CLAIM",
                        "cat_id": cat.cat_id,
                        "stratum": cat.stratum,
                        "doctrine": doctrine_by_cat[cat.cat_id],
                        "opportunism": round(opportunism, 4),
                    }
                )

        for prophet_id in sorted(receivers | false_claimants):
            prophet = cats[prophet_id]
            prophet_state = state[prophet_id]
            movement_id = f"M{prophet_id}"
            movement_meta.setdefault(
                movement_id,
                {
                    "founder": prophet_id,
                    "genuine_receiver": prophet_id in receivers,
                    "doctrine": doctrine_by_cat[prophet_id],
                },
            )
            target_id = int(c3.h01(seed, "recruit", season, prophet_id) * population)
            if target_id != prophet_id:
                target = cats[target_id]
                target_state = state[target_id]
                affinity = 0.06 + (0.06 if target.stratum == prophet.stratum else 0.0)
                doctrine = movement_meta[movement_id]["doctrine"]
                if doctrine in ("LIBERATION_SHARING", "MUTUAL_AID"):
                    affinity += 0.08 * target.sharing
                elif doctrine == "PROSPERITY_REVELATION":
                    affinity += 0.06 if target.stratum == "elite" else 0.0
                else:
                    affinity += 0.05 * target.caution
                persuasion = (
                    0.28 * prophet_state["credibility"]
                    + 0.10 * prophet_state["influence"]
                    + affinity
                    - 0.15 * target_state["stigma"]
                )
                if persuasion > 0.145:
                    movement_followers[movement_id].add(target_id)
                    target_state["belief"] = c3.clamp(target_state["belief"] + 0.012)

            for follower_id in sorted(movement_followers[movement_id])[:2]:
                follower = cats[follower_id]
                contribution = min(
                    follower.wealth,
                    0.004 if follower.stratum == "debtor" else (0.012 if follower.stratum == "laborer" else 0.06),
                )
                follower.wealth -= contribution
                movement_treasury[movement_id] += contribution
                state[follower_id]["donated"] += contribution

            prophet_state["influence"] += 0.0015 * len(movement_followers[movement_id])
            burn = min(
                movement_treasury[movement_id],
                0.01 + 0.0005 * len(movement_followers[movement_id]),
            )
            movement_treasury[movement_id] -= burn
            institutional_sink += burn

            if movement_treasury[movement_id] > 0.05:
                founder_draw = min(movement_treasury[movement_id], 0.006)
                movement_treasury[movement_id] -= founder_draw
                prophet.wealth += founder_draw

    final_wealth = sum(cat.wealth for cat in cats) + sum(movement_treasury.values())
    conservation_residual = initial_wealth - entertainment_sink - institutional_sink - final_wealth

    strata: dict[str, dict[str, float]] = {}
    for stratum in ("elite", "laborer", "debtor"):
        ids = [cat.cat_id for cat in cats if cat.stratum == stratum]
        strata[stratum] = {
            "mean_leisure_spend": round(mean(state[i]["leisure_spend"] for i in ids), 4),
            "mean_cultural_output": round(mean(state[i]["culture"] for i in ids), 4),
            "mean_escapism": round(mean(state[i]["escapism"] for i in ids), 4),
            "mean_stress": round(mean(state[i]["stress"] for i in ids), 4),
        }

    movements = []
    for movement_id in sorted(movement_meta):
        meta = movement_meta[movement_id]
        founder = cats[meta["founder"]]
        movements.append(
            {
                **meta,
                "founder_stratum": founder.stratum,
                "followers": len(movement_followers[movement_id]),
                "treasury": round(movement_treasury[movement_id], 4),
                "founder_influence": round(state[meta["founder"]]["influence"], 4),
                "founder_wealth": round(founder.wealth, 4),
            }
        )

    return {
        "schema": SCHEMA,
        "evidence_status": "simulation",
        "seed": seed,
        "population": population,
        "seasons": seasons,
        "oracle": {
            "amplitude": oracle_amplitude,
            "genuine_receivers": sorted(receivers),
            "false_claimants": sorted(false_claimants),
            "claim_is_not_receipt": True,
        },
        "events": events,
        "movements": movements,
        "entertainment": {
            "counts": dict(sorted(entertainment_counts.items())),
            "strata": strata,
        },
        "accounting": {
            "initial_wealth": round(initial_wealth, 6),
            "entertainment_sink": round(entertainment_sink, 6),
            "institutional_sink": round(institutional_sink, 6),
            "final_wealth_plus_treasuries": round(final_wealth, 6),
            "conservation_residual": round(conservation_residual, 12),
        },
        "world_laws": {
            "genuine_receiver_must_still_build_credibility": True,
            "visible_belief_rent_can_attract_false_claimants": True,
            "wealth_or_power_does_not_prove_oracle_receipt": True,
            "scarcity_can_generate_improvised_culture_without_making_hardship_good": True,
            "cheap_escape_can_reduce_short_run_stress_and_overlearn_escape": True,
            "entertainment_niches_are_resource_conditioned": True,
            "simulation_is_not_social_prediction": True,
        },
    }


def build_reference() -> dict[str, Any]:
    result = simulate()
    movements = {row["founder"]: row for row in result["movements"]}
    receiver_set = set(result["oracle"]["genuine_receivers"])
    false_set = set(result["oracle"]["false_claimants"])
    if not (0 < len(receiver_set) <= 5):
        raise RuntimeError("C4 oracle receiver fixture stopped being rare")
    if len(false_set) < 1:
        raise RuntimeError("C4 belief-rent fixture stopped producing false claimants")
    if receiver_set & false_set:
        raise RuntimeError("C4 false claimant incorrectly marked as genuine receiver")
    if not any(event["event"] == "GENUINE_ORACLE_RECEIVED" for event in result["events"]):
        raise RuntimeError("C4 lost genuine oracle authentication path")
    if not any(event["event"] == "FALSE_ORACLE_CLAIM" for event in result["events"]):
        raise RuntimeError("C4 lost false oracle claim path")
    if not any((not row["genuine_receiver"]) and row["followers"] > 0 for row in result["movements"]):
        raise RuntimeError("C4 false claimant never converted belief into social power")
    strata = result["entertainment"]["strata"]
    if not (strata["elite"]["mean_leisure_spend"] > strata["laborer"]["mean_leisure_spend"] > strata["debtor"]["mean_leisure_spend"]):
        raise RuntimeError("C4 leisure-resource hierarchy drifted")
    if not (strata["debtor"]["mean_cultural_output"] > strata["laborer"]["mean_cultural_output"] > strata["elite"]["mean_cultural_output"]):
        raise RuntimeError("C4 improvised-culture fixture stopped differentiating by constraint")
    if strata["debtor"]["mean_escapism"] <= strata["laborer"]["mean_escapism"]:
        raise RuntimeError("C4 debtor escapism-overlearning fixture weakened unexpectedly")
    if abs(result["accounting"]["conservation_residual"]) > 1e-8:
        raise RuntimeError("C4 wealth-flow conservation drifted")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=77)
    parser.add_argument("--population", type=int, default=96)
    parser.add_argument("--seasons", type=int, default=60)
    parser.add_argument("--oracle-amplitude", type=float, default=0.05)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = simulate(
        seed=args.seed,
        population=args.population,
        seasons=args.seasons,
        oracle_amplitude=args.oracle_amplitude,
    )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"receivers": result["oracle"]["genuine_receivers"], "false_claimants": result["oracle"]["false_claimants"]}, sort_keys=True))


if __name__ == "__main__":
    main()
