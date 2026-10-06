#!/usr/bin/env python3
"""Render a lean, partially expressed Purrtocol Second Light descendant.

This strategy reads the same Expression Genome as the full renderer but only
materializes a bounded subset of physical axes. It exists as a real Renderer
Arena competitor, not as a replacement for the full expression renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from generate_purrtocol_second_light import build as build_base
from render_purrtocol_expression import (
    parse_glb,
    pack_glb,
    physical_fingerprint,
    quat_z,
    quat_z_deg,
    rebase_scale_track,
    rebase_z_rotation_track,
    select_genome,
)

REALIZED_AXES = [
    "body_roundness",
    "head_roundness",
    "ear_asymmetry",
    "tail_arc",
    "roughness_bias",
]
TOTAL_EXPRESSION_AXES = 8
LINEAGE_EXPRESSION_COVERAGE = len(REALIZED_AXES) / TOTAL_EXPRESSION_AXES


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def apply_lean_expression(
    gltf: dict[str, Any], binary: bytearray, genome: dict[str, Any]
) -> None:
    exp = genome["expression"]
    silhouette = exp["silhouette"]
    surface = exp["surface"]
    nodes = {node["name"]: node for node in gltf["nodes"]}

    body_r = silhouette["body_roundness"]
    head_r = silhouette["head_roundness"]
    ear_a = silhouette["ear_asymmetry"]
    tail_arc = silhouette["tail_arc"]

    nodes["body"]["scale"] = [
        round(0.58 + 0.28 * body_r, 4),
        round(1.02 - 0.18 * body_r, 4),
        round(0.46 + 0.22 * body_r, 4),
    ]
    nodes["head"]["scale"] = [
        round(0.48 + 0.26 * head_r, 4),
        round(0.70 - 0.18 * head_r, 4),
        round(0.42 + 0.22 * head_r, 4),
    ]

    ear_delta = (ear_a - 0.5) * 0.24
    nodes["ear_L"]["scale"] = [0.20, round(0.34 * (1.0 + ear_delta), 4), 0.16]
    nodes["ear_R"]["scale"] = [0.20, round(0.34 * (1.0 - ear_delta), 4), 0.16]
    nodes["ear_L"]["rotation"] = quat_z(18.0 + 18.0 * ear_delta)
    nodes["ear_R"]["rotation"] = quat_z(-18.0 + 18.0 * ear_delta)

    tail_angle = -60.0 + 50.0 * tail_arc
    nodes["tail"]["rotation"] = quat_z(tail_angle)
    nodes["tail"]["scale"] = [0.15, round(0.42 + 0.25 * tail_arc, 4), 0.15]

    rough = clamp(0.18 + 0.72 * surface["roughness_bias"], 0.20, 0.90)
    gltf["materials"][0]["pbrMetallicRoughness"]["roughnessFactor"] = round(rough, 4)

    idx_to_name = {i: node["name"] for i, node in enumerate(gltf["nodes"])}
    for animation in gltf["animations"]:
        for channel in animation["channels"]:
            sampler = animation["samplers"][channel["sampler"]]
            target = channel["target"]
            node_name = idx_to_name[target["node"]]
            path = target["path"]
            if path == "scale" and node_name == "body":
                rebase_scale_track(
                    gltf,
                    binary,
                    sampler["output"],
                    sampler.get("interpolation", "LINEAR"),
                    nodes["body"]["scale"],
                )
            elif path == "rotation" and node_name in {"tail", "ear_L", "ear_R"}:
                rebase_z_rotation_track(
                    gltf,
                    binary,
                    sampler["output"],
                    sampler.get("interpolation", "LINEAR"),
                    quat_z_deg(nodes[node_name]["rotation"]),
                    1.0,
                )

    # Keep only the minimum lineage/evidence metadata required to bind this
    # physical specimen back to its expression genome. Richer provenance stays
    # in the receipt rather than inflating the GLB.
    gltf["asset"]["extras"] = {
        "variant_id": "PKV-LEAN-" + genome["expression_id"],
        "expression_id": genome["expression_id"],
        "expression_signature": genome["expression_signature"],
        "renderer_profile": "lean-static-continuity/v0",
        "classification": "visualization_not_evidence",
        "canonical": False,
        "human_reaction": "UNKNOWN",
    }


def render(doc: dict[str, Any], index: int, expression_id: str | None) -> tuple[bytes, dict[str, Any]]:
    genome = select_genome(doc, index, expression_id)
    base, base_metrics = build_base()
    gltf, binary = parse_glb(base)
    apply_lean_expression(gltf, binary, genome)
    physical_sha256 = physical_fingerprint(gltf, binary)
    out = pack_glb(gltf, binary)
    metrics = {
        **base_metrics,
        "renderer_id": "lean-expressed-second-light/v0",
        "physical_sha256": physical_sha256,
        "expression_id": genome["expression_id"],
        "expression_signature": genome["expression_signature"],
        "source_organism_id": genome["source_organism_id"],
        "source_species_id": genome["source_species_id"],
        "source_niche_id": genome["source_niche_id"],
        "lineage_expression_coverage": LINEAGE_EXPRESSION_COVERAGE,
        "realized_axes": list(REALIZED_AXES),
        "omitted_axes": [
            "breath_amplitude",
            "step_amplitude",
            "timing_scale",
        ],
    }
    return out, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--genomes", required=True)
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--expression-id")
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt")
    args = parser.parse_args()

    doc = json.loads(Path(args.genomes).read_text(encoding="utf-8"))
    data, metrics = render(doc, args.index, args.expression_id)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)

    if args.receipt:
        receipt = {
            "schema": "purrtocol-lean-renderer-receipt/v0",
            "status": "experimental_implemented_visualization",
            "canonical": False,
            "promotion": "none",
            "evidence_status": "visualization_not_evidence",
            "human_reaction": "UNKNOWN",
            "asset": output.name,
            "asset_bytes": len(data),
            "asset_sha256": hashlib.sha256(data).hexdigest(),
            **metrics,
            "invariants": [
                "Simulation != Evidence",
                "Visualization != Evidence",
                "Generated variant != Canon",
                "UNKNOWN != SUCCESS",
                "Extinct != breeding eligible",
                "Partial expression must be declared",
            ],
        }
        path = Path(args.receipt)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(json.dumps({"bytes": len(data), **metrics}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
