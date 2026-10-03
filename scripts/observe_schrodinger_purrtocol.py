#!/usr/bin/env python3
"""Observe Schrödinger's Purrtocol.

This is a deterministic epistemic toy, not a quantum simulation.

Two deterministic Purrtocol *concept* manifests are generated from sealed-box
seeds. A separate observation seed deterministically selects one candidate.

Before the first CI run, the repository deliberately does not freeze which
candidate will be selected. After observation, the selected candidate may be
promoted into a real implemented derivative while both sealed-box candidates
remain concept records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from breed_purrtocol import breed

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data" / "purrtocol_schrodinger_contract.json"


def select_index(observer_seed: str, candidate_variant_ids: list[str]) -> tuple[int, str]:
    payload = observer_seed + "\n" + ",".join(candidate_variant_ids)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    index = int(digest[:16], 16) % len(candidate_variant_ids)
    return index, digest


def candidate(label: str, seed: str, parent: str) -> dict[str, Any]:
    result = breed(
        seed,
        parent_variant_id=parent,
        origin_repository="https://github.com/hopeless-t/chatgpt-recovery-dynamics",
        submitted_by="schrodinger-observatory",
    )
    return {
        "label": label,
        "seed": seed,
        "variant_id": result["variant_id"],
        "name": result["name"],
        "status": result["status"],
        "evidence_status": result["evidence_status"],
        "genome": result["genome"],
        "mutations": result["mutations"],
        "preserved_invariants": result["preserved_invariants"],
        "generator": result["generator"],
    }


def observe() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    box = contract["sealed_box"]
    prefix = box["candidate_seed_prefix"]
    parent = box["parent_variant_id"]

    candidates = [
        candidate(label, f"{prefix}:{label}", parent)
        for label in box["candidate_labels"]
    ]
    ids = [row["variant_id"] for row in candidates]
    selected_index, observation_digest = select_index(
        contract["observation"]["observer_seed"],
        ids,
    )
    selected = candidates[selected_index]

    return {
        "schema": "purrtocol-schrodinger-observation/v1",
        "classification": contract["classification"],
        "contract": str(CONTRACT_PATH.relative_to(ROOT)),
        "box": {
            "candidate_count": len(candidates),
            "candidates": candidates,
            "pre_observation_status": "candidate_set_not_yet_promoted",
        },
        "observation": {
            "observer_seed": contract["observation"]["observer_seed"],
            "observation_digest_sha256": observation_digest,
            "selection_index": selected_index,
            "selected_label": selected["label"],
            "selected_candidate_variant_id": selected["variant_id"],
            "selected_candidate_name": selected["name"],
            "selected_genome": selected["genome"],
            "semantics": "deterministic repository observation bookkeeping",
            "quantum_physics_claim": False,
        },
        "promotion_plan": {
            "implemented_variant_id": contract["promotion"]["implemented_variant_id"],
            "selected_candidate_is_copied_into_implemented_variant": True,
            "concept_candidates_remain_concepts": True,
        },
        "interpretation_rules": [
            "The two sealed-box candidates are deterministic concept manifests.",
            "The first observed selection is repository history only after the CI run is read and frozen.",
            "The selection is not quantum measurement or physical wavefunction collapse.",
            "Observation does not imply external human attention or production-system evidence.",
            "Concept candidate != implemented derivative.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()

    result = observe()
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
