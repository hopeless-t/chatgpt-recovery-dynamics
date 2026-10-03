#!/usr/bin/env python3
"""Validate the Purrtocol 3D contract, GLB asset, promotion, and event lineage."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data" / "purrtocol_3d_contract.json"
CONCEPTS_PATH = ROOT / "data" / "pakenya_concepts.jsonl"
PROMOTIONS_PATH = ROOT / "data" / "pakenya_promotions.jsonl"
EVENTS_PATH = ROOT / "data" / "pakenya_events.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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
        if chunk_type == 0x4E4F534A:
            json_chunk = chunk
            break

    assert json_chunk is not None, "GLB JSON chunk missing"
    return json.loads(json_chunk.rstrip(b" \t\r\n\x00").decode("utf-8"))


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["schema"] == "purrtocol-3d-contract/v1"
    assert contract["concept_event_id"] == "PKE-106"
    assert contract["promotion_gate"]["automatic_promotion"] is False

    concepts = read_jsonl(CONCEPTS_PATH)
    concept = next(row for row in concepts if row["event_id"] == "PKE-106")
    # Historical concept provenance remains immutable after promotion.
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
        assert contract["status"] == "preproduction_concept"
        assert promotion is None, "PKE-106 promoted before runtime asset exists"
        print("Purrtocol 3D preproduction contract: PASS")
        return

    assert contract["status"] == "implemented_first_light"
    assert promotion is not None, "3D asset exists without PKE-106 promotion"
    assert preview.exists(), "3D asset exists without runtime preview"

    expected = contract["first_light"]
    data = asset.read_bytes()
    assert len(data) == expected["asset_bytes"]
    actual_sha256 = hashlib.sha256(data).hexdigest()
    assert actual_sha256 == expected["sha256"], (
        f"GLB sha256 mismatch: actual={actual_sha256} expected={expected['sha256']}"
    )

    gltf = parse_glb_json(asset)
    assert gltf.get("asset", {}).get("version") == "2.0"
    extras = gltf.get("asset", {}).get("extras", {})
    assert extras.get("variant_id") == "PKV-CANONICAL"
    assert extras.get("classification") == "visualization_not_evidence"

    node_names = {
        node.get("name")
        for node in gltf.get("nodes", [])
        if isinstance(node, dict) and node.get("name")
    }
    missing_nodes = sorted(set(contract["required_nodes"]) - node_names)
    assert not missing_nodes, f"missing required runtime nodes: {missing_nodes}"

    animation_names = {
        anim.get("name")
        for anim in gltf.get("animations", [])
        if isinstance(anim, dict) and anim.get("name")
    }
    missing_animations = sorted(
        set(contract["required_animations"]) - animation_names
    )
    assert not missing_animations, (
        f"missing required animations: {missing_animations}"
    )

    assert len(gltf.get("nodes", [])) == expected["scene_nodes"]
    assert len(gltf.get("animations", [])) == expected["animation_clips"]
    assert promotion["implemented_event_id"] == expected["implemented_event_id"]

    events = read_jsonl(EVENTS_PATH)
    event = next(
        row for row in events
        if row["event_id"] == promotion["implemented_event_id"]
    )
    assert event["status"] == "implemented"
    assert event["domain"] == "3d"
    assert event["source_commit"] == promotion["implementation_commit"]

    html = preview.read_text(encoding="utf-8")
    assert 'src="../assets/purrtocol/purrtocol.glb"' in html
    assert "model-viewer/4.3.1/model-viewer.min.js" in html
    for name in contract["required_animations"]:
        assert name in html

    print(
        json.dumps(
            {
                "status": "IMPLEMENTATION CONTRACT PASS",
                "asset_bytes": len(data),
                "sha256": expected["sha256"],
                "nodes": len(gltf.get("nodes", [])),
                "animations": sorted(animation_names),
                "promotion_event": promotion["implemented_event_id"],
                "concept_origin_preserved": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
