#!/usr/bin/env python3
"""Validate Purrtocol variant lineage/discovery surfaces without third-party dependencies."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse

from breed_purrtocol import breed

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "recover_dont_amplify",
    "visualization_not_evidence",
    "unknown_not_retry_permission",
    "observer_side_not_omniscient_backend",
    "concept_not_implemented",
    "first_success_not_necessarily_healthy",
    "observe_before_materialize",
}
ID_RE = re.compile(r"^PKV-[A-Z0-9][A-Z0-9._-]*$")
TOP_LEVEL_ALLOWED = {
    "schema", "variant_id", "name", "status", "parent_variant_id", "origin",
    "mutations", "preserved_invariants", "evidence_status", "license",
    "homepage", "assets", "notes", "generator", "genome",
}


def rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def valid_url(value: str) -> bool:
    p = urlparse(value)
    return p.scheme in {"http", "https"} and bool(p.netloc)


def validate_variant(v: dict, *, allow_placeholder: bool = False) -> None:
    assert set(v) <= TOP_LEVEL_ALLOWED, sorted(set(v) - TOP_LEVEL_ALLOWED)
    assert v["schema"] == "purrtocol-variant/v1"
    assert ID_RE.fullmatch(v["variant_id"]), v["variant_id"]
    assert v["status"] in {"canonical", "concept", "implemented", "external"}
    parent = v["parent_variant_id"]
    assert parent is None or ID_RE.fullmatch(parent)
    assert valid_url(v["origin"]["repository_url"])
    assert isinstance(v["mutations"], list)
    kept = v["preserved_invariants"]
    assert len(set(kept)) >= 3
    assert set(kept) <= ALLOWED
    assert v["evidence_status"] in {
        "story", "concept", "implemented_artifact", "observed_repository_history"
    }
    assert v["license"]
    if "generator" in v:
        g = v["generator"]
        assert set(g) == {"name", "version", "seed", "genome_schema", "genome_sha256"}
        assert g["name"] and g["version"] and g["seed"]
        assert g["genome_schema"] == "purrtocol-genome/v1"
        assert re.fullmatch(r"[0-9a-f]{64}", g["genome_sha256"])
        assert isinstance(v.get("genome"), dict) and v["genome"]
    if not allow_placeholder:
        assert "YOU/" not in v["origin"]["repository_url"]


def main() -> None:
    registry = rows(ROOT / "data" / "purrtocol_variants.jsonl")
    ids = [v["variant_id"] for v in registry]
    assert len(ids) == len(set(ids)), "duplicate variant IDs"
    assert "PKV-CANONICAL" in ids

    by_id = {v["variant_id"]: v for v in registry}
    for v in registry:
        validate_variant(v)
        if v["variant_id"] == "PKV-CANONICAL":
            assert v["status"] == "canonical"
            assert v["parent_variant_id"] is None
        else:
            assert v["parent_variant_id"] in by_id, (
                f"local registry parent missing for {v['variant_id']}"
            )

    example = json.loads(
        (ROOT / "examples" / "purrtocol-variant.example.json").read_text(
            encoding="utf-8"
        )
    )
    validate_variant(example, allow_placeholder=True)
    assert example["parent_variant_id"] == "PKV-CANONICAL"

    schema_data = json.loads(
        (ROOT / "data" / "purrtocol_variant_schema.json").read_text(encoding="utf-8")
    )
    schema_pages = json.loads(
        (ROOT / "docs" / "purrtocol-variant.schema.json").read_text(encoding="utf-8")
    )
    assert schema_data == schema_pages, "published schema drift"
    assert schema_pages["$id"].endswith("/purrtocol-variant.schema.json")

    genome_data = json.loads(
        (ROOT / "data" / "purrtocol_genome.json").read_text(encoding="utf-8")
    )
    genome_pages = json.loads(
        (ROOT / "docs" / "purrtocol-genome.json").read_text(encoding="utf-8")
    )
    assert genome_data == genome_pages, "published genome drift"
    assert genome_data["schema"] == "purrtocol-genome/v1"

    theoretical_combinations = math.prod(
        len(options) for options in genome_data["genes"].values()
    )
    assert theoretical_combinations == 199_148_544

    nursery_seed = "pakenya-cambrian-001"
    bred_a = breed(
        nursery_seed,
        origin_repository="https://github.com/hopeless-t/chatgpt-recovery-dynamics",
        submitted_by="nursery-ci",
    )
    bred_b = breed(
        nursery_seed,
        origin_repository="https://github.com/hopeless-t/chatgpt-recovery-dynamics",
        submitted_by="nursery-ci",
    )
    bred_other = breed(
        "pakenya-cambrian-002",
        origin_repository="https://github.com/hopeless-t/chatgpt-recovery-dynamics",
        submitted_by="nursery-ci",
    )
    assert bred_a == bred_b, "same seed must be deterministic"
    assert bred_a["variant_id"] != bred_other["variant_id"]
    validate_variant(bred_a)
    assert bred_a["status"] == "concept"
    assert bred_a["evidence_status"] == "concept"
    assert bred_a["parent_variant_id"] == "PKV-CANONICAL"
    expected_genome_hash = hashlib.sha256(
        (ROOT / "data" / "purrtocol_genome.json").read_bytes()
    ).hexdigest()
    assert bred_a["generator"]["genome_sha256"] == expected_genome_hash
    for gene, value in bred_a["genome"].items():
        assert gene in genome_data["genes"]
        assert value in genome_data["genes"][gene]

    nursery_html = (
        ROOT / "docs" / "purrtocol-nursery" / "index.html"
    ).read_text(encoding="utf-8")
    assert "199,148,544" in nursery_html
    assert "組合せ空間 ≠ implemented variants" in nursery_html
    assert "status:'concept'" in nursery_html
    nursery_md = (
        ROOT / "docs" / "purrtocol-nursery" / "index.md"
    ).read_text(encoding="utf-8")
    assert "199,148,544 theoretical genotype combinations" in nursery_md
    assert "Generated != implemented." in nursery_md

    schrodinger = by_id["PKV-SCHRODINGER-OBS-001"]
    assert schrodinger["status"] == "implemented"
    assert schrodinger["parent_variant_id"] == "PKV-CANONICAL"
    assert schrodinger["evidence_status"] == "implemented_artifact"
    assert schrodinger["origin"]["commit"] == "8016a326c0b324dfd2884926c070228b5f44d36c"
    assert "docs/purrtocol-schrodinger/index.html" in schrodinger["assets"]

    schrodinger_observation = json.loads(
        (ROOT / "data" / "purrtocol_schrodinger_observation.json").read_text(
            encoding="utf-8"
        )
    )
    schrodinger_observation_pages = json.loads(
        (ROOT / "docs" / "purrtocol-schrodinger" / "observation.json").read_text(
            encoding="utf-8"
        )
    )
    assert schrodinger_observation == schrodinger_observation_pages
    assert (
        schrodinger_observation["observation"]["selected_label"] == "A"
    )
    assert (
        schrodinger["genome"]
        == schrodinger_observation["observation"]["selected_genome"]
    )
    candidate_b = next(
        row for row in schrodinger_observation["box"]["candidates"]
        if row["label"] == "B"
    )
    assert candidate_b["variant_id"] not in by_id
    assert schrodinger_observation["observation"]["quantum_physics_claim"] is False

    schrodinger_variant_pages = json.loads(
        (ROOT / "docs" / "purrtocol-schrodinger" / "variant.json").read_text(
            encoding="utf-8"
        )
    )
    assert schrodinger_variant_pages == schrodinger

    discovery = json.loads(
        (ROOT / "docs" / "purrtocol.json").read_text(encoding="utf-8")
    )
    assert discovery["schema"] == "purrtocol-discovery/v1"
    assert discovery["canonical_variant_id"] == "PKV-CANONICAL"
    assert discovery["current_frontier"]["concept_id"] == "PKE-106"
    assert discovery["current_frontier"]["implemented"] is True
    assert discovery["current_frontier"]["status"] == "IMPLEMENTED_FIRST_LIGHT"
    assert discovery["current_frontier"]["implemented_event_id"] == "PKE-033"
    assert discovery["current_frontier"]["sha256"] == "fc667ad30bd69fb794a876ec0acbb9e9efdbdd9c3a3d3f056c1769f4579c6467"
    assert "docs/assets/purrtocol/purrtocol.glb" in by_id["PKV-CANONICAL"]["assets"]
    horizon = discovery["observer_horizon_story"]
    assert horizon["sam"] == "NOT_OBSERVED"
    assert horizon["tibo"] == "NOT_OBSERVED"
    assert horizon["classification"] == "story_only"

    html = (
        ROOT / "docs" / "purrtocol-variant-foundry" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'rel="alternate" type="text/markdown"' in html
    assert 'rel="describedby" href="./llms.txt"' in html
    assert "story mechanic only" in html
    assert "Sam/Tibo observation → NOT OBSERVED" in html

    md = (ROOT / "docs" / "purrtocol-variant-foundry" / "index.md").read_text(
        encoding="utf-8"
    )
    assert "Fork the cat" in md
    assert "NOT OBSERVED" in md

    foundry_llms = (
        ROOT / "docs" / "purrtocol-variant-foundry" / "llms.txt"
    ).read_text(encoding="utf-8")
    assert foundry_llms.startswith("# Purrtocol Variant Foundry\n")
    assert "[Variant JSON Schema]" in foundry_llms

    llms = (ROOT / "docs" / "llms.txt").read_text(encoding="utf-8")
    assert llms.startswith("# ChatGPT Conversation Recovery Dynamics\n")
    assert "\n> " in llms[:500]
    assert "[Purrtocol Variant Foundry]" in llms
    assert "purrtocol-variant-foundry/index.md" in llms

    print(
        json.dumps(
            {
                "status": "PASS",
                "registry_variants": len(registry),
                "schrodinger_variant": "PKV-SCHRODINGER-OBS-001",
                "theoretical_genotype_combinations": theoretical_combinations,
                "nursery_reference_variant_id": bred_a["variant_id"],
                "canonical_root": "PKV-CANONICAL",
                "3d_frontier": "PKE-106 -> PKE-033 IMPLEMENTED_FIRST_LIGHT",
                "observer_horizon": "story_only / NOT_OBSERVED",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
