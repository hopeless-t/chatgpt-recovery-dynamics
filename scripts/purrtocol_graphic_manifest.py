#!/usr/bin/env python3
"""Project Purrtocol C1 ecology history into bounded graphic render plans.

The output is a deterministic render manifest, not a rendered asset and not
empirical evidence. Human reaction remains UNKNOWN until actually observed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

MAX_PROFILES = 24
DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "data" / "purrtocol_3d_contract.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def choose_rows(ecology: dict[str, Any], count: int) -> list[dict[str, Any]]:
    ledger = ecology["ledger"]
    if not ledger:
        return []

    final_generation = max(row["generation"] for row in ledger)
    final_rows = [row for row in ledger if row["generation"] == final_generation]
    survivors = [row for row in final_rows if row["survives"]]

    # Prefer one representative per surviving species before repeats.
    species_counts = Counter(row["species_id"] for row in survivors)
    ranked = sorted(
        survivors,
        key=lambda row: (
            -species_counts[row["species_id"]],
            -row["fitness"],
            row["species_id"],
            row["organism_id"],
        ),
    )
    selected: list[dict[str, Any]] = []
    seen_species: set[str] = set()
    for row in ranked:
        if row["species_id"] in seen_species:
            continue
        selected.append(row)
        seen_species.add(row["species_id"])
        if len(selected) >= count:
            return selected

    for row in ranked:
        if row in selected:
            continue
        selected.append(row)
        if len(selected) >= count:
            return selected

    # If final survivors are sparse, add distinct extinction exemplars. They are
    # explicitly marked memorial-only and can never be mistaken for survivors.
    extinct = sorted(
        (row for row in final_rows if not row["survives"]),
        key=lambda row: (row["extinction_reason"], -row["fitness"], row["organism_id"]),
    )
    seen_reasons: set[str] = set()
    for row in extinct:
        reason = row["extinction_reason"]
        if reason in seen_reasons:
            continue
        selected.append(row)
        seen_reasons.add(reason)
        if len(selected) >= count:
            break
    return selected


def camera_grammar(row: dict[str, Any]) -> str:
    motion = row["phenotype"]["motion_grammar"]
    return {
        "deliberate-glide": "cinematic-slow-dolly",
        "restless-loop": "locked-off-deadpan-loop",
        "elastic-curiosity": "serious-product-orbit",
        "steady-patrol": "documentary-side-track",
    }.get(motion, "neutral-three-quarter")


def lighting_grammar(row: dict[str, Any]) -> str:
    niche = row["niche_id"]
    return {
        "429-desert": "hard-rim-warning-haze",
        "distributed-wetlands": "soft-cyan-state-reflections",
        "mobile-dungeon": "low-key-intermittent-beacon",
        "agent-space": "clean-black-void-instrument-light",
        "human-square": "dead-serious-commercial-keylight",
    }.get(niche, "neutral-studio")


def material_grammar(row: dict[str, Any]) -> str:
    medium = row["phenotype"]["visual_medium"]
    return {
        "voxel-cat": "matte-voxel-clean",
        "lowpoly-cat": "lowpoly-studio-clean",
        "line-art-cat": "toon-outline-projection",
        "terminal-cat": "emissive-terminal-projection",
        "paper-cat": "paper-diorama-projection",
    }.get(medium, "contract-neutral")


def projection_regime(row: dict[str, Any]) -> str:
    t = row["traits"]
    if row["survives"] and t["novelty"] >= 0.68 and row["projection_score"] >= 0.58:
        return "serious-midnight-commercial"
    if not row["survives"]:
        return "museum-extinction-memorial"
    if row["niche_id"] == "human-square":
        return "deadpan-public-information-film"
    return "clinical-recovery-demo"


def make_profile(row: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    regime = projection_regime(row)
    return {
        "profile_id": "PKG-" + hashlib.sha256(row["organism_id"].encode("utf-8")).hexdigest()[:12].upper(),
        "source": {
            "organism_id": row["organism_id"],
            "species_id": row["species_id"],
            "parent_id": row["parent_id"],
            "generation": row["generation"],
            "niche_id": row["niche_id"],
            "survives": row["survives"],
            "extinction_reason": row["extinction_reason"],
            "evidence_status": "simulation",
        },
        "phenotype": row["phenotype"],
        "render_plan": {
            "status": "proposed-render-plan",
            "rig_profile": "purrtocol-first-light-semantic-compatible",
            "presentation_regime": regime,
            "production_intent": "play-straight",
            "camera_grammar": camera_grammar(row),
            "lighting_grammar": lighting_grammar(row),
            "material_grammar": material_grammar(row),
            "motion_grammar": row["phenotype"]["motion_grammar"],
            "semantic_animation_contract": list(contract["required_animations"]),
            "semantic_nodes_contract": list(contract["required_nodes"]),
            "audio_grammar": "silent-by-default; optional restrained broadcast-ident",
            "loop_policy": "seamless-when-semantically-safe",
        },
        "projection_axes": {
            "status": "heuristic-not-human-rated",
            "technical_fidelity_target": "high",
            "deadpan_seriousness": "high" if regime == "serious-midnight-commercial" else "medium",
            "visual_surprise": "high" if row["traits"]["novelty"] >= 0.68 else "medium",
            "semantic_readability": "required",
        },
        "human_reaction": {
            "status": "UNKNOWN",
            "rule": "Do not infer humor, comprehension, or replay value from the render plan. Observe humans later.",
        },
        "promotion": {
            "automatic": False,
            "implemented_asset": False,
            "requires_rendered_asset": True,
            "requires_runtime_validation": True,
        },
    }


def build(ecology_path: Path, contract_path: Path, count: int) -> dict[str, Any]:
    ecology = load_json(ecology_path)
    contract = load_json(contract_path)
    if ecology.get("schema") != "purrtocol-ecology-run/v0":
        raise ValueError("expected purrtocol-ecology-run/v0 input")
    if ecology.get("evidence_status") != "simulation":
        raise ValueError("graphic projection only accepts simulation-labeled C1 ecology input")
    if contract.get("schema") != "purrtocol-3d-contract/v1":
        raise ValueError("expected purrtocol-3d-contract/v1")

    selected = choose_rows(ecology, count)
    profiles = [make_profile(row, contract) for row in selected]
    regimes = Counter(p["render_plan"]["presentation_regime"] for p in profiles)
    return {
        "schema": "purrtocol-graphic-manifest/v0",
        "evidence_status": "simulation",
        "projection_status": "render-plan-only",
        "source_ecology": {
            "sha256": sha256_file(ecology_path),
            "schema": ecology["schema"],
            "seed": ecology["seed"],
        },
        "semantic_contract": {
            "path": str(contract_path).replace("\\", "/"),
            "schema": contract["schema"],
            "required_animations": list(contract["required_animations"]),
            "required_nodes": list(contract["required_nodes"]),
            "first_light_baseline": {
                "asset_bytes": contract["first_light"]["asset_bytes"],
                "scene_nodes": contract["first_light"]["scene_nodes"],
                "animation_clips": contract["first_light"]["animation_clips"],
                "textures": contract["first_light"]["textures"],
            },
        },
        "world_laws": {
            "visualization_is_not_evidence": True,
            "simulation_is_not_evidence": True,
            "human_reaction_stays_unknown_until_observed": True,
            "technical_quality_is_not_humor": True,
            "no_automatic_promotion": True,
            "play_the_absurd_subject_straight": True,
        },
        "summary": {
            "profiles": len(profiles),
            "presentation_regimes": dict(sorted(regimes.items())),
            "implemented_assets": 0,
        },
        "profiles": profiles,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ecology", required=True)
    p.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    p.add_argument("--count", type=int, default=6)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    if not 1 <= args.count <= MAX_PROFILES:
        p.error(f"count must be between 1 and {MAX_PROFILES}")

    result = build(Path(args.ecology), Path(args.contract), args.count)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
