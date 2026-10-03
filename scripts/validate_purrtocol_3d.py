#!/usr/bin/env python3
"""Validate the Purrtocol 3D preflight contract and, when present, the GLB runtime asset."""

from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data" / "purrtocol_3d_contract.json"
CONCEPTS_PATH = ROOT / "data" / "pakenya_concepts.jsonl"
PROMOTIONS_PATH = ROOT / "data" / "pakenya_promotions.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def parse_glb_json(path: Path) -> dict:
    data = path.read_bytes()
    assert len(data) >= 20, "GLB too small"

    magic, version, total_length = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF", f"bad GLB magic: {magic!r}"
    assert version == 2, f"expected GLB version 2, got {version}"
    assert total_length == len(data), (
        f"GLB length header {total_length} != actual {len(data)}"
    )

    offset = 12
    json_chunk = None
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:  # JSON
            json_chunk = chunk
            break

    assert json_chunk is not None, "GLB JSON chunk missing"
    return json.loads(json_chunk.rstrip(b" \t\r\n\x00").decode("utf-8"))


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["schema"] == "purrtocol-3d-contract/v1"
    assert contract["status"] == "preproduction_concept"
    assert contract["concept_event_id"] == "PKE-106"
    assert contract["promotion_gate"]["automatic_promotion"] is False

    concepts = read_jsonl(CONCEPTS_PATH)
    concept = next(row for row in concepts if row["event_id"] == "PKE-106")
    assert concept["status"] == "concept"
    assert concept["timestamp_utc"] is None
    assert concept["source_commit"] is None

    promotions = read_jsonl(PROMOTIONS_PATH)
    promotion = next(
        (row for row in promotions if row["concept_id"] == "PKE-106"),
        None,
    )

    asset = ROOT / contract["runtime_asset"]
    preview = ROOT / contract["runtime_preview"]

    if not asset.exists():
        assert promotion is None, "PKE-106 promoted before the runtime 3D asset exists"
        print("Purrtocol 3D preproduction contract: PASS (asset not yet implemented)")
        return

    assert promotion is not None, "3D runtime asset exists without explicit PKE-106 promotion"
    assert preview.exists(), "3D runtime asset exists without runtime preview"

    gltf = parse_glb_json(asset)
    assert gltf.get("asset", {}).get("version") == "2.0"

    node_names = {
        node.get("name")
        for node in gltf.get("nodes", [])
        if isinstance(node, dict) and node.get("name")
    }
    required_nodes = set(contract["required_nodes"])
    missing_nodes = sorted(required_nodes - node_names)
    assert not missing_nodes, f"missing required runtime nodes: {missing_nodes}"

    animation_names = {
        anim.get("name")
        for anim in gltf.get("animations", [])
        if isinstance(anim, dict) and anim.get("name")
    }
    required_animations = set(contract["required_animations"])
    missing_animations = sorted(required_animations - animation_names)
    assert not missing_animations, f"missing required animations: {missing_animations}"

    print(
        json.dumps(
            {
                "status": "IMPLEMENTATION CONTRACT PASS",
                "asset_bytes": asset.stat().st_size,
                "nodes": len(gltf.get("nodes", [])),
                "animations": sorted(animation_names),
                "promotion_event": promotion["implemented_event_id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
