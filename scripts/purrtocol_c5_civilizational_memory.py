#!/usr/bin/env python3
"""C5 Purrtocol Civilization: rare civilizational reconstruction path.

Fictional game/research simulation only.

The reconstruction route is intentionally rare. Knowing a blueprint is not enough;
capabilities must be continuously rebuilt and retained across generations.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict

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
    memory: float = 0.28
    basic_tools: float = 0.20
    metrology: float = 0.08
    materials: float = 0.15
    machine_tools: float = 0.04
    power: float = 0.10
    education: float = 0.12
    standards: float = 0.03
    logistics: float = 0.08
    precision_industry: float = 0.01
    computing: float = 0.00
    propulsion: float = 0.00
    orbital_systems: float = 0.00


def prereq_product(s: State, names: tuple[str, ...]) -> float:
    p = 1.0
    for name in names:
        p *= max(0.0, getattr(s, name))
    return p ** (1.0 / len(names))


def simulate(seed: int, generations: int = 320) -> dict:
    s = State()
    history = []
    failure_modes: dict[str, int] = {}

    for g in range(generations):
        # Persistent social/institutional drag. These are not direct failure events;
        # they slowly erode capabilities that are expensive to preserve.
        elite_capture = 0.18 + 0.20 * h01(seed, "elite", g)
        conflict = 0.06 + 0.18 * h01(seed, "conflict", g)
        superstition = 0.05 + 0.14 * h01(seed, "superstition", g)
        entertainment_absorption = 0.05 + 0.15 * h01(seed, "entertainment", g)
        resource_mismatch = 0.08 + 0.22 * h01(seed, "resource", g)

        # Knowledge retention is hard: education and material surplus are required
        # just to prevent generational forgetting.
        retention = clamp(0.30 + 0.45 * s.education + 0.20 * s.standards - 0.25 * conflict)
        s.memory = clamp(s.memory * (0.985 + 0.02 * retention) + 0.010 * s.education - 0.010 * superstition)

        # Capability gains are gated by dependency chains, not a simple tech tree.
        s.basic_tools = clamp(s.basic_tools + 0.012 * s.memory - 0.006 * resource_mismatch)
        s.metrology = clamp(s.metrology + 0.010 * prereq_product(s, ("memory", "basic_tools", "education")) - 0.005 * conflict)
        s.materials = clamp(s.materials + 0.010 * prereq_product(s, ("basic_tools", "logistics")) - 0.006 * resource_mismatch)
        s.machine_tools = clamp(s.machine_tools + 0.009 * prereq_product(s, ("metrology", "materials", "power")) - 0.006 * conflict)
        s.power = clamp(s.power + 0.008 * prereq_product(s, ("materials", "basic_tools")) - 0.005 * resource_mismatch)
        s.education = clamp(s.education + 0.008 * s.memory - 0.006 * elite_capture - 0.004 * superstition)
        s.standards = clamp(s.standards + 0.008 * prereq_product(s, ("metrology", "education")) - 0.005 * conflict)
        s.logistics = clamp(s.logistics + 0.008 * prereq_product(s, ("basic_tools", "standards")) - 0.005 * conflict)
        s.precision_industry = clamp(s.precision_industry + 0.006 * prereq_product(s, ("machine_tools", "metrology", "standards", "power")) - 0.004 * conflict)
        s.computing = clamp(s.computing + 0.004 * prereq_product(s, ("precision_industry", "power", "education", "standards")) - 0.003 * conflict)
        s.propulsion = clamp(s.propulsion + 0.003 * prereq_product(s, ("precision_industry", "materials", "power", "computing")) - 0.003 * resource_mismatch)
        s.orbital_systems = clamp(s.orbital_systems + 0.0025 * prereq_product(s, ("propulsion", "precision_industry", "computing", "logistics", "standards")) - 0.0025 * conflict)

        # High-level capability is socially fragile and can be cannibalized for short-term survival.
        for name in ("precision_industry", "computing", "propulsion", "orbital_systems"):
            value = getattr(s, name)
            erosion = 0.004 * elite_capture + 0.003 * entertainment_absorption
            setattr(s, name, clamp(value - erosion))

        if s.education < 0.08:
            failure_modes["knowledge_bottleneck"] = failure_modes.get("knowledge_bottleneck", 0) + 1
        if s.machine_tools < 0.06:
            failure_modes["tooling_bottleneck"] = failure_modes.get("tooling_bottleneck", 0) + 1
        if s.standards < 0.05:
            failure_modes["standards_bottleneck"] = failure_modes.get("standards_bottleneck", 0) + 1
        if s.logistics < 0.08:
            failure_modes["logistics_bottleneck"] = failure_modes.get("logistics_bottleneck", 0) + 1

        history.append({"generation": g, **{k: round(v, 6) for k, v in asdict(s).items()}})

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
        "escape_ready": escape_ready,
        "final": {k: round(v, 6) for k, v in final.items()},
        "failure_modes": failure_modes,
        "history_tail": history[-8:],
        "world_laws": {
            "blueprint_is_not_capability": True,
            "capability_requires_dependency_chain": True,
            "knowledge_can_be_lost_across_generations": True,
            "high_technology_is_socially_fragile": True,
            "escape_route_is_intentionally_rare": True,
            "failure_is_not_game_over": True,
            "no_final_civilization": True,
        },
    }


def reference_suite() -> dict:
    # Wide enough seed bank to prove rarity without claiming any real-world rate.
    rows = [simulate(seed) for seed in range(64)]
    successes = [r["seed"] for r in rows if r["escape_ready"]]
    if len(successes) > 3:
        raise RuntimeError(f"C5 escape route became too common: {successes}")
    return {
        "schema": "purrtocol-c5-civilizational-memory-reference/v0",
        "evidence_status": "simulation",
        "seed_bank": 64,
        "successful_seeds": successes,
        "success_count": len(successes),
        "success_fraction": round(len(successes) / 64.0, 6),
        "world_laws": rows[0]["world_laws"],
    }


if __name__ == "__main__":
    print(json.dumps(reference_suite(), ensure_ascii=False, indent=2, sort_keys=True))
