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


def parse_glb(path: Path) -> tuple[dict, bytes]:
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
    bin_chunk = b""
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            json_chunk = chunk
        elif chunk_type == 0x004E4942:
            bin_chunk = chunk

    assert json_chunk is not None, "GLB JSON chunk missing"
    return (
        json.loads(json_chunk.rstrip(b" \t\r\n\x00").decode("utf-8")),
        bin_chunk,
    )


def _vec3_f32(blob: bytes, offset: int, count: int) -> list[tuple[float, float, float]]:
    return [
        struct.unpack_from("<fff", blob, offset + index * 12)
        for index in range(count)
    ]


def _u16(blob: bytes, offset: int, count: int) -> list[int]:
    return [
        struct.unpack_from("<H", blob, offset + index * 2)[0]
        for index in range(count)
    ]


def validate_render_geometry(gltf: dict, bin_chunk: bytes) -> dict:
    """Check the shared cube is front-face visible and non-degenerate."""

    primitive = gltf["meshes"][0]["primitives"][0]
    position_accessor = gltf["accessors"][primitive["attributes"]["POSITION"]]
    normal_accessor = gltf["accessors"][primitive["attributes"]["NORMAL"]]
    index_accessor = gltf["accessors"][primitive["indices"]]

    position_view = gltf["bufferViews"][position_accessor["bufferView"]]
    normal_view = gltf["bufferViews"][normal_accessor["bufferView"]]
    index_view = gltf["bufferViews"][index_accessor["bufferView"]]

    positions = _vec3_f32(
        bin_chunk,
        position_view.get("byteOffset", 0) + position_accessor.get("byteOffset", 0),
        position_accessor["count"],
    )
    normals = _vec3_f32(
        bin_chunk,
        normal_view.get("byteOffset", 0) + normal_accessor.get("byteOffset", 0),
        normal_accessor["count"],
    )
    indices = _u16(
        bin_chunk,
        index_view.get("byteOffset", 0) + index_accessor.get("byteOffset", 0),
        index_accessor["count"],
    )

    assert len(indices) % 3 == 0
    outward = 0
    normal_agreement = 0

    def sub(a, b):
        return tuple(a[i] - b[i] for i in range(3))

    def cross(a, b):
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )

    def dot(a, b):
        return sum(a[i] * b[i] for i in range(3))

    for tri in range(0, len(indices), 3):
        i0, i1, i2 = indices[tri : tri + 3]
        p0, p1, p2 = positions[i0], positions[i1], positions[i2]
        geometric = cross(sub(p1, p0), sub(p2, p0))
        centroid = tuple((p0[i] + p1[i] + p2[i]) / 3 for i in range(3))
        if dot(geometric, centroid) > 0:
            outward += 1
        if dot(geometric, normals[i0]) > 0:
            normal_agreement += 1

    triangles = len(indices) // 3
    assert triangles == 12
    assert outward == triangles, (
        f"cube winding is not outward: {outward}/{triangles}"
    )
    assert normal_agreement == triangles, (
        f"geometric/declaration normal mismatch: {normal_agreement}/{triangles}"
    )

    position_min = position_accessor["min"]
    position_max = position_accessor["max"]
    spans = [position_max[i] - position_min[i] for i in range(3)]
    assert all(value > 0 for value in spans), spans

    visible_materials = 0
    for material in gltf.get("materials", []):
        color = material.get("pbrMetallicRoughness", {}).get(
            "baseColorFactor",
            [1, 1, 1, 1],
        )
        if max(color[:3]) > 0.2 and color[3] > 0:
            visible_materials += 1
    assert visible_materials >= 6

    return {
        "triangles": triangles,
        "outward_triangles": outward,
        "normal_agreement_triangles": normal_agreement,
        "visible_materials": visible_materials,
    }


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

    gltf, bin_chunk = parse_glb(asset)
    assert gltf.get("asset", {}).get("version") == "2.0"
    render_geometry = validate_render_geometry(gltf, bin_chunk)
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

    poster = ROOT / "docs" / "assets" / "purrtocol" / "purrtocol-poster.svg"
    assert poster.exists(), "3D viewer requires an always-visible poster fallback"
    poster_text = poster.read_text(encoding="utf-8")
    assert "3D Purrtocol" in poster_text
    assert "Visualization ≠ Evidence" in poster_text

    browser_observation = json.loads(
        (
            ROOT / "docs" / "purrtocol-3d" / "BROWSER_OBSERVATION.json"
        ).read_text(encoding="utf-8")
    )
    assert browser_observation["schema"] == "purrtocol-3d-browser-observation/v1"
    assert (
        browser_observation["observations"]["live_render"]["conclusion"]
        == "success"
    )
    assert (
        browser_observation["observations"]["forced_runtime_failure"]["conclusion"]
        == "success"
    )
    assert (
        browser_observation["interpretation"]["live_browser_result"]
        == "INTERACTIVE_3D_OBSERVED"
    )
    assert (
        browser_observation["interpretation"]["fallback_result"]
        == "DARK_BOX_FAILURE_MODE_MITIGATED"
    )
    assert (
        browser_observation["interpretation"]["production_device_claim"]
        == "NOT_ESTABLISHED"
    )

    html = preview.read_text(encoding="utf-8")
    assert 'src="../assets/purrtocol/purrtocol.glb"' in html
    assert "ajax.googleapis.com/ajax/libs/model-viewer/4.3.1" in html
    assert "cdnjs.cloudflare.com/ajax/libs/model-viewer/4.3.1" in html
    assert 'poster="../assets/purrtocol/purrtocol-poster.svg"' in html
    assert 'slot="poster"' in html
    assert "poster fallback remains visible" in html
    assert "viewer.addEventListener('error'" in html
    assert "WebGL2 available" in html
    assert "display:block" in html
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
                "render_geometry": render_geometry,
                "poster_fallback": "docs/assets/purrtocol/purrtocol-poster.svg",
                "viewer_runtime_sources": 2,
                "browser_observation_run": browser_observation["workflow_run_id"],
                "interactive_3d_observed": True,
                "dark_box_fallback_observed": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
