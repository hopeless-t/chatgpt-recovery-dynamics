#!/usr/bin/env python3
"""C5 Purrtocol Civilization: rare civilizational reconstruction path.

Fictional game/research simulation only.

The reconstruction route is intentionally rare. A blueprint is not a capability:
knowledge, tooling, standards, logistics, education, power, and precision industry
must remain mutually alive across many generations before orbital escape is possible.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


CAPABILITIES = (
    "memory",
    "basic_tools",
    "metrology",
    "materials",
    "machine_tools",
    "power",
    "education",
    "standards",
    "logistics",
    "precision_industry",
    "computing",
    "propulsion",
    "orbital_systems",
)


def h01(seed: int, *parts: object) -> float:
    key = "|".join(map(str, (seed, *parts)))
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16) / 16**16


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass
class State:
    memory: float
    basic_tools: float
    metrology: float
    materials: float
    machine_tools: float
    power: float
    education: float
    standards: float
    logistics: float
    precision_industry: float
    computing: float
    propulsion: float
    orbital_systems: float


def prereq_product(s: State, names: tuple[str, ...]) -> float:
    p = 1.0
    for name in names:
        p *= max(0.0, getattr(s, name))
    return p ** (1.0 / len(names))


def simulate(seed: int, generations: int = 700) -> dict:
    archive_quality = h01(seed, "archive")
    resource_access = h01(seed, "resource_access")
    coordination = h01(seed, "coordination")
    peace_capacity = h01(seed, "peace")
    surplus = h01(seed, "surplus")

    continuity_support = (
        0.25 * archive_quality
        + 0.20 * resource_access
        + 0.25 * coordination
        + 0.20 * peace_capacity
        + 0.10 * surplus
    )
    continuity = max(0.0, min(1.0, (continuity_support - 0.45) / 0.55))

    s = State(
        memory=0.20 + 0.18 * archive_quality,
        basic_tools=0.16 + 0.08 * resource_access,
        metrology=0.05 + 0.05 * coordination,
        materials=0.10 + 0.08 * resource_access,
        machine_tools=0.02,
        power=0.07 + 0.05 * resource_access,
        education=0.08 + 0.12 * coordination,
        standards=0.02,
        logistics=0.05 + 0.05 * coordination,
        precision_industry=0.005,
        computing=0.0,
        propulsion=0.0,
        orbital_systems=0.0,
    )

    failure_modes: dict[str, int] = {}
    history_tail: list[dict] = []

    for g in range(generations):
        conflict = (0.04 + 0.14 * h01(seed, "conflict", g)) * (1.0 - 0.55 * peace_capacity)
        elite_capture = (0.10 + 0.18 * h01(seed, "elite", g)) * (1.0 - 0.35 * coordination)
        superstition = (0.04 + 0.10 * h01(seed, "superstition", g)) * (1.0 - 0.45 * archive_quality)
        entertainment_absorption = 0.04 + 0.12 * h01(seed, "entertainment", g)
        resource_mismatch = (0.05 + 0.18 * h01(seed, "resource", g)) * (1.0 - 0.50 * resource_access)

        # Preservation itself is a capability. A civilization can know what it needs
        # and still lose the chain through schools, standards, conflict, or materials.
        s.memory = clamp(
            s.memory
            + 0.006 * s.education
            + 0.004 * archive_quality * continuity
            - 0.005 * conflict
            - 0.004 * superstition
            - 0.002 * (1.0 - continuity)
        )
        s.basic_tools = clamp(s.basic_tools + 0.008 * s.memory * resource_access - 0.003 * resource_mismatch)
        s.metrology = clamp(
            s.metrology
            + 0.007 * prereq_product(s, ("memory", "basic_tools", "education")) * coordination
            - 0.003 * conflict
        )
        s.materials = clamp(
            s.materials
            + 0.007 * prereq_product(s, ("basic_tools", "logistics")) * resource_access
            - 0.003 * resource_mismatch
        )
        s.power = clamp(
            s.power
            + 0.006 * prereq_product(s, ("materials", "basic_tools")) * resource_access
            - 0.003 * resource_mismatch
        )
        s.education = clamp(
            s.education
            + 0.006 * s.memory * coordination
            + 0.003 * archive_quality * continuity
            - 0.004 * elite_capture
            - 0.003 * superstition
        )
        s.standards = clamp(
            s.standards
            + 0.006 * prereq_product(s, ("metrology", "education")) * coordination
            - 0.003 * conflict
        )
        s.logistics = clamp(
            s.logistics
            + 0.006 * prereq_product(s, ("basic_tools", "standards")) * coordination
            - 0.003 * conflict
        )
        s.machine_tools = clamp(
            s.machine_tools
            + 0.006 * prereq_product(s, ("metrology", "materials", "power")) * coordination
            - 0.003 * conflict
        )
        s.precision_industry = clamp(
            s.precision_industry
            + 0.0055 * prereq_product(s, ("machine_tools", "metrology", "standards", "power")) * continuity_support
            - 0.0035 * conflict
            - 0.0015 * elite_capture
        )
        s.computing = clamp(
            s.computing
            + 0.0045 * prereq_product(s, ("precision_industry", "power", "education", "standards")) * continuity_support
            - 0.003 * conflict
            - 0.001 * entertainment_absorption
        )
        s.propulsion = clamp(
            s.propulsion
            + 0.004 * prereq_product(s, ("precision_industry", "materials", "power", "computing")) * continuity_support
            - 0.003 * resource_mismatch
            - 0.0015 * conflict
        )
        s.orbital_systems = clamp(
            s.orbital_systems
            + 0.0035 * prereq_product(s, ("propulsion", "precision_industry", "computing", "logistics", "standards")) * continuity_support
            - 0.0025 * conflict
            - 0.001 * elite_capture
        )

        if s.education < 0.12:
            failure_modes["knowledge_bottleneck"] = failure_modes.get("knowledge_bottleneck", 0) + 1
        if s.machine_tools < 0.10:
            failure_modes["tooling_bottleneck"] = failure_modes.get("tooling_bottleneck", 0) + 1
        if s.standards < 0.10:
            failure_modes["standards_bottleneck"] = failure_modes.get("standards_bottleneck", 0) + 1
        if s.logistics < 0.12:
            failure_modes["logistics_bottleneck"] = failure_modes.get("logistics_bottleneck", 0) + 1

        row = {"generation": g, **{k: round(v, 6) for k, v in asdict(s).items()}}
        history_tail.append(row)
        if len(history_tail) > 8:
            history_tail.pop(0)

    final = asdict(s)
    escape_ready = (
        final["memory"] >= 0.70
        and final["education"] >= 0.68
        and final["standards"] >= 0.65
        and final["precision_industry"] >= 0.62
        and final["computing"] >= 0.58
        and final["propulsion"] >= 0.55
        and final["orbital_systems"] >= 0.52
        and final["logistics"] >= 0.62
    )

    return {
        "schema": "purrtocol-c5-civilizational-memory/v0",
        "evidence_status": "simulation",
        "seed": seed,
        "generations": generations,
        "continuity_conditions": {
            "archive_quality": round(archive_quality, 6),
            "resource_access": round(resource_access, 6),
            "coordination": round(coordination, 6),
            "peace_capacity": round(peace_capacity, 6),
            "surplus": round(surplus, 6),
            "continuity_support": round(continuity_support, 6),
        },
        "escape_ready": escape_ready,
        "final": {k: round(v, 6) for k, v in final.items()},
        "failure_modes": failure_modes,
        "history_tail": history_tail,
        "world_laws": {
            "blueprint_is_not_capability": True,
            "capability_requires_dependency_chain": True,
            "knowledge_can_be_lost_across_generations": True,
            "high_technology_is_socially_fragile": True,
            "escape_route_is_intentionally_rare": True,
            "escape_is_not_required_for_a_valid_run": True,
            "failure_is_not_game_over": True,
            "no_final_civilization": True,
        },
    }


def reference_suite() -> dict:
    # Synthetic calibration bank. It constrains game balance, not real-world probability.
    rows = [simulate(seed) for seed in range(64)]
    successes = [r["seed"] for r in rows if r["escape_ready"]]
    if not 1 <= len(successes) <= 2:
        raise RuntimeError(f"C5 escape rarity drifted outside the intended legendary band: {successes}")
    return {
        "schema": "purrtocol-c5-civilizational-memory-reference/v0",
        "evidence_status": "simulation",
        "seed_bank": 64,
        "successful_seeds": successes,
        "success_count": len(successes),
        "success_fraction": round(len(successes) / 64.0, 6),
        "rarity_contract": {
            "legendary_route": True,
            "minimum_successes_in_reference_bank": 1,
            "maximum_successes_in_reference_bank": 2,
            "success_is_not_required_for_normal_play": True,
        },
        "world_laws": rows[0]["world_laws"],
    }


if __name__ == "__main__":
    print(json.dumps(reference_suite(), ensure_ascii=False, indent=2, sort_keys=True))
