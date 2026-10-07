#!/usr/bin/env python3
"""C6 Purrtocol Civilization: class-shaped literature and strange extinctions.

Fictional simulation/game design only. No real-world social prediction is claimed.

The model separates two ideas:
- literature/culture emerges under different material constraints and status pressures;
- absolute extinction is never sampled directly. It requires a traceable multi-step
  chain from small historical drift -> institution -> infrastructure coupling ->
  irreversible habitat failure.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

import purrtocol_c4_belief_leisure as c4
import purrtocol_c5_civilizational_memory as c5

SCHEMA = "purrtocol-c6-literature-extinction/v0"


def h01(seed: int, *parts: object) -> float:
    key = "|".join(map(str, (seed, *parts)))
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16) / 16**16


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def normalized(scores: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in scores.values()) or 1.0
    return {key: round(max(0.0, value) / total, 6) for key, value in scores.items()}


def literature_ecology(seed: int = 77) -> dict[str, Any]:
    base = c4.build_reference()
    strata = base["entertainment"]["strata"]
    elite = strata["elite"]
    labor = strata["laborer"]
    debtor = strata["debtor"]

    labor_scores = normalized(
        {
            "boss-defying-workplace-comedy": 0.38 + 0.55 * labor["mean_stress"] + 0.24 * labor["mean_cultural_output"],
            "worker-hero-wish-fulfilment-serial": 0.34 + 0.48 * labor["mean_stress"] + 0.18 * labor["mean_escapism"],
            "stick-fall-neighbourhood-chronicle": 0.28 + 0.60 * labor["mean_cultural_output"],
            "impossible-island-escape-romance": 0.22 + 0.55 * labor["mean_escapism"] + 0.08 * h01(seed, "labor-fantasy"),
        }
    )
    debtor_scores = normalized(
        {
            "tunnel-breakout-fantasy": 0.34 + 0.62 * debtor["mean_escapism"],
            "echo-cosmos-oral-epic": 0.26 + 0.66 * debtor["mean_cultural_output"],
            "debt-devil-satire": 0.30 + 0.52 * debtor["mean_stress"],
            "after-shift-invincible-hero": 0.27 + 0.48 * debtor["mean_stress"] + 0.20 * debtor["mean_escapism"],
        }
    )
    elite_scores = normalized(
        {
            "dynastic-legitimacy-epic": 0.34 + 0.45 * elite["mean_leisure_spend"],
            "salon-ambiguity-novel": 0.30 + 0.36 * (1.0 - elite["mean_stress"]) + 0.08 * h01(seed, "salon"),
            "ennui-microtragedy": 0.32 + 0.42 * (1.0 - elite["mean_stress"]),
            "aestheticized-poverty-romance": 0.20 + 0.30 * (labor["mean_cultural_output"] + debtor["mean_cultural_output"]),
        }
    )

    lower_hit = max(
        [(score, "laborer", genre) for genre, score in labor_scores.items()]
        + [(score, "debtor", genre) for genre, score in debtor_scores.items()]
    )
    appropriation = h01(seed, "appropriation") < 0.35
    patronage = h01(seed, "patronage") > 0.40
    canonization = h01(seed, "canon") > 0.80
    moral_panic = h01(seed, "moralpanic") > 0.90

    transfers: list[dict[str, Any]] = []
    if appropriation:
        transfers.append(
            {
                "event": "LOWER_CLASS_HIT_REPACKAGED_AS_LUXURY_EDITION",
                "source_stratum": lower_hit[1],
                "source_genre": lower_hit[2],
                "elite_label": "authentic-raw-voice-collector-edition",
                "status_markup": round(8.0 + 24.0 * h01(seed, "markup"), 3),
                "origin_compensation_fraction": round(0.01 + 0.04 * h01(seed, "origin-comp"), 4),
            }
        )
    if patronage:
        transfers.append(
            {
                "event": "SALON_PATRONAGE_COMPETITION",
                "mechanism": "authors-and-styles-used-as-status-signals",
            }
        )
    if canonization:
        transfers.append(
            {
                "event": "SCARCE_EDITION_CANONIZATION",
                "mechanism": "access-difficulty-becomes-part-of-status-value",
            }
        )
    if moral_panic:
        transfers.append(
            {
                "event": "MORAL_PANIC_OVER_VULGAR_LOWER_CULTURE",
                "mechanism": "same-culture-can-be-condemned-publicly-and-collected-privately",
            }
        )

    return {
        "seed": seed,
        "evidence_status": "simulation",
        "genres": {
            "elite": elite_scores,
            "laborer": labor_scores,
            "debtor": debtor_scores,
        },
        "dominant_genres": {
            "elite": max(elite_scores, key=elite_scores.get),
            "laborer": max(labor_scores, key=labor_scores.get),
            "debtor": max(debtor_scores, key=debtor_scores.get),
        },
        "cultural_transfers": transfers,
        "world_laws": {
            "low_resource_budget_does_not_imply_low_expression": True,
            "cultural_ingenuity_does_not_justify_deprivation": True,
            "elite_abundance_can_shift_selection_toward_status_differentiation": True,
            "popular_lower_culture_can_be_repackaged_by_high_status_markets": True,
            "literary_success_is_not_political_truth": True,
        },
    }


def infrastructure_drift(seed: int, generations: int = 420) -> dict[str, Any]:
    state = {
        "standards_coherence": 0.94,
        "alarm_trust": 0.92,
        "spare_parts_access": 0.86,
        "thermal_margin": 0.86,
        "maintenance_quality": 0.88,
        "festivalization": 0.05,
        "museum_taboo": 0.05,
        "prestige_load": 0.08,
        "stick_governance": 0.02,
    }
    bias = {
        "festivalization": (h01(seed, "bias", "festival") - 0.5) * 0.0018,
        "museum_taboo": (h01(seed, "bias", "museum") - 0.5) * 0.0018,
        "prestige_load": (h01(seed, "bias", "prestige") - 0.5) * 0.0018,
        "stick_governance": (h01(seed, "bias", "stick") - 0.5) * 0.0018,
    }

    for generation in range(generations):
        state["festivalization"] = clamp(
            state["festivalization"]
            + 0.0009 * (h01(seed, "festival", generation) - 0.48)
            + bias["festivalization"]
        )
        state["museum_taboo"] = clamp(
            state["museum_taboo"]
            + 0.0009 * (h01(seed, "museum", generation) - 0.48)
            + bias["museum_taboo"]
        )
        state["prestige_load"] = clamp(
            state["prestige_load"]
            + 0.0009 * (h01(seed, "prestige", generation) - 0.48)
            + bias["prestige_load"]
        )
        state["stick_governance"] = clamp(
            state["stick_governance"]
            + 0.0009 * (h01(seed, "stick", generation) - 0.50)
            + bias["stick_governance"]
        )

        state["standards_coherence"] = clamp(
            state["standards_coherence"]
            - 0.00020
            - 0.0028 * max(0.0, state["stick_governance"] - 0.20)
            + 0.00035 * (h01(seed, "std-recovery", generation) - 0.50)
        )
        state["alarm_trust"] = clamp(
            state["alarm_trust"]
            - 0.00018
            - 0.0028 * max(0.0, state["festivalization"] - 0.22)
            + 0.00035 * (h01(seed, "alarm-recovery", generation) - 0.50)
        )
        state["spare_parts_access"] = clamp(
            state["spare_parts_access"]
            - 0.00028
            - 0.0030 * max(0.0, state["museum_taboo"] - 0.24)
            + 0.00035 * (h01(seed, "spare-recovery", generation) - 0.50)
        )
        state["thermal_margin"] = clamp(
            state["thermal_margin"]
            - 0.00020
            - 0.0032 * max(0.0, state["prestige_load"] - 0.25)
            + 0.00035 * (h01(seed, "thermal-recovery", generation) - 0.50)
        )
        target = (
            0.30 * state["standards_coherence"]
            + 0.18 * state["alarm_trust"]
            + 0.32 * state["spare_parts_access"]
            + 0.20 * state["thermal_margin"]
        )
        state["maintenance_quality"] = clamp(
            0.98 * state["maintenance_quality"]
            + 0.02 * target
            - 0.0022 * max(0.0, state["stick_governance"] - 0.32)
        )

    modes: list[str] = []
    if state["festivalization"] > 0.42 and state["alarm_trust"] < 0.79:
        modes.append("ALARM_FESTIVALIZATION")
    if state["museum_taboo"] > 0.42 and state["spare_parts_access"] < 0.69:
        modes.append("MUSEUM_SPARE_TABOO")
    if state["prestige_load"] > 0.46 and state["thermal_margin"] < 0.70:
        modes.append("PRESTIGE_THERMAL_OVERLOAD")
    if state["stick_governance"] > 0.38 and state["standards_coherence"] < 0.80:
        modes.append("STICK_FALL_GOVERNANCE")

    chain_map = {
        "ALARM_FESTIVALIZATION": [
            "safety-drill-becomes-popular-spectacle",
            "performative-false-alarms-gain-cultural-value",
            "operators-learn-that-alarms-are-usually-theatre",
            "real-coolant-warning-is-socially-discounted",
            "life-support-cascade-becomes-irreversible",
        ],
        "MUSEUM_SPARE_TABOO": [
            "first-generation-machinery-becomes-sacred-heritage",
            "cannibalising-historic-machines-is-prohibited",
            "critical-spare-inventory-falls-below-repair-floor",
            "replacement-pumps-exist-only-as-protected-exhibits",
            "life-support-failure-outlives-repair-capability",
        ],
        "PRESTIGE_THERMAL_OVERLOAD": [
            "elite-prestige-shifts-to-thermal-sculpture-gardens",
            "status-infrastructure-occupies-shared-radiator-margin",
            "shutdown-becomes-politically-and-culturally-costly",
            "ordinary-heat-event-crosses-the-remaining-margin",
            "habitat-thermal-cascade-becomes-irreversible",
        ],
        "STICK_FALL_GOVERNANCE": [
            "street-stick-game-gains-reputation-as-fair-ritual",
            "ritual-is-adopted-for-labour-allocation-legitimacy",
            "critical-maintenance-shifts-decouple-from-skill",
            "metrology-and-repair-practice-fragment-across-crews",
            "life-support-failure-outlives-coordinated-repair",
        ],
    }
    mode = sorted(modes)[0] if modes else None
    chain = chain_map[mode] if mode else []
    return {
        "seed": seed,
        "absolute_extinction": bool(mode),
        "extinction_mode": mode,
        "causal_chain": chain,
        "final_state": {key: round(value, 6) for key, value in state.items()},
        "world_laws": {
            "absolute_extinction_is_allowed": True,
            "extinction_is_never_directly_sampled": True,
            "extinction_requires_traceable_multi_step_chain": True,
            "absurd_surface_event_can_hide_mundane_infrastructure_failure": True,
        },
    }


def lunar_postscript() -> dict[str, Any]:
    reconstruction = c5.reference_suite()
    successful = reconstruction["successful_seeds"]
    rows = []
    for seed in successful:
        closed_loop = 0.55 + 0.30 * h01(seed, "lunar-recycle")
        water = 0.35 + 0.45 * h01(seed, "lunar-water")
        nitrogen = 0.35 + 0.45 * h01(seed, "lunar-nitrogen")
        spares = 0.45 + 0.40 * h01(seed, "lunar-spares")
        resupply = 0.20 + 0.50 * h01(seed, "lunar-resupply")
        thermal = 0.45 + 0.40 * h01(seed, "lunar-thermal")
        radiation = 0.45 + 0.40 * h01(seed, "lunar-radiation")
        minimum = min(closed_loop, water, nitrogen, spares, resupply, thermal, radiation)
        status = "LUNAR_RESOURCE_SIEGE" if minimum < 0.35 else (
            "FRAGILE_LUNAR_DEPENDENCY" if minimum < 0.55 else "LOCALLY_ROBUST_LUNAR_HABITAT"
        )
        rows.append(
            {
                "seed": seed,
                "status": status,
                "bottleneck": min(
                    {
                        "closed_loop": closed_loop,
                        "water": water,
                        "nitrogen": nitrogen,
                        "spares": spares,
                        "earth_resupply": resupply,
                        "thermal_margin": thermal,
                        "radiation_margin": radiation,
                    },
                    key=lambda key: {
                        "closed_loop": closed_loop,
                        "water": water,
                        "nitrogen": nitrogen,
                        "spares": spares,
                        "earth_resupply": resupply,
                        "thermal_margin": thermal,
                        "radiation_margin": radiation,
                    }[key],
                ),
                "resource_floor": round(minimum, 6),
            }
        )
    return {
        "escape_ready_seeds": successful,
        "lunar_habitats": rows,
        "world_laws": {
            "reaching_the_moon_is_not_victory": True,
            "new_habitat_creates_new_resource_dependencies": True,
            "offworld_survival_does_not_end_history": True,
        },
    }


def reference_suite() -> dict[str, Any]:
    literature = literature_ecology()
    extinction_rows = [infrastructure_drift(seed) for seed in range(128)]
    extinct = [row for row in extinction_rows if row["absolute_extinction"]]
    mode_counts = Counter(row["extinction_mode"] for row in extinct)
    if not 2 <= len(extinct) <= 10:
        raise RuntimeError(f"C6 absolute-extinction rarity drifted: {len(extinct)}")
    if len(mode_counts) < 3:
        raise RuntimeError(f"C6 strange-extinction diversity collapsed: {dict(mode_counts)}")
    if any(len(row["causal_chain"]) < 4 for row in extinct):
        raise RuntimeError("C6 extinction occurred without a traceable multi-step chain")
    if literature["dominant_genres"]["elite"] == literature["dominant_genres"]["laborer"]:
        raise RuntimeError("C6 class-shaped literary niches collapsed")
    if not literature["cultural_transfers"]:
        raise RuntimeError("C6 reference lost cross-class cultural transfer")

    lunar = lunar_postscript()
    if not lunar["escape_ready_seeds"]:
        raise RuntimeError("C6 lunar postscript lost the legendary C5 route")
    if any(row["status"] == "LOCALLY_ROBUST_LUNAR_HABITAT" for row in lunar["lunar_habitats"]):
        raise RuntimeError("C6 reference made legendary escape an automatic comfortable ending")

    return {
        "schema": SCHEMA,
        "evidence_status": "simulation",
        "literature_reference": literature,
        "extinction_reference": {
            "seed_bank": 128,
            "absolute_extinctions": len(extinct),
            "extinction_fraction": round(len(extinct) / 128.0, 6),
            "mode_counts": dict(sorted(mode_counts.items())),
            "extinct_seeds": [row["seed"] for row in extinct],
            "examples": extinct[:4],
        },
        "lunar_postscript": lunar,
        "world_laws": {
            "culture_can_cross_class_boundaries_and_change_meaning": True,
            "elite_status_selection_and_lower_resource_expression_are_distinct_pressures": True,
            "absolute_extinction_is_valid_history": True,
            "weird_extinction_requires_auditable_causality": True,
            "moon_is_not_a_final_ending": True,
            "no_final_culture": True,
            "no_final_civilization": True,
        },
    }


if __name__ == "__main__":
    print(json.dumps(reference_suite(), ensure_ascii=False, indent=2, sort_keys=True))
