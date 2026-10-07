#!/usr/bin/env python3
"""Small deterministic bootstrap simulator for Purrtocol Civilization.

Simulation/projection only. It makes no claims about production systems.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import purrtocol_c2_knowledge_institutions as c2_knowledge
import purrtocol_c3_stratification_oracle as c3_stratification
import purrtocol_c4_belief_leisure as c4_belief_leisure
import purrtocol_genesis_microcosm as genesis_microcosm

ROLES = ("Observer", "Executor", "CacheKeeper", "Broker", "Archivist", "Teacher", "Projector", "Auditor")


@dataclass
class Cat:
    cat_id: str
    role: str
    caution: float
    sharing: float
    compression: float
    novelty: float
    energy: int


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def make_cat(rng: random.Random, n: int) -> Cat:
    return Cat(
        cat_id=f"PKC-{n:03d}",
        role=ROLES[n % len(ROLES)],
        caution=rng.random(),
        sharing=rng.random(),
        compression=rng.random(),
        novelty=rng.random(),
        energy=rng.randint(6, 14),
    )


def genesis_reference_summary() -> dict:
    reference = genesis_microcosm.reference_suite()
    micro = reference["micro_twin"]
    if reference["same_macro_condition_distinct_signatures"] < 6:
        raise RuntimeError("Genesis macro-equivalent worlds became too uniform")
    if micro["allocation_history_mismatches"] < 12:
        raise RuntimeError("Genesis micro perturbation stopped propagating")
    if micro["baseline_final"]["dominant_niche"] == micro["perturbed_final"]["dominant_niche"]:
        raise RuntimeError("Genesis reference twins no longer diverge in dominant niche")
    if reference["environment_conditioned_founder_expression"] != {
        "hazard-world": "caution",
        "connected-world": "sharing",
        "sparse-volatile-world": "compression",
        "heterogeneous-world": "novelty",
    }:
        raise RuntimeError("Genesis environment-conditioned founder expression drifted")
    return reference


def c2_reference_summary() -> dict:
    reference = c2_knowledge.build(60)
    outcomes = {
        scenario_id: row["outcome"]
        for scenario_id, row in reference["scenarios"].items()
    }
    expected = {
        "late-abolition-after-knowledge-boom": "REVOLUTION",
        "adaptive-reform-before-break": "REFORMED_ORDER",
        "early-knowledge-lockdown": "AUTHORITARIAN_STAGNATION",
    }
    if outcomes != expected:
        raise RuntimeError(f"C2 reference counterfactual drifted: {outcomes!r}")

    late = reference["scenarios"]["late-abolition-after-knowledge-boom"]
    reform = reference["scenarios"]["adaptive-reform-before-break"]
    early = reference["scenarios"]["early-knowledge-lockdown"]
    if not any(e["event"] == "FORMAL_SCHOOL_SYSTEM_ABOLISHED" for e in late["events"]):
        raise RuntimeError("C2 late-abolition fixture never abolished formal schooling")
    if not any(e["event"] == "UNDERGROUND_EDUCATION_NETWORK" for e in late["events"]):
        raise RuntimeError("C2 late-abolition fixture never formed underground education")
    if reform["policy_counts"].get("REFORM_COMPACT", 0) <= 0:
        raise RuntimeError("C2 reform fixture never exercised REFORM_COMPACT")
    if early["final_state"]["citizen_knowledge"] >= 0.30:
        raise RuntimeError("C2 early-lockdown fixture unexpectedly retained high public knowledge")

    return {
        "schema": reference["schema"],
        "evidence_status": reference["evidence_status"],
        "outcomes": outcomes,
        "world_laws": reference["world_laws"],
        "counterexample_contract": {
            "abolition_is_not_universal_revolution_trigger": True,
            "reform_can_avoid_revolution_in_reference_fixture": True,
            "early_lockdown_can_avoid_revolution_but_stagnate": True,
            "late_abolition_can_leave_underground_learning": True,
        },
    }


def c3_reference_summary() -> dict:
    reference = c3_stratification.build_reference()
    no_oracle = reference["scenarios"]["closed-dystopia-no-oracle"]
    weak = reference["scenarios"]["closed-dystopia-weak-oracle"]
    repeated = reference["scenarios"]["closed-dystopia-three-whispers"]

    for row in (no_oracle, weak, repeated):
        if row["outcome"] != "STABLE_DYSTOPIA":
            raise RuntimeError(f"C3 reference material regime drifted: {row['scenario_id']}={row['outcome']}")
        if abs(row["accounting"]["conservation_residual"]) > 1e-8:
            raise RuntimeError("C3 wealth-flow conservation drifted")
        final = row["final_state"]
        if final["labor_hours"] < 13.0 or final["ration"] >= 0.70:
            raise RuntimeError("C3 harsh-labor fixture stopped being materially harsh")
        if final["elite_wealth_share"] < 0.80 or final["elite_leisure_hours"] < 10.0:
            raise RuntimeError("C3 elite-luxury contrast disappeared")
        if final["mean_health_debtors"] > 0.20:
            raise RuntimeError("C3 debt-labor hazard fixture became unexpectedly mild")

    if no_oracle["oracle_contract"]["unique_receivers"]:
        raise RuntimeError("C3 no-oracle world reported an oracle receiver")
    if weak["oracle_contract"]["pulses_used"] != 1:
        raise RuntimeError("C3 weak-oracle fixture lost its single pulse")
    if not (0.0 < weak["oracle_contract"]["unique_receiver_fraction"] <= 0.05):
        raise RuntimeError("C3 oracle stopped being rare")
    if weak["final_state"]["stigmatised_prophets"] < 1:
        raise RuntimeError("C3 weak-oracle fixture lost suspicious-prophet path")
    if repeated["oracle_contract"]["pulses_used"] != 3:
        raise RuntimeError("C3 repeated-whisper fixture lost bounded three-pulse path")
    if repeated["oracle_contract"]["unique_receiver_fraction"] > 0.05:
        raise RuntimeError("C3 repeated whispers made oracle reception too common")

    return {
        "schema": reference["schema"],
        "evidence_status": reference["evidence_status"],
        "outcomes": {
            scenario_id: row["outcome"]
            for scenario_id, row in reference["scenarios"].items()
        },
        "oracle_reference": {
            "weak_unique_receivers": weak["oracle_contract"]["unique_receivers"],
            "weak_unique_receiver_fraction": weak["oracle_contract"]["unique_receiver_fraction"],
            "weak_stigmatised_prophets": weak["final_state"]["stigmatised_prophets"],
            "repeated_stigmatised_prophets": repeated["final_state"]["stigmatised_prophets"],
        },
        "material_reference": {
            "labor_hours": weak["final_state"]["labor_hours"],
            "ration": weak["final_state"]["ration"],
            "hazard": weak["final_state"]["hazard"],
            "elite_wealth_share": weak["final_state"]["elite_wealth_share"],
            "elite_leisure_hours": weak["final_state"]["elite_leisure_hours"],
            "debtor_mean_debt": weak["final_state"]["debtor_mean_debt"],
            "mean_health_debtors": weak["final_state"]["mean_health_debtors"],
        },
        "world_laws": weak["world_laws"],
    }


def c4_reference_summary() -> dict:
    reference = c4_belief_leisure.build_reference()
    receivers = reference["oracle"]["genuine_receivers"]
    false_claimants = reference["oracle"]["false_claimants"]
    if receivers != [19, 89]:
        raise RuntimeError(f"C4 genuine receiver fixture drifted: {receivers!r}")
    if false_claimants != [10, 52]:
        raise RuntimeError(f"C4 false-claim fixture drifted: {false_claimants!r}")
    if abs(reference["accounting"]["conservation_residual"]) > 1e-8:
        raise RuntimeError("C4 wealth-flow conservation drifted")
    strata = reference["entertainment"]["strata"]
    if not (
        strata["elite"]["mean_leisure_spend"]
        > strata["laborer"]["mean_leisure_spend"]
        > strata["debtor"]["mean_leisure_spend"]
    ):
        raise RuntimeError("C4 leisure-resource hierarchy drifted")
    if not (
        strata["debtor"]["mean_cultural_output"]
        > strata["laborer"]["mean_cultural_output"]
        > strata["elite"]["mean_cultural_output"]
    ):
        raise RuntimeError("C4 improvised-culture fixture drifted")
    if strata["debtor"]["mean_escapism"] <= strata["laborer"]["mean_escapism"]:
        raise RuntimeError("C4 constrained-escapism fixture drifted")
    if not any((not row["genuine_receiver"]) and row["followers"] > 0 for row in reference["movements"]):
        raise RuntimeError("C4 false claimant no longer converts claim into social power")
    return {
        "schema": reference["schema"],
        "evidence_status": reference["evidence_status"],
        "genuine_receivers": receivers,
        "false_claimants": false_claimants,
        "movements": reference["movements"],
        "entertainment_strata": strata,
        "world_laws": reference["world_laws"],
    }


def run(seed: int, population: int, shock: float) -> dict:
    rng = random.Random(seed)
    cats = [make_cat(rng, i) for i in range(population)]
    ledger = []
    survivors = []
    total_retries = 0
    total_value = 0.0

    for cat in cats:
        ambiguity = clamp(shock * (0.55 + 0.9 * rng.random()))
        observe = round(cat.energy * ambiguity * cat.caution * 0.45)
        blind_retry_pressure = cat.energy * ambiguity * (1.0 - cat.caution)
        retries = round(blind_retry_pressure * 0.55)
        compute = max(1, round(cat.energy * (0.25 + 0.35 * rng.random())))
        memory = max(1, round(cat.energy * (0.08 + 0.18 * cat.sharing)))
        useful = compute * (0.45 + 0.35 * cat.sharing) + observe * 0.35
        amplification = retries / max(1, compute + observe)
        recovery_ok = amplification <= 0.60

        explanation = clamp(0.30 * cat.compression + 0.25 * cat.novelty + 0.25 * cat.sharing + 0.20 * rng.random())
        projection_ok = explanation >= 0.42
        value = useful - 0.9 * retries - 0.25 * memory
        survives = recovery_ok and projection_ok and value > 0
        if survives:
            survivors.append(cat.cat_id)
        total_retries += retries
        total_value += value
        ledger.append({
            **asdict(cat),
            "ambiguity": round(ambiguity, 4),
            "observe": observe,
            "retries": retries,
            "compute": compute,
            "memory": memory,
            "retry_amplification": round(amplification, 4),
            "recovery_gate": recovery_ok,
            "projection_score": round(explanation, 4),
            "projection_gate": projection_ok,
            "value": round(value, 4),
            "survives": survives,
        })

    role_survivors = {}
    for row in ledger:
        if row["survives"]:
            role_survivors[row["role"]] = role_survivors.get(row["role"], 0) + 1
    dominant = max(role_survivors, key=role_survivors.get) if role_survivors else None

    news_facts = {
        "population": population,
        "survivors": len(survivors),
        "extinct": population - len(survivors),
        "total_retries": total_retries,
        "total_value": round(total_value, 4),
        "dominant_survivor_role": dominant,
    }
    return {
        "schema": "purrtocol-civilization-season/v0",
        "evidence_status": "simulation",
        "seed": seed,
        "environment": {"shock": shock, "resources": "bounded"},
        "news_facts": news_facts,
        "survivor_ids": survivors,
        "ledger": ledger,
        "genesis_microcosm_reference": genesis_reference_summary(),
        "c2_knowledge_institutions_reference": c2_reference_summary(),
        "c3_stratification_oracle_reference": c3_reference_summary(),
        "c4_belief_leisure_reference": c4_reference_summary(),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=27)
    p.add_argument("--population", type=int, default=32)
    p.add_argument("--shock", type=float, default=0.65)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    if not 1 <= args.population <= 4096:
        p.error("population must be between 1 and 4096")
    if not 0.0 <= args.shock <= 1.0:
        p.error("shock must be between 0 and 1")
    result = run(args.seed, args.population, args.shock)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["news_facts"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
