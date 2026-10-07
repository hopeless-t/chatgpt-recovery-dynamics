#!/usr/bin/env python3
"""Bounded C3 Purrtocol Civilization simulator: stratification + weak oracle.

Simulation/projection only. This is a game/research mechanism and does not model,
predict, or endorse real political systems.

Core rules:
- Dystopia emerges from resource allocation and institutional feedback, not a direct RNG event.
- The player cannot directly command agents. At most three weak oracle pulses may be injected.
- Only a small subset of cats can receive an oracle pulse.
- Receiving an oracle does not imply being believed; public preaching can create stigma.
- Same base trait vocabulary is retained: caution / sharing / compression / novelty.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any

SCHEMA = "purrtocol-c3-stratification-oracle/v0"
MAX_SEASONS = 160
MAX_ORACLES = 3


@dataclass
class Cat:
    cat_id: int
    stratum: str
    caution: float
    sharing: float
    compression: float
    novelty: float
    wealth: float
    debt: float
    health: float = 1.0
    belief: float = 0.0
    organization: float = 0.0
    stigma: float = 0.0


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def h01(seed: int, *parts: object) -> float:
    key = "|".join(map(str, (seed, *parts)))
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16) / 16**16


def make_population(seed: int, population: int) -> list[Cat]:
    out: list[Cat] = []
    for i in range(population):
        u = h01(seed, "class", i)
        stratum = "elite" if u < 0.08 else ("debtor" if u < 0.36 else "laborer")
        base_wealth = {"elite": 140.0, "laborer": 16.0, "debtor": 5.0}[stratum]
        base_debt = {"elite": 0.0, "laborer": 2.0, "debtor": 25.0}[stratum]
        out.append(
            Cat(
                cat_id=i,
                stratum=stratum,
                caution=h01(seed, "caution", i),
                sharing=h01(seed, "sharing", i),
                compression=h01(seed, "compression", i),
                novelty=h01(seed, "novelty", i),
                wealth=base_wealth * (0.85 + 0.30 * h01(seed, "wealth", i)),
                debt=base_debt * (0.80 + 0.40 * h01(seed, "debt", i)),
            )
        )
    return out


def oracle_receptivity(seed: int, cat: Cat) -> float:
    # Same base vocabulary; "oracle sensitivity" is derived, not a new heritable trait.
    return (
        0.42 * cat.novelty
        + 0.30 * cat.compression
        + 0.18 * cat.caution
        + 0.10 * h01(seed, "oracle-recept", cat.cat_id)
    )


def simulate(
    scenario_id: str,
    *,
    seed: int,
    population: int = 96,
    seasons: int = 80,
    harshness: float = 1.0,
    oracle_schedule: dict[int, float] | None = None,
) -> dict[str, Any]:
    if not 16 <= population <= 512:
        raise ValueError("population must be between 16 and 512")
    if not 1 <= seasons <= MAX_SEASONS:
        raise ValueError(f"seasons must be between 1 and {MAX_SEASONS}")
    if not 0.0 <= harshness <= 1.25:
        raise ValueError("harshness must be between 0 and 1.25")

    oracle_schedule = dict(sorted((oracle_schedule or {}).items()))
    if len(oracle_schedule) > MAX_ORACLES:
        raise ValueError(f"oracle pulses are bounded to {MAX_ORACLES}")
    if any(t < 0 or t >= seasons for t in oracle_schedule):
        raise ValueError("oracle season outside simulation horizon")
    if any(a < 0.0 or a > 0.06 for a in oracle_schedule.values()):
        raise ValueError("oracle amplitude must be between 0 and 0.06")

    cats = make_population(seed, population)
    ledger: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    oracle_receivers: dict[int, list[int]] = {}
    oracle_touched: set[int] = set()
    initial_wealth = sum(c.wealth for c in cats)
    external_production = 0.0
    external_consumption_sink = 0.0

    for season in range(seasons):
        elites = [c for c in cats if c.stratum == "elite"]
        workers = [c for c in cats if c.stratum != "elite"]

        mean_belief = mean(c.belief for c in cats)
        mean_org = mean(c.organization for c in cats)
        unrest = clamp(0.65 * mean_belief + 0.60 * mean_org)

        # Institutional ratchet: low resistance invites extraction; high resistance
        # invites surveillance. Neither branch is a direct "dystopia RNG" event.
        extraction = min(0.70, 0.44 * harshness + 0.10 * (1.0 - unrest))
        labor_hours = min(15.5, 10.5 + 3.7 * harshness + 0.5 * (1.0 - unrest))
        ration = max(0.42, 0.88 - 0.28 * harshness - 0.05 * h01(seed, "ration", season))
        hazard = min(0.60, 0.18 + 0.24 * harshness + 0.05 * h01(seed, "hazard", season))
        surveillance = min(0.92, 0.35 + 0.35 * harshness + 0.25 * unrest)

        rent_pool = 0.0
        period_production = 0.0
        period_consumption = 0.0
        period_luxury = 0.0

        for cat in workers:
            effective_hours = labor_hours + (1.0 if cat.stratum == "debtor" else 0.0)
            effective_hazard = min(0.75, hazard * (1.25 if cat.stratum == "debtor" else 1.0))
            effort = (effective_hours / 10.0) * (0.65 + 0.35 * cat.health)
            production = 2.6 * effort * (0.85 + 0.30 * cat.compression)
            wage = production * (1.0 - extraction) * 0.82
            rent = production - wage
            period_production += production
            rent_pool += rent
            cat.wealth += wage

            subsistence = 0.80 + 0.55 * (1.0 - ration) + 0.09 * effective_hours
            paid = min(cat.wealth, subsistence)
            cat.wealth -= paid
            period_consumption += paid

            if cat.stratum == "debtor":
                debt_payment = min(cat.wealth, 0.55 + 0.035 * cat.debt)
                cat.wealth -= debt_payment
                rent_pool += debt_payment
                # Principal can fall, but unpaid balances compound.
                cat.debt = max(0.0, cat.debt * 1.015 - debt_payment)

            health_noise = h01(seed, "health", season, cat.cat_id)
            damage = max(
                0.0,
                effective_hazard * (0.022 + 0.018 * health_noise)
                + (effective_hours - 10.0) * 0.004
                - ration * 0.012,
            )
            cat.health = max(0.15, clamp(cat.health - damage + 0.01))

        if elites:
            share = rent_pool / len(elites)
            for cat in elites:
                cat.wealth += share
                luxury = min(
                    cat.wealth,
                    3.0 + 4.5 * harshness + 0.6 * h01(seed, "luxury", season, cat.cat_id),
                )
                cat.wealth -= luxury
                period_luxury += luxury

        # Weak player agency: an oracle pulse only perturbs interpretation.
        if season in oracle_schedule:
            amplitude = oracle_schedule[season]
            received: list[int] = []
            for cat in cats:
                score = oracle_receptivity(seed, cat) + amplitude * (
                    0.85 + 0.15 * h01(seed, "oracle-phase", season, cat.cat_id)
                )
                if score > 0.90:
                    cat.belief = clamp(cat.belief + 0.20 + 0.35 * amplitude)
                    received.append(cat.cat_id)
                    oracle_touched.add(cat.cat_id)
            oracle_receivers[season] = received
            events.append(
                {
                    "season": season,
                    "event": "WEAK_ORACLE_PULSE",
                    "amplitude": round(amplitude, 4),
                    "receivers": received,
                    "receiver_fraction": round(len(received) / population, 4),
                }
            )

        # Oracle recipients can preach, but low-status preaching under surveillance
        # is often treated as suspicious rather than authoritative.
        for cat in cats:
            if cat.belief <= 0.12:
                cat.organization *= 0.96
                continue
            stratum_penalty = 0.20 if cat.stratum == "debtor" else (0.08 if cat.stratum == "laborer" else 0.0)
            credibility = (
                0.35
                + 0.30 * cat.compression
                + 0.20 * cat.sharing
                - 0.30 * surveillance
                - stratum_penalty
                - 0.25 * cat.stigma
            )
            preaching_pressure = cat.sharing * cat.belief
            if preaching_pressure > 0.11:
                if cat.cat_id in oracle_touched and credibility < 0.40:
                    old_stigma = cat.stigma
                    cat.stigma = clamp(cat.stigma + 0.10)
                    if old_stigma < 0.20 <= cat.stigma:
                        events.append(
                            {
                                "season": season,
                                "event": "SUSPICIOUS_PROPHET",
                                "cat_id": cat.cat_id,
                                "stratum": cat.stratum,
                                "credibility": round(credibility, 4),
                            }
                        )
                elif credibility >= 0.40:
                    # Social transmission is weak and can originate from either
                    # material grievance or oracle interpretation. Oracle receipt
                    # never guarantees successful preaching.
                    for contact_index in range(2):
                        target = int(
                            h01(seed, "contact", season, cat.cat_id, contact_index) * population
                        )
                        other = cats[target]
                        other.belief = clamp(
                            other.belief
                            + 0.025
                            * preaching_pressure
                            * (1.0 - surveillance)
                        )
            cat.organization = clamp(
                cat.organization * 0.93
                + cat.belief * cat.sharing * (1.0 - surveillance) * 0.035
            )

        worker_wealths = [c.wealth for c in workers]
        elite_mean_wealth = mean(c.wealth for c in elites)
        worker_mean_wealth = mean(worker_wealths)
        elite_total_wealth = sum(c.wealth for c in elites)
        worker_total_wealth = sum(worker_wealths)
        elite_wealth_share = elite_total_wealth / max(1e-9, elite_total_wealth + worker_total_wealth)
        elite_leisure_hours = max(4.0, 9.0 + 2.5 * harshness - 0.5 * unrest)
        inequality = elite_mean_wealth / (elite_mean_wealth + median(worker_wealths) + 1e-9)

        # Material grievance can evolve without any oracle.
        for cat in workers:
            grievance = max(
                0.0,
                0.30 * (labor_hours / 14.0)
                + 0.30 * (1.0 - ration)
                + 0.25 * hazard
                + 0.25 * inequality
                - 0.65,
            )
            cat.belief = clamp(
                cat.belief + grievance * 0.015 * (0.60 + 0.40 * cat.novelty)
            )

        external_production += period_production
        external_consumption_sink += period_consumption + period_luxury

        debtor_debt = [c.debt for c in cats if c.stratum == "debtor"]
        ledger.append(
            {
                "season": season,
                "extraction": round(extraction, 4),
                "labor_hours": round(labor_hours, 4),
                "ration": round(ration, 4),
                "hazard": round(hazard, 4),
                "surveillance": round(surveillance, 4),
                "elite_mean_wealth": round(elite_mean_wealth, 4),
                "worker_mean_wealth": round(worker_mean_wealth, 4),
                "elite_to_worker_wealth_ratio": round(
                    elite_mean_wealth / max(1.0, worker_mean_wealth), 4
                ),
                "elite_wealth_share": round(elite_wealth_share, 4),
                "elite_leisure_hours": round(elite_leisure_hours, 4),
                "debtor_mean_debt": round(mean(debtor_debt), 4),
                "mean_health_workers": round(mean(c.health for c in workers), 4),
                "mean_health_debtors": round(mean(c.health for c in cats if c.stratum == "debtor"), 4),
                "mean_belief": round(mean(c.belief for c in cats), 4),
                "mean_organization": round(mean(c.organization for c in cats), 4),
                "stigmatised_prophets": sum(1 for c in cats if c.stigma >= 0.20),
                "period_production_source": round(period_production, 4),
                "period_consumption_sink": round(period_consumption + period_luxury, 4),
                "period_elite_luxury_sink": round(period_luxury, 4),
            }
        )

    final = ledger[-1]
    final_wealth = sum(c.wealth for c in cats)
    # Debt is tracked separately from spendable wealth, so the cash-like conservation
    # identity only covers explicit wealth sources/sinks.
    conservation_residual = (
        initial_wealth + external_production - external_consumption_sink - final_wealth
    )

    oracle_receiver_count = sum(len(v) for v in oracle_receivers.values())
    unique_receivers = sorted({cat_id for ids in oracle_receivers.values() for cat_id in ids})
    dystopian_material_conditions = (
        final["labor_hours"] >= 13.0
        and final["ration"] < 0.70
        and final["hazard"] >= 0.38
        and final["elite_wealth_share"] >= 0.80
        and final["elite_leisure_hours"] >= 10.0
    )
    organized_underground = final["mean_organization"] >= 0.035
    outcome = (
        "UNDERGROUND_DISSENT"
        if dystopian_material_conditions and organized_underground
        else "STABLE_DYSTOPIA"
        if dystopian_material_conditions
        else "NON_DYSTOPIAN_OR_UNRESOLVED"
    )

    return {
        "schema": SCHEMA,
        "evidence_status": "simulation",
        "scenario_id": scenario_id,
        "seed": seed,
        "seasons": seasons,
        "population": population,
        "harshness": harshness,
        "outcome": outcome,
        "oracle_contract": {
            "max_pulses": MAX_ORACLES,
            "pulses_used": len(oracle_schedule),
            "direct_commands_forbidden": True,
            "oracle_changes_belief_not_material_state_directly": True,
            "receiver_selection_is_rare_thresholded_reception": True,
            "receiver_count_total": oracle_receiver_count,
            "unique_receivers": unique_receivers,
            "unique_receiver_fraction": round(len(unique_receivers) / population, 4),
        },
        "class_summary": {
            "elite": sum(1 for c in cats if c.stratum == "elite"),
            "laborer": sum(1 for c in cats if c.stratum == "laborer"),
            "debtor": sum(1 for c in cats if c.stratum == "debtor"),
        },
        "final_state": final,
        "events": events,
        "ledger": ledger,
        "accounting": {
            "initial_wealth": round(initial_wealth, 8),
            "external_production_source": round(external_production, 8),
            "external_consumption_sink": round(external_consumption_sink, 8),
            "final_wealth": round(final_wealth, 8),
            "conservation_residual": round(conservation_residual, 8),
        },
        "world_laws": {
            "dystopia_is_emergent_not_direct_rng": True,
            "elite_luxury_and_worker_hardship_share_one_resource_system": True,
            "debt_can_bind_lower_strata": True,
            "oracle_is_weak_and_rare": True,
            "oracle_recipient_is_not_automatically_credible": True,
            "prophecy_can_create_stigma": True,
            "player_cannot_directly_command_cats": True,
            "simulation_is_not_political_prediction": True,
        },
    }


def build_reference() -> dict[str, Any]:
    no_oracle = simulate("closed-dystopia-no-oracle", seed=77, oracle_schedule={})
    whisper = simulate(
        "closed-dystopia-weak-oracle",
        seed=77,
        oracle_schedule={20: 0.04},
    )
    repeated = simulate(
        "closed-dystopia-three-whispers",
        seed=77,
        oracle_schedule={20: 0.04, 45: 0.04, 65: 0.04},
    )
    return {
        "schema": "purrtocol-c3-stratification-oracle-reference/v0",
        "evidence_status": "simulation",
        "scenarios": {
            no_oracle["scenario_id"]: no_oracle,
            whisper["scenario_id"]: whisper,
            repeated["scenario_id"]: repeated,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", action="store_true")
    parser.add_argument("--seed", type=int, default=77)
    parser.add_argument("--population", type=int, default=96)
    parser.add_argument("--seasons", type=int, default=80)
    parser.add_argument("--harshness", type=float, default=1.0)
    parser.add_argument("--oracle", action="append", default=[], help="season:amplitude")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.reference:
        result = build_reference()
    else:
        schedule: dict[int, float] = {}
        for item in args.oracle:
            season_s, amplitude_s = item.split(":", 1)
            schedule[int(season_s)] = float(amplitude_s)
        result = simulate(
            "cli-world",
            seed=args.seed,
            population=args.population,
            seasons=args.seasons,
            harshness=args.harshness,
            oracle_schedule=schedule,
        )

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
