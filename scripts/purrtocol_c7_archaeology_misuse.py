#!/usr/bin/env python3
"""C7 Purrtocol Civilization: archaeology, misinterpretation, and relic reuse.

Fictional simulation/game-system design only.

World laws:
- Relic != understood technology.
- Wrong interpretation != useless interpretation.
- Social confidence != historical correctness.
- Physical affordance can outlive semantic memory.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

import purrtocol_c5_civilizational_memory as c5

SCHEMA = "purrtocol-c7-archaeology-misuse/v0"
LEGENDARY_SEED = 57


def h01(seed: int, *parts: object) -> float:
    key = "|".join(map(str, (seed, *parts)))
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16) / 16**16


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


RELICS: tuple[dict[str, Any], ...] = (
    {
        "relic_id": "crew-capsule",
        "original_function": "crew-survival-and-reentry",
        "affordances": ("sealed-shell", "thermal-protection", "seats", "small-interior"),
        "misuses": (
            ("ROYAL_ANCESTOR_TOMB", "ritual", "preserves-shell"),
            ("STORM_REFUGE", "practical", "preserves-sealing-knowledge"),
            ("GRAIN_VAULT", "practical", "preserves-moisture-control-intuition"),
            ("CONFESSION_ORACLE_CHAMBER", "ritual", "preserves-acoustic-curiosity"),
        ),
    },
    {
        "relic_id": "engine-bell",
        "original_function": "rocket-nozzle",
        "affordances": ("heat-resistant", "funnel-shape", "large-resonant-cavity"),
        "misuses": (
            ("TEMPLE_HORN", "ritual", "preserves-resonance-knowledge"),
            ("RAIN_CATCHER", "practical", "preserves-flow-intuition"),
            ("COMMUNAL_FURNACE_HOOD", "practical", "preserves-heat-flow-intuition"),
            ("VICTORY_CANOPY", "status", "preserves-object-only"),
        ),
    },
    {
        "relic_id": "star-tracker",
        "original_function": "stellar-attitude-sensing",
        "affordances": ("optics", "sky-pointing", "repeatable-star-patterns"),
        "misuses": (
            ("SKY_ORACLE", "ritual", "preserves-seasonal-astronomy"),
            ("ROYAL_BIRTH_DIVINER", "status", "preserves-star-catalogue-fragments"),
            ("FARMERS_CALENDAR_BOX", "practical", "preserves-seasonal-astronomy"),
            ("SEA_NAVIGATION_SHRINE", "practical", "preserves-directional-astronomy"),
        ),
    },
    {
        "relic_id": "thermal-tiles",
        "original_function": "reentry-heat-protection",
        "affordances": ("heat-resistant", "lightweight", "regular-modules"),
        "misuses": (
            ("SACRED_COOKSTONES", "practical", "preserves-heat-material-selection"),
            ("FORTUNE_GAME_TILES", "leisure", "preserves-modular-counting"),
            ("PRIESTLY_ROOF_SHINGLES", "ritual", "preserves-heat-material-selection"),
            ("ELITE_DISPLAY_ARMOUR", "status", "preserves-object-only"),
        ),
    },
    {
        "relic_id": "pressure-tank",
        "original_function": "pressurized-propellant-storage",
        "affordances": ("sealed-vessel", "pressure-resistant", "large-volume"),
        "misuses": (
            ("FERMENTATION_VAT", "practical", "preserves-vessel-hygiene"),
            ("COMMUNAL_WATER_CISTERN", "practical", "preserves-sealing-knowledge"),
            ("ECHO_TEMPLE", "ritual", "preserves-acoustic-curiosity"),
            ("DYNASTIC_TREASURE_VAULT", "status", "preserves-object-only"),
        ),
    },
    {
        "relic_id": "docking-ring",
        "original_function": "standardized-spacecraft-coupling",
        "affordances": ("precision-circle", "repeatable-interface", "load-bearing"),
        "misuses": (
            ("MARRIAGE_COVENANT_RING", "ritual", "preserves-dimensional-standard"),
            ("MARKET_MEASURE_GATE", "practical", "preserves-dimensional-standard"),
            ("CITY_FOUNDING_ARCH", "status", "preserves-object-only"),
            ("GIANT_STICK_FALL_ARENA", "leisure", "preserves-circular-layout"),
        ),
    },
)


def successor_knowledge(seed: int) -> dict[str, float]:
    return {
        "language_continuity": 0.04 + 0.34 * h01(seed, "language"),
        "archive_literacy": 0.03 + 0.30 * h01(seed, "archive"),
        "metrology": 0.04 + 0.40 * h01(seed, "metrology"),
        "physics": 0.02 + 0.28 * h01(seed, "physics"),
        "materials": 0.08 + 0.42 * h01(seed, "materials"),
        "machine_tools": 0.02 + 0.25 * h01(seed, "machine-tools"),
        "ritualization": 0.20 + 0.70 * h01(seed, "ritualization"),
        "status_pressure": 0.15 + 0.75 * h01(seed, "status"),
        "scarcity": 0.18 + 0.75 * h01(seed, "scarcity"),
        "institutional_trust": 0.10 + 0.70 * h01(seed, "trust"),
    }


def reconstruction_score(k: dict[str, float], relic_id: str) -> float:
    base = (
        0.22 * k["language_continuity"]
        + 0.22 * k["archive_literacy"]
        + 0.18 * k["metrology"]
        + 0.20 * k["physics"]
        + 0.10 * k["materials"]
        + 0.08 * k["machine_tools"]
    )
    return clamp(base + 0.04 * (h01(LEGENDARY_SEED, "reconstruction", relic_id) - 0.5))


def choose_misuse(seed: int, relic: dict[str, Any], k: dict[str, float]) -> tuple[str, str, str]:
    ranked: list[tuple[float, tuple[str, str, str]]] = []
    for name, category, echo in relic["misuses"]:
        score = h01(seed, relic["relic_id"], name)
        if category == "ritual":
            score += 0.55 * k["ritualization"] + 0.15 * k["institutional_trust"]
        elif category == "status":
            score += 0.55 * k["status_pressure"] + 0.10 * (1.0 - k["scarcity"])
        elif category == "practical":
            score += 0.42 * k["scarcity"] + 0.20 * k["materials"]
        else:
            score += 0.25 * k["scarcity"] + 0.20 * k["ritualization"]
        ranked.append((score, (name, category, echo)))
    return max(ranked, key=lambda row: row[0])[1]


def interpret_relic(seed: int, relic: dict[str, Any], k: dict[str, float]) -> dict[str, Any]:
    reconstruct = reconstruction_score(k, relic["relic_id"])
    correct = reconstruct >= 0.54
    if correct:
        interpretation, category, echo = (
            "PARTIAL_TECHNICAL_RECONSTRUCTION",
            "technical",
            "original-function-fragment",
        )
    else:
        interpretation, category, echo = choose_misuse(seed, relic, k)

    evidence_destruction = clamp(
        0.55 * k["scarcity"]
        + 0.18 * (1.0 - k["archive_literacy"])
        - 0.34 * k["ritualization"]
        + 0.08 * (h01(seed, relic["relic_id"], "strip") - 0.5)
    )
    ritual_preservation = clamp(
        0.62 * k["ritualization"]
        + 0.18 * k["institutional_trust"]
        - 0.15 * k["scarcity"]
    )
    confidence = clamp(
        0.28
        + 0.38 * k["institutional_trust"]
        + 0.28 * k["ritualization"]
        + 0.12 * k["status_pressure"]
        + 0.08 * h01(seed, relic["relic_id"], "confidence")
    )

    if correct:
        fate = "TECHNICAL_STUDY"
    elif evidence_destruction > 0.50:
        # Calibrated so destructive reuse is possible but rare in the 24-culture reference bank.
        fate = "STRIPPED_FOR_PARTS"
    elif ritual_preservation > 0.56:
        fate = "RITUALLY_PRESERVED"
    else:
        fate = "REPURPOSED_IN_DAILY_LIFE"

    return {
        "relic_id": relic["relic_id"],
        "original_function": relic["original_function"],
        "interpretation": interpretation,
        "interpretation_category": category,
        "historically_correct": correct,
        "reconstruction_score": round(reconstruct, 6),
        "social_confidence": round(confidence, 6),
        "functional_echo": echo,
        "fate": fate,
        "evidence_destruction_pressure": round(evidence_destruction, 6),
        "ritual_preservation_pressure": round(ritual_preservation, 6),
    }


def successor_culture(seed: int) -> dict[str, Any]:
    k = successor_knowledge(seed)
    rows = [interpret_relic(seed, relic, k) for relic in RELICS]
    echoes = Counter(row["functional_echo"] for row in rows if not row["historically_correct"])
    derived: list[str] = []
    if echoes["preserves-dimensional-standard"]:
        derived.append("RITUAL_DIMENSIONAL_STANDARDIZATION")
    if echoes["preserves-seasonal-astronomy"] or echoes["preserves-directional-astronomy"]:
        derived.append("MYTHIC_BUT_USEFUL_ASTRONOMY")
    if echoes["preserves-heat-material-selection"]:
        derived.append("EMPIRICAL_HEAT_MATERIAL_TRADITION")
    if echoes["preserves-sealing-knowledge"] or echoes["preserves-vessel-hygiene"]:
        derived.append("CONTAINER_CRAFT_TRADITION")
    if echoes["preserves-modular-counting"]:
        derived.append("GAME_DERIVED_COUNTING_NOTATION")

    institutions: list[str] = []
    for row in rows:
        if row["interpretation_category"] == "ritual" and row["fate"] == "RITUALLY_PRESERVED":
            institutions.append(f"CULT_OF_{row['relic_id'].upper().replace('-', '_')}")
        if row["interpretation"] == "MARKET_MEASURE_GATE":
            institutions.append("MARKET_GATE_STANDARD_AUTHORITY")
        if row["interpretation"] == "SKY_ORACLE":
            institutions.append("SKY_ORACLE_CALENDAR_PRIESTHOOD")
        if row["interpretation"] == "FORTUNE_GAME_TILES":
            institutions.append("THERMAL_TILE_FORTUNE_LEAGUE")

    correct = sum(row["historically_correct"] for row in rows)
    return {
        "successor_seed": seed,
        "evidence_status": "simulation",
        "knowledge": {key: round(value, 6) for key, value in k.items()},
        "relic_interpretations": rows,
        "correct_reconstructions": correct,
        "wrong_interpretations": len(rows) - correct,
        "derived_capabilities": sorted(set(derived)),
        "institutions": sorted(set(institutions)),
    }


def reference_suite() -> dict[str, Any]:
    origin = c5.simulate(LEGENDARY_SEED)
    if not origin["escape_ready"]:
        raise RuntimeError("C7 lost the legendary advanced origin civilization")

    successors = [successor_culture(seed) for seed in range(24)]
    total_relics = len(successors) * len(RELICS)
    total_correct = sum(row["correct_reconstructions"] for row in successors)
    interpretations = Counter(
        relic["interpretation"]
        for culture in successors
        for relic in culture["relic_interpretations"]
    )
    wrong_confident = [
        relic
        for culture in successors
        for relic in culture["relic_interpretations"]
        if not relic["historically_correct"] and relic["social_confidence"] >= 0.60
    ]
    productive = [culture for culture in successors if culture["derived_capabilities"]]
    preserved = [
        relic
        for culture in successors
        for relic in culture["relic_interpretations"]
        if not relic["historically_correct"] and relic["fate"] == "RITUALLY_PRESERVED"
    ]
    stripped = [
        relic
        for culture in successors
        for relic in culture["relic_interpretations"]
        if relic["fate"] == "STRIPPED_FOR_PARTS"
    ]

    if total_correct > 4:
        raise RuntimeError(f"C7 successor cultures understand relics too easily: {total_correct}/{total_relics}")
    if len(interpretations) < 10:
        raise RuntimeError("C7 relic interpretation diversity collapsed")
    if len(wrong_confident) < 8:
        raise RuntimeError("C7 lost confident-but-wrong successor interpretations")
    if len(productive) < 8:
        raise RuntimeError("C7 lost wrong-but-useful cultural reuse")
    if not preserved:
        raise RuntimeError("C7 lost accidental evidence preservation through ritual")
    if not stripped:
        raise RuntimeError("C7 lost destructive scarcity-driven reuse")

    return {
        "schema": SCHEMA,
        "evidence_status": "simulation",
        "origin": {
            "seed": LEGENDARY_SEED,
            "escape_ready": origin["escape_ready"],
            "advanced_capabilities": origin["final"],
        },
        "successor_bank": {
            "cultures": len(successors),
            "relics_per_culture": len(RELICS),
            "total_relic_interpretations": total_relics,
            "correct_reconstructions": total_correct,
            "correct_fraction": round(total_correct / total_relics, 6),
            "unique_interpretations": len(interpretations),
            "interpretation_counts": dict(sorted(interpretations.items())),
            "confident_wrong_cases": len(wrong_confident),
            "productive_misreader_cultures": len(productive),
            "ritually_preserved_wrong_cases": len(preserved),
            "stripped_for_parts_cases": len(stripped),
        },
        "examples": successors[:8],
        "world_laws": {
            "relic_is_not_understood_technology": True,
            "wrong_interpretation_can_be_locally_useful": True,
            "social_confidence_does_not_prove_historical_correctness": True,
            "ritual_can_accidentally_preserve_technical_evidence": True,
            "scarcity_can_destroy_archaeological_evidence": True,
            "physical_affordance_can_outlive_semantic_memory": True,
            "technical_reconstruction_requires_dependency_chain": True,
            "no_final_technology": True,
            "no_final_civilization": True,
        },
    }


if __name__ == "__main__":
    print(json.dumps(reference_suite(), ensure_ascii=False, indent=2, sort_keys=True))
