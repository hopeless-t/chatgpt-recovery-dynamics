#!/usr/bin/env python3
"""Compile Graphic Evolution profiles into bounded Second Light expression genomes.

Expression genomes are deterministic implementation parameters, not rendered assets
and not empirical observations.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

MOTION = {
    "deliberate-glide": (0.07, 0.34, 0.42, 1.18),
    "restless-loop": (0.14, 0.78, 0.76, 0.86),
    "elastic-curiosity": (0.16, 0.86, 0.68, 0.92),
    "steady-patrol": (0.10, 0.54, 0.58, 1.00),
}
MEDIUM = {
    "voxel-cat": (0.34, 0.38, 0.76),
    "lowpoly-cat": (0.58, 0.56, 0.60),
    "line-art-cat": (0.76, 0.70, 0.42),
    "terminal-cat": (0.48, 0.52, 0.30),
    "paper-cat": (0.40, 0.46, 0.72),
}
NICHE_EAR = {
    "429-desert": 0.76,
    "distributed-wetlands": 0.42,
    "mobile-dungeon": 0.62,
    "agent-space": 0.28,
    "human-square": 0.50,
}

def stable_jitter(key: str, span: float = 0.08) -> float:
    raw = hashlib.sha256(key.encode("utf-8")).digest()[0] / 255.0
    return (raw - 0.5) * 2.0 * span

def clamp(v: float, lo: float, hi: float) -> float:
    return round(max(lo, min(hi, v)), 4)

def compile_profile(profile: dict) -> dict:
    src = profile["source"]
    phenotype = profile["phenotype"]
    render = profile["render_plan"]
    oid = src["organism_id"]
    motion = MOTION.get(phenotype.get("motion_grammar"), (0.10, 0.50, 0.55, 1.0))
    medium = MEDIUM.get(phenotype.get("visual_medium"), (0.52, 0.52, 0.55))
    j = stable_jitter(oid)
    survives = bool(src["survives"])
    expression = {
        "silhouette": {
            "body_roundness": clamp(medium[0] + j, 0.20, 0.90),
            "head_roundness": clamp(medium[1] - j / 2, 0.20, 0.90),
            "ear_asymmetry": clamp(NICHE_EAR.get(src["niche_id"], 0.5) + j, 0.10, 0.90),
            "tail_arc": clamp(0.52 + motion[1] * 0.32 + j, 0.20, 0.95),
        },
        "motion": {
            "breath_amplitude": clamp(motion[0] + j / 5, 0.03, 0.22),
            "tail_secondary_motion": clamp(motion[1] + j, 0.15, 0.95),
            "step_amplitude": clamp(motion[2] + j / 2, 0.20, 0.90),
            "timing_scale": clamp(motion[3] - j, 0.72, 1.30),
        },
        "surface": {
            "roughness_bias": clamp(medium[2] + j / 2, 0.20, 0.90),
            "texture_budget": 0,
        },
        "presentation": {
            "regime": render["presentation_regime"],
            "camera_grammar": render["camera_grammar"],
            "lighting_grammar": render["lighting_grammar"],
            "production_intent": render["production_intent"],
        },
    }
    signature = hashlib.sha256(json.dumps(expression, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "expression_id": "PKX-" + signature[:12].upper(),
        "source_profile_id": profile["profile_id"],
        "source_organism_id": oid,
        "source_species_id": src["species_id"],
        "source_generation": src["generation"],
        "source_niche_id": src["niche_id"],
        "survives": survives,
        "breeding_eligible": survives,
        "implementation_target": "purrtocol-second-light-generator/v0" if survives else "museum-extinction-memorial-only",
        "expression": expression,
        "expression_signature": signature,
        "evidence_status": "simulation-derived-proposal",
        "human_reaction": "UNKNOWN",
        "canonical": False,
    }

def build(manifest: dict) -> dict:
    if manifest.get("schema") != "purrtocol-graphic-manifest/v0":
        raise ValueError("expected purrtocol-graphic-manifest/v0")
    if manifest.get("evidence_status") != "simulation":
        raise ValueError("only simulation-labeled graphic manifests are accepted")
    genomes = [compile_profile(p) for p in manifest["profiles"]]
    return {
        "schema": "purrtocol-expression-genome/v0",
        "status": "proposed-expression-parameters",
        "target": "Purrtocol Second Light experimental lane",
        "source_manifest_schema": manifest["schema"],
        "world_laws": {
            "expression_is_not_rendered_asset": True,
            "visualization_is_not_evidence": True,
            "generated_variant_is_not_canon": True,
            "human_reaction_stays_unknown_until_observed": True,
            "technical_quality_is_not_humor": True,
        },
        "summary": {
            "genomes": len(genomes),
            "breeding_eligible": sum(g["breeding_eligible"] for g in genomes),
            "memorial_only": sum(not g["breeding_eligible"] for g in genomes),
        },
        "genomes": genomes,
    }

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)
    a=p.parse_args()
    manifest=json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    out=build(manifest)
    path=Path(a.output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(out["summary"], sort_keys=True))

if __name__ == "__main__": main()
