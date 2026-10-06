#!/usr/bin/env python3
"""Deterministic C1 ecology simulator for Purrtocol WORLD.

This is a bounded simulation/projection surface. It does not turn generated
variants into implemented artifacts or empirical evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from breed_purrtocol import GENOME_PATH, breed

MAX_POPULATION = 512
MAX_GENERATIONS = 32

NICHES: tuple[dict[str, Any], ...] = (
    {
        "id": "429-desert",
        "shock": 0.86,
        "observation_bonus": 1.05,
        "projection_pressure": 0.38,
        "resource_pressure": 0.92,
    },
    {
        "id": "distributed-wetlands",
        "shock": 0.67,
        "observation_bonus": 1.18,
        "projection_pressure": 0.43,
        "resource_pressure": 0.78,
    },
    {
        "id": "mobile-dungeon",
        "shock": 0.74,
        "observation_bonus": 1.12,
        "projection_pressure": 0.46,
        "resource_pressure": 0.84,
    },
    {
        "id": "agent-space",
        "shock": 0.79,
        "observation_bonus": 1.22,
        "projection_pressure": 0.50,
        "resource_pressure": 0.82,
    },
    {
        "id": "human-square",
        "shock": 0.49,
        "observation_bonus": 0.96,
        "projection_pressure": 0.58,
        "resource_pressure": 0.71,
    },
)


@dataclass(frozen=True)
class Traits:
    caution: float
    sharing: float
    compression: float
    novelty: float
    efficiency: float
    energy: int


@dataclass(frozen=True)
class Organism:
    organism_id: str
    parent_id: str | None
    generation: int
    niche_id: str
    genome: dict[str, str]
    traits: Traits


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def digest_int(*parts: object) -> int:
    text = ":".join(str(p) for p in parts)
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def organism_id(seed: int, generation: int, ordinal: int, parent_id: str | None) -> str:
    raw = f"{seed}:{generation}:{ordinal}:{parent_id or 'ROOT'}"
    return "PKE-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:14].upper()


def trait_rng(seed: int, label: str) -> random.Random:
    return random.Random(digest_int(seed, label))


def initial_traits(seed: int, ordinal: int) -> Traits:
    rng = trait_rng(seed, f"initial:{ordinal}")
    return Traits(
        caution=round(rng.uniform(0.18, 0.92), 6),
        sharing=round(rng.uniform(0.15, 0.95), 6),
        compression=round(rng.uniform(0.15, 0.95), 6),
        novelty=round(rng.uniform(0.08, 0.96), 6),
        efficiency=round(rng.uniform(0.28, 0.96), 6),
        energy=rng.randint(7, 15),
    )


def mutate_traits(parent: Traits, seed: int, generation: int, ordinal: int) -> Traits:
    rng = trait_rng(seed, f"traits:{generation}:{ordinal}")

    def m(v: float, scale: float = 0.12) -> float:
        return round(clamp(v + rng.uniform(-scale, scale)), 6)

    return Traits(
        caution=m(parent.caution),
        sharing=m(parent.sharing),
        compression=m(parent.compression),
        novelty=m(parent.novelty, 0.15),
        efficiency=m(parent.efficiency),
        energy=max(5, min(18, parent.energy + rng.choice((-1, 0, 0, 0, 1)))),
    )


def mutate_genome(parent: dict[str, str], seed: int, generation: int, ordinal: int) -> tuple[dict[str, str], list[str]]:
    spec = json.loads(GENOME_PATH.read_text(encoding="utf-8"))
    genes = dict(parent)
    gene_names = sorted(spec["genes"])
    rng = trait_rng(seed, f"genome:{generation}:{ordinal}")
    mutation_count = 1 if rng.random() < 0.82 else 2
    changed: list[str] = []
    for gene_name in rng.sample(gene_names, k=mutation_count):
        options = [x for x in spec["genes"][gene_name] if x != genes[gene_name]]
        if not options:
            continue
        before = genes[gene_name]
        after = rng.choice(options)
        genes[gene_name] = after
        changed.append(f"{gene_name}:{before}->{after}")
    return genes, changed


def maybe_migrate(niche_id: str, seed: int, generation: int, ordinal: int) -> tuple[str, bool]:
    rng = trait_rng(seed, f"migration:{generation}:{ordinal}")
    if rng.random() >= 0.09:
        return niche_id, False
    ids = [n["id"] for n in NICHES if n["id"] != niche_id]
    return rng.choice(ids), True


def make_initial_population(seed: int, population: int) -> list[Organism]:
    result: list[Organism] = []
    for ordinal in range(population):
        concept = breed(f"ecology:{seed}:root:{ordinal}")
        result.append(
            Organism(
                organism_id=organism_id(seed, 0, ordinal, None),
                parent_id=None,
                generation=0,
                niche_id=NICHES[ordinal % len(NICHES)]["id"],
                genome=dict(concept["genome"]),
                traits=initial_traits(seed, ordinal),
            )
        )
    return result


def niche_by_id(niche_id: str) -> dict[str, Any]:
    return next(n for n in NICHES if n["id"] == niche_id)


def phenotype_descriptor(org: Organism, *, recovery_ok: bool, projection_ok: bool, retries: int) -> dict[str, Any]:
    if not recovery_ok:
        state_cue = org.genome["blocked_cue"]
    elif not projection_ok:
        state_cue = org.genome["recovering_cue"]
    else:
        state_cue = org.genome["healthy_cue"]

    if org.traits.caution >= 0.70:
        motion = "deliberate-glide"
    elif retries >= 3:
        motion = "restless-loop"
    elif org.traits.novelty >= 0.70:
        motion = "elastic-curiosity"
    else:
        motion = "steady-patrol"

    return {
        "status": "projection-descriptor-only",
        "visual_medium": org.genome["medium"],
        "silhouette": org.genome["silhouette"],
        "state_cue": state_cue,
        "observation_prop": org.genome["observation_prop"],
        "motion_grammar": motion,
        "rendering_note": "Phenotype is derived from simulated ecology state; it is not empirical evidence or a rendered asset.",
    }


def evaluate(org: Organism, seed: int) -> dict[str, Any]:
    niche = niche_by_id(org.niche_id)
    rng = trait_rng(seed, f"evaluate:{org.generation}:{org.organism_id}")
    t = org.traits

    ambiguity = clamp(niche["shock"] * rng.uniform(0.62, 1.24))
    observation = round(t.energy * ambiguity * t.caution * 0.52 * niche["observation_bonus"])
    blind_pressure = t.energy * ambiguity * (1.0 - t.caution)
    retries = round(blind_pressure * 0.62)
    compute = max(1, round(t.energy * (0.28 + 0.44 * t.efficiency)))
    memory = max(1, round(t.energy * (0.08 + 0.17 * t.sharing)))
    useful = compute * (0.36 + 0.42 * t.efficiency + 0.16 * t.sharing) + observation * 0.31
    amplification = retries / max(1, compute + observation)

    recovery_threshold = 0.54
    recovery_ok = amplification <= recovery_threshold
    projection_score = clamp(
        0.29 * t.compression
        + 0.26 * t.novelty
        + 0.22 * t.sharing
        + 0.13 * t.efficiency
        + 0.10 * rng.random()
    )
    projection_ok = projection_score >= niche["projection_pressure"]
    value = useful - (1.03 * retries) - (0.30 * memory) - (niche["resource_pressure"] * compute * 0.14)
    resource_ok = value > 0
    survives = recovery_ok and projection_ok and resource_ok

    if not recovery_ok:
        extinction_reason = "recovery-invalid"
    elif not projection_ok:
        extinction_reason = "projection-failed"
    elif not resource_ok:
        extinction_reason = "resource-negative"
    else:
        extinction_reason = None

    fitness = (
        (1.0 - min(1.0, amplification)) * 0.35
        + projection_score * 0.27
        + t.efficiency * 0.23
        + t.sharing * 0.15
    )
    if not survives:
        fitness = 0.0

    return {
        "organism_id": org.organism_id,
        "parent_id": org.parent_id,
        "generation": org.generation,
        "niche_id": org.niche_id,
        "genome": dict(org.genome),
        "traits": asdict(t),
        "ambiguity": round(ambiguity, 6),
        "observation": observation,
        "retries": retries,
        "compute": compute,
        "memory": memory,
        "retry_amplification": round(amplification, 6),
        "recovery_gate": recovery_ok,
        "projection_score": round(projection_score, 6),
        "projection_gate": projection_ok,
        "resource_value": round(value, 6),
        "resource_gate": resource_ok,
        "survives": survives,
        "extinction_reason": extinction_reason,
        "fitness": round(fitness, 6),
        "phenotype": phenotype_descriptor(
            org,
            recovery_ok=recovery_ok,
            projection_ok=projection_ok,
            retries=retries,
        ),
    }


def species_signature(row: dict[str, Any]) -> str:
    g = row["genome"]
    raw = "|".join(
        (
            row["niche_id"],
            g["silhouette"],
            g["temperament"],
            g["narrative_job"],
            g["mutation_class"],
        )
    )
    return "PKS-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()


def reproduce(
    survivors: list[tuple[Organism, dict[str, Any]]],
    *,
    seed: int,
    generation: int,
    target_population: int,
) -> tuple[list[Organism], list[dict[str, Any]]]:
    ranked = sorted(survivors, key=lambda item: (-item[1]["fitness"], item[0].organism_id))
    next_population: list[Organism] = []
    births: list[dict[str, Any]] = []
    for ordinal in range(target_population):
        parent, _ = ranked[ordinal % len(ranked)]
        genome, mutations = mutate_genome(parent.genome, seed, generation, ordinal)
        niche_id, migrated = maybe_migrate(parent.niche_id, seed, generation, ordinal)
        child = Organism(
            organism_id=organism_id(seed, generation, ordinal, parent.organism_id),
            parent_id=parent.organism_id,
            generation=generation,
            niche_id=niche_id,
            genome=genome,
            traits=mutate_traits(parent.traits, seed, generation, ordinal),
        )
        next_population.append(child)
        births.append(
            {
                "organism_id": child.organism_id,
                "parent_id": parent.organism_id,
                "generation": generation,
                "niche_id": niche_id,
                "migrated": migrated,
                "mutations": mutations,
            }
        )
    return next_population, births


def run(seed: int, population: int, generations: int) -> dict[str, Any]:
    current = make_initial_population(seed, population)
    ledger: list[dict[str, Any]] = []
    births: list[dict[str, Any]] = []
    generation_summaries: list[dict[str, Any]] = []
    extinct_reasons: Counter[str] = Counter()

    for generation in range(generations):
        evaluated: list[tuple[Organism, dict[str, Any]]] = []
        niche_counts: dict[str, Counter[str]] = defaultdict(Counter)

        for org in current:
            row = evaluate(org, seed)
            row["species_id"] = species_signature(row)
            ledger.append(row)
            evaluated.append((org, row))
            key = "survived" if row["survives"] else row["extinction_reason"]
            niche_counts[org.niche_id][key] += 1
            if row["extinction_reason"]:
                extinct_reasons[row["extinction_reason"]] += 1

        survivors = [(org, row) for org, row in evaluated if row["survives"]]
        species_alive = sorted({row["species_id"] for _, row in survivors})
        generation_summaries.append(
            {
                "generation": generation,
                "population": len(current),
                "survivors": len(survivors),
                "extinct": len(current) - len(survivors),
                "species_alive": len(species_alive),
                "niches": {k: dict(sorted(v.items())) for k, v in sorted(niche_counts.items())},
            }
        )

        if generation == generations - 1 or not survivors:
            break
        current, new_births = reproduce(
            survivors,
            seed=seed,
            generation=generation + 1,
            target_population=population,
        )
        births.extend(new_births)

    final_generation = generation_summaries[-1]["generation"] if generation_summaries else 0
    final_rows = [row for row in ledger if row["generation"] == final_generation]
    final_survivors = [row for row in final_rows if row["survives"]]
    final_species = Counter(row["species_id"] for row in final_survivors)

    return {
        "schema": "purrtocol-ecology-run/v0",
        "evidence_status": "simulation",
        "projection_status": "phenotype-descriptors-only",
        "seed": seed,
        "bounds": {
            "population": population,
            "generations_requested": generations,
            "max_population": MAX_POPULATION,
            "max_generations": MAX_GENERATIONS,
        },
        "world_laws": {
            "projection_cannot_rescue_recovery_invalid": True,
            "simulation_not_evidence": True,
            "generated_concept_not_implemented": True,
            "no_final_boss": True,
        },
        "niches": list(NICHES),
        "summary": {
            "generations_completed": len(generation_summaries),
            "final_population_evaluated": len(final_rows),
            "final_survivors": len(final_survivors),
            "final_species": len(final_species),
            "extinction_reasons": dict(sorted(extinct_reasons.items())),
            "dominant_final_species": (
                sorted(final_species.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                if final_species
                else None
            ),
        },
        "generation_summaries": generation_summaries,
        "births": births,
        "ledger": ledger,
        "observer_effect": {
            "status": "modeled-boundary",
            "statement": "Observing propagation can itself create instrumentation activity; measurement footprint must be separated from external ecology.",
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=41)
    p.add_argument("--population", type=int, default=48)
    p.add_argument("--generations", type=int, default=5)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    if not 1 <= args.population <= MAX_POPULATION:
        p.error(f"population must be between 1 and {MAX_POPULATION}")
    if not 1 <= args.generations <= MAX_GENERATIONS:
        p.error(f"generations must be between 1 and {MAX_GENERATIONS}")

    result = run(args.seed, args.population, args.generations)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
