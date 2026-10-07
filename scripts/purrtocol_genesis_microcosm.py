#!/usr/bin/env python3
"""Purrtocol Genesis: pre-life substrate, bounded fluctuation, and closed microcosm.

Simulation/projection only. This is a synthetic game/research mechanism, not a
model of real biology, economics, or politics.

The model imports structural ideas from market-microcosm-lab:
- explicit external sources/sinks;
- internal conservation;
- usage allocation + survival floor + ecosystem diversity fund;
- viability before optimization;
- declared bounded stochasticity and reproducible seeds.

Randomness never directly selects a regime outcome. Tiny exogenous fluctuations
change state; thresholds and feedbacks may then amplify those differences.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCHEMA = "purrtocol-genesis-microcosm/v0"
MAX_SEASONS = 240
MAX_POPULATION = 64
TRAITS = ("caution", "sharing", "compression", "novelty")
CHANNELS = ("energy", "signal", "shelter")


@dataclass(frozen=True)
class Environment:
    flux_energy: float = 2.4
    flux_signal: float = 1.9
    flux_shelter: float = 1.7
    hazard: float = 0.48
    volatility: float = 0.18
    connectivity: float = 0.52
    initial_energy: float = 5.0
    initial_signal: float = 4.0
    initial_shelter: float = 4.0


@dataclass
class Purrtocol:
    organism_id: str
    lineage_id: str
    reserve: float
    caution: float
    sharing: float
    compression: float
    novelty: float
    age: int = 0
    alive: bool = True


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def u01(seed: int, *parts: object) -> float:
    """Counter-based deterministic draw in [0, 1].

    Namespaces make exogenous environment noise independent from mutation draws.
    A branch that creates more children does not change the future weather.
    """
    payload = "|".join([str(seed), *(str(part) for part in parts)]).encode("utf-8")
    raw = hashlib.sha256(payload).digest()[:8]
    return int.from_bytes(raw, "big") / float(2**64 - 1)


def symmetric(seed: int, *parts: object, amplitude: float) -> float:
    return (2.0 * u01(seed, *parts) - 1.0) * amplitude


def founder_base_expression(env: Environment) -> dict[str, float]:
    """Same trait vocabulary, environment-conditioned expression."""
    scarcity = clamp01(
        1.0 - (env.flux_energy + env.flux_signal + env.flux_shelter) / 7.5
    )
    heterogeneity = statistics.pstdev(
        [env.flux_energy, env.flux_signal, env.flux_shelter]
    ) / 1.5
    return {
        "caution": clamp01(0.35 + 0.42 * env.hazard + 0.22 * env.volatility),
        "sharing": clamp01(0.34 + 0.40 * env.connectivity + 0.12 * scarcity),
        "compression": clamp01(0.33 + 0.38 * scarcity + 0.25 * env.volatility),
        "novelty": clamp01(
            0.34 + 0.36 * heterogeneity + 0.18 * (1.0 - env.hazard)
        ),
    }


def founder_expression(env: Environment, seed: int, founder_index: int) -> dict[str, float]:
    base = founder_base_expression(env)
    return {
        trait: clamp01(
            value
            + symmetric(
                seed, "founder-expression", founder_index, trait, amplitude=0.018
            )
        )
        for trait, value in base.items()
    }


def niche(cat: Purrtocol) -> str:
    values = {trait: getattr(cat, trait) for trait in TRAITS}
    return max(
        TRAITS,
        key=lambda trait: (values[trait], -TRAITS.index(trait)),
    )


def harvest_affinity(cat: Purrtocol) -> dict[str, float]:
    return {
        "energy": 0.60 + 0.50 * cat.compression + 0.20 * cat.caution,
        "signal": 0.50 + 0.60 * cat.sharing + 0.45 * cat.novelty,
        "shelter": 0.50 + 0.65 * cat.caution + 0.15 * cat.sharing,
    }


def dominant_niche(counts: collections.Counter[str]) -> str | None:
    if not counts:
        return None
    return max(
        TRAITS,
        key=lambda trait: (counts.get(trait, 0), -TRAITS.index(trait)),
    )


def run_world(
    *,
    seed: int,
    seasons: int = 80,
    environment: Environment | None = None,
    signal_perturbation: float = 0.0,
    perturbation_period: int = 1,
    max_population: int = 24,
) -> dict[str, Any]:
    if not 1 <= seasons <= MAX_SEASONS:
        raise ValueError(f"seasons must be between 1 and {MAX_SEASONS}")
    if not 4 <= max_population <= MAX_POPULATION:
        raise ValueError(f"max_population must be between 4 and {MAX_POPULATION}")
    if abs(signal_perturbation) > 0.25:
        raise ValueError("signal_perturbation must stay within +/-0.25")

    env = environment or Environment()
    pools = {
        "energy": env.initial_energy,
        "signal": env.initial_signal,
        "shelter": env.initial_shelter,
    }
    commons = 0.0
    population: list[Purrtocol] = []
    events: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    emerged = False
    next_id = 0

    for season in range(seasons):
        alive_at_start = [cat for cat in population if cat.alive]
        opening_stock = (
            sum(pools.values())
            + commons
            + sum(cat.reserve for cat in alive_at_start)
        )

        source: dict[str, float] = {}
        for channel, flux in (
            ("energy", env.flux_energy),
            ("signal", env.flux_signal),
            ("shelter", env.flux_shelter),
        ):
            noise = symmetric(
                seed,
                "environment",
                season,
                channel,
                amplitude=env.volatility,
            )
            source[channel] = max(0.0, flux * (1.0 + 0.20 * noise))

        if season == perturbation_period:
            source["signal"] += signal_perturbation

        for channel in CHANNELS:
            pools[channel] += source[channel]
        external_source = sum(source.values())

        abiotic_sink = 0.0
        for channel in CHANNELS:
            decay_rate = (
                0.010 + 0.010 * env.hazard if channel != "shelter" else 0.007
            )
            decay = pools[channel] * decay_rate
            pools[channel] -= decay
            abiotic_sink += decay

        metabolism_sink = 0.0
        mortality_sink = 0.0
        births = 0
        deaths = 0
        fund_target: str | None = None

        if not emerged:
            emergence_score = (
                pools["energy"] * pools["signal"] * pools["shelter"]
            ) ** (1.0 / 3.0) * (1.0 - 0.25 * env.hazard)
            if season >= 2 and emergence_score >= 5.0:
                founder_count = 4
                founder_cost = 0.8
                for founder_index in range(founder_count):
                    expression = founder_expression(env, seed, founder_index)
                    pools["energy"] -= founder_cost
                    population.append(
                        Purrtocol(
                            organism_id=f"PG-{next_id:04d}",
                            lineage_id=f"L{next_id:03d}",
                            reserve=founder_cost,
                            **expression,
                        )
                    )
                    next_id += 1
                emerged = True
                events.append(
                    {
                        "season": season,
                        "event": "LIFE_EMERGED",
                        "founders": founder_count,
                        "emergence_score": round(emergence_score, 6),
                        "trait_vocabulary": list(TRAITS),
                    }
                )
        else:
            alive = [cat for cat in population if cat.alive]

            demands: dict[str, list[tuple[Purrtocol, float]]] = {
                channel: [] for channel in CHANNELS
            }
            for cat in alive:
                affinity = harvest_affinity(cat)
                for channel in CHANNELS:
                    demands[channel].append((cat, 0.22 * affinity[channel]))

            gained = {cat.organism_id: 0.0 for cat in alive}
            usage = {cat.organism_id: 0.0 for cat in alive}
            for channel in CHANNELS:
                total_demand = sum(demand for _, demand in demands[channel])
                taken = min(pools[channel], total_demand)
                if total_demand > 0.0:
                    for cat, demand in demands[channel]:
                        amount = taken * demand / total_demand
                        gained[cat.organism_id] += amount
                        usage[cat.organism_id] += amount
                pools[channel] -= taken

            for cat in alive:
                cat.reserve += gained[cat.organism_id]

            # Internal transfer into a common pool.
            for cat in alive:
                excess = max(0.0, cat.reserve - 1.05)
                contribution = excess * (0.03 + 0.12 * cat.sharing)
                cat.reserve -= contribution
                commons += contribution

            # Market Microcosm pattern:
            # 50% usage, 30% survival floor, 20% ecosystem diversity fund.
            if alive and commons > 1e-12:
                distributable = commons
                commons = 0.0
                usage_pool = 0.50 * distributable
                survival_pool = 0.30 * distributable
                ecosystem_pool = 0.20 * distributable

                total_usage = sum(usage.values())
                if total_usage > 0.0:
                    for cat in alive:
                        cat.reserve += (
                            usage_pool * usage[cat.organism_id] / total_usage
                        )
                else:
                    commons += usage_pool

                low_reserve = sorted(
                    alive, key=lambda cat: (cat.reserve, cat.organism_id)
                )[: max(1, len(alive) // 3)]
                for cat in low_reserve:
                    cat.reserve += survival_pool / len(low_reserve)

                counts = collections.Counter(niche(cat) for cat in alive)
                minimum_count = min(counts.values())
                fund_target = sorted(
                    (
                        trait
                        for trait, count in counts.items()
                        if count == minimum_count
                    ),
                    key=TRAITS.index,
                )[0]
                target_cats = [
                    cat for cat in alive if niche(cat) == fund_target
                ]
                for cat in target_cats:
                    cat.reserve += ecosystem_pool / len(target_cats)

                events.append(
                    {
                        "season": season,
                        "event": "ECOSYSTEM_FUND_TARGET",
                        "niche": fund_target,
                    }
                )

            for cat in alive:
                metabolic_cost = (
                    0.25
                    + 0.10 * env.hazard
                    + 0.05 * (1.0 - cat.compression)
                )
                paid = min(cat.reserve, metabolic_cost)
                cat.reserve -= paid
                metabolism_sink += paid
                cat.age += 1

            for cat in alive:
                survival_threshold = 0.055 + 0.04 * (1.0 - cat.caution)
                if cat.reserve < survival_threshold:
                    mortality_sink += cat.reserve
                    cat.reserve = 0.0
                    cat.alive = False
                    deaths += 1

            # Reproduction is an internal reserve split.
            alive = [cat for cat in population if cat.alive]
            eligible = sorted(
                (
                    cat
                    for cat in alive
                    if cat.reserve > 1.18 and cat.age >= 3
                ),
                key=lambda cat: (-cat.reserve, cat.organism_id),
            )
            birth_budget = max(0, min(3, max_population - len(alive)))
            for parent in eligible[:birth_budget]:
                child_cost = 0.38
                parent.reserve -= child_cost
                base = founder_base_expression(env)
                birth_ordinal = next_id
                expression = {
                    trait: clamp01(
                        0.78 * getattr(parent, trait)
                        + 0.22 * base[trait]
                        + symmetric(
                            seed,
                            "mutation",
                            parent.organism_id,
                            birth_ordinal,
                            trait,
                            amplitude=0.025,
                        )
                    )
                    for trait in TRAITS
                }
                population.append(
                    Purrtocol(
                        organism_id=f"PG-{next_id:04d}",
                        lineage_id=parent.lineage_id,
                        reserve=child_cost,
                        **expression,
                    )
                )
                next_id += 1
                births += 1

        external_sink = abiotic_sink + metabolism_sink + mortality_sink
        closing_stock = (
            sum(pools.values())
            + commons
            + sum(cat.reserve for cat in population if cat.alive)
        )
        conservation_residual = closing_stock - (
            opening_stock + external_source - external_sink
        )

        alive = [cat for cat in population if cat.alive]
        counts = collections.Counter(niche(cat) for cat in alive)
        dominant = dominant_niche(counts)

        ledger.append(
            {
                "season": season,
                "phase": "LIFE" if emerged else "PRE_LIFE",
                "population": len(alive),
                "dominant_niche": dominant,
                "niche_counts": {
                    trait: counts.get(trait, 0) for trait in TRAITS
                },
                "births": births,
                "deaths": deaths,
                "fund_target": fund_target,
                "external_source": round(external_source, 8),
                "external_sink": round(external_sink, 8),
                "conservation_residual": round(conservation_residual, 10),
                "resource_pools": {
                    channel: round(pools[channel], 6)
                    for channel in CHANNELS
                },
            }
        )

    alive = [cat for cat in population if cat.alive]
    counts = collections.Counter(niche(cat) for cat in alive)
    means = {
        trait: (
            sum(getattr(cat, trait) for cat in alive) / len(alive)
            if alive
            else None
        )
        for trait in TRAITS
    }
    founder_event = next(
        (event for event in events if event["event"] == "LIFE_EMERGED"),
        None,
    )

    return {
        "schema": SCHEMA,
        "evidence_status": "simulation",
        "seed": seed,
        "environment": asdict(env),
        "random_contract": {
            "environment_noise_namespace": "environment",
            "founder_expression_namespace": "founder-expression",
            "mutation_namespace": "mutation",
            "bounded_environment_noise": env.volatility,
            "regime_outcomes_are_not_direct_random_draws": True,
        },
        "perturbation": {
            "channel": "signal",
            "period": perturbation_period,
            "absolute_amount": signal_perturbation,
            "relative_to_baseline_period_flux": round(
                signal_perturbation / env.flux_signal if env.flux_signal else 0.0,
                8,
            ),
        },
        "founder_event": founder_event,
        "trait_vocabulary": list(TRAITS),
        "final_state": {
            "population": len(alive),
            "dominant_niche": dominant_niche(counts),
            "niche_counts": {
                trait: counts.get(trait, 0) for trait in TRAITS
            },
            "trait_means": {
                trait: (
                    round(means[trait], 6)
                    if means[trait] is not None
                    else None
                )
                for trait in TRAITS
            },
        },
        "events": events,
        "ledger": ledger,
        "world_laws": {
            "internal_transfers_must_conserve_stock": True,
            "external_sources_and_sinks_must_be_explicit": True,
            "usage_allocation_is_not_the_only_allocation": True,
            "survival_floor_precedes_growth_optimization": True,
            "ecosystem_fund_protects_underrepresented_existing_niches": True,
            "same_trait_vocabulary_can_express_differently_by_environment": True,
            "micro_fluctuation_can_change_history_without_direct_outcome_rng": True,
            "same_seed_same_world": True,
            "simulation_is_not_evidence_about_real_societies_or_biology": True,
        },
    }


def fund_target_sequence(world: dict[str, Any]) -> list[str]:
    return [
        event["niche"]
        for event in world["events"]
        if event["event"] == "ECOSYSTEM_FUND_TARGET"
    ]


def zip_longest_strictish(
    left: list[str], right: list[str]
) -> list[tuple[str | None, str | None]]:
    length = max(len(left), len(right))
    return [
        (
            left[index] if index < len(left) else None,
            right[index] if index < len(right) else None,
        )
        for index in range(length)
    ]


def reference_suite() -> dict[str, Any]:
    """Compact CI fixture proving the intended replayability contract."""
    deterministic_a = run_world(seed=417, seasons=80)
    deterministic_b = run_world(seed=417, seasons=80)
    if deterministic_a != deterministic_b:
        raise RuntimeError("same seed no longer produces byte-equivalent state")

    ensemble = [run_world(seed=seed, seasons=80) for seed in range(410, 422)]
    signatures = {
        (
            world["final_state"]["dominant_niche"],
            tuple(world["final_state"]["niche_counts"].items()),
        )
        for world in ensemble
    }
    dominant_niches = {
        world["final_state"]["dominant_niche"] for world in ensemble
    }
    if len(signatures) < 6 or len(dominant_niches) < 2:
        raise RuntimeError("same macro conditions became too uniform across seeds")

    # Common exogenous environment stream + one 0.005 signal perturbation.
    # Baseline period signal flux is 1.9, so this is about 0.26%.
    twin_base = run_world(seed=467, seasons=80, signal_perturbation=0.0)
    twin_perturbed = run_world(seed=467, seasons=80, signal_perturbation=0.005)
    base_fund = fund_target_sequence(twin_base)
    perturbed_fund = fund_target_sequence(twin_perturbed)
    mismatch_count = sum(
        left != right
        for left, right in zip_longest_strictish(base_fund, perturbed_fund)
    )
    if mismatch_count < 12:
        raise RuntimeError("micro perturbation no longer propagates through allocation history")
    if (
        twin_base["final_state"]["dominant_niche"]
        == twin_perturbed["final_state"]["dominant_niche"]
    ):
        raise RuntimeError("reference twin no longer crosses the niche-history bifurcation")

    for world in (deterministic_a, twin_base, twin_perturbed, *ensemble):
        residual = max(
            abs(row["conservation_residual"]) for row in world["ledger"]
        )
        if residual > 1e-8:
            raise RuntimeError(f"closed-microcosm conservation drifted: {residual}")
        if world["trait_vocabulary"] != list(TRAITS):
            raise RuntimeError("trait vocabulary drifted across worlds")

    presets = {
        "hazard-world": (
            Environment(
                hazard=0.85,
                volatility=0.15,
                connectivity=0.25,
                flux_energy=2.2,
                flux_signal=1.8,
                flux_shelter=1.7,
            ),
            "caution",
        ),
        "connected-world": (
            Environment(
                hazard=0.15,
                volatility=0.10,
                connectivity=0.90,
                flux_energy=2.3,
                flux_signal=2.2,
                flux_shelter=2.0,
            ),
            "sharing",
        ),
        "sparse-volatile-world": (
            Environment(
                hazard=0.35,
                volatility=0.45,
                connectivity=0.25,
                flux_energy=0.8,
                flux_signal=0.7,
                flux_shelter=0.9,
            ),
            "compression",
        ),
        "heterogeneous-world": (
            Environment(
                hazard=0.15,
                volatility=0.12,
                connectivity=0.30,
                flux_energy=3.8,
                flux_signal=0.8,
                flux_shelter=1.0,
            ),
            "novelty",
        ),
    }
    adaptation: dict[str, str] = {}
    for name, (env, expected_trait) in presets.items():
        profile = founder_base_expression(env)
        dominant_trait = max(
            TRAITS,
            key=lambda trait: (profile[trait], -TRAITS.index(trait)),
        )
        if dominant_trait != expected_trait:
            raise RuntimeError(f"{name} founder expression drifted: {dominant_trait}")
        adaptation[name] = dominant_trait

    return {
        "schema": "purrtocol-genesis-reference/v0",
        "evidence_status": "simulation",
        "same_seed_deterministic": True,
        "same_macro_condition_distinct_signatures": len(signatures),
        "same_macro_condition_dominant_niches": sorted(
            niche for niche in dominant_niches if niche is not None
        ),
        "micro_twin": {
            "seed": 467,
            "signal_perturbation": 0.005,
            "relative_perturbation": twin_perturbed["perturbation"][
                "relative_to_baseline_period_flux"
            ],
            "allocation_history_mismatches": mismatch_count,
            "baseline_final": twin_base["final_state"],
            "perturbed_final": twin_perturbed["final_state"],
        },
        "environment_conditioned_founder_expression": adaptation,
        "world_laws": deterministic_a["world_laws"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=417)
    parser.add_argument("--seasons", type=int, default=80)
    parser.add_argument("--signal-perturbation", type=float, default=0.0)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--reference-suite",
        action="store_true",
        help="write the compact deterministic CI/reference summary",
    )
    args = parser.parse_args()

    if args.reference_suite:
        result = reference_suite()
    else:
        result = run_world(
            seed=args.seed,
            seasons=args.seasons,
            signal_perturbation=args.signal_perturbation,
        )

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result.get("final_state", result), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
