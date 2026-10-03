#!/usr/bin/env python3
"""Deterministic Purrtocol concept breeder.

Produces a concept manifest only. Generation does not imply implementation,
registry inclusion, endorsement, or empirical evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GENOME_PATH = ROOT / "data" / "purrtocol_genome.json"


def digest(seed: str, label: str = "") -> bytes:
    text = seed if not label else f"{seed}:{label}"
    return hashlib.sha256(text.encode("utf-8")).digest()


def choose(seed: str, gene: str, options: list[str]) -> str:
    raw = digest(seed, gene)
    index = int.from_bytes(raw[:8], "big") % len(options)
    return options[index]


def breed(
    seed: str,
    *,
    parent_variant_id: str = "PKV-CANONICAL",
    origin_repository: str = "https://github.com/YOU/YOUR-FORK",
    submitted_by: str = "your-handle",
) -> dict[str, Any]:
    spec = json.loads(GENOME_PATH.read_text(encoding="utf-8"))
    genes = {
        gene: choose(seed, gene, options)
        for gene, options in spec["genes"].items()
    }

    prefix = choose(seed, "name_prefix", spec["name_prefixes"])
    suffix = choose(seed, "name_suffix", spec["name_suffixes"])
    seed_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    genome_hash = hashlib.sha256(
        GENOME_PATH.read_bytes()
    ).hexdigest()

    mutations = [
        f"{gene}={value}"
        for gene, value in genes.items()
    ]

    return {
        "schema": "purrtocol-variant/v1",
        "variant_id": "PKV-SEED-" + seed_hash[:12].upper(),
        "name": f"{prefix}{suffix} / seeded Purrtocol concept",
        "status": "concept",
        "parent_variant_id": parent_variant_id,
        "origin": {
            "repository_url": origin_repository,
            "commit": None,
            "submitted_by": submitted_by,
            "pull_request_url": None,
        },
        "mutations": mutations,
        "preserved_invariants": spec["canonical_invariants"],
        "evidence_status": "concept",
        "license": "MIT",
        "homepage": None,
        "assets": [],
        "generator": {
            "name": "purrtocol-genome-breeder",
            "version": "1",
            "seed": seed,
            "genome_schema": spec["schema"],
            "genome_sha256": genome_hash,
        },
        "genome": genes,
        "notes": (
            "Deterministically generated concept. No implementation is implied. "
            "Fork this manifest, build an artifact, preserve provenance, then submit "
            "for optional upstream lineage indexing."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", required=True)
    ap.add_argument("--parent", default="PKV-CANONICAL")
    ap.add_argument(
        "--origin-repository",
        default="https://github.com/YOU/YOUR-FORK",
    )
    ap.add_argument("--submitted-by", default="your-handle")
    ap.add_argument("--output")
    args = ap.parse_args()

    result = breed(
        args.seed,
        parent_variant_id=args.parent,
        origin_repository=args.origin_repository,
        submitted_by=args.submitted_by,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
