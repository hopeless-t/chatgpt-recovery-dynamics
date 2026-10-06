#!/usr/bin/env python3
"""Render one breeding-eligible Expression Genome onto Purrtocol Second Light.

This is a deterministic visualization compiler. It does not promote simulation
to evidence and it does not replace the canonical First Light asset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any

from generate_purrtocol_second_light import build as build_base


TYPE_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def quat_z(deg: float) -> list[float]:
    half = math.radians(deg) / 2.0
    return [0.0, 0.0, math.sin(half), math.cos(half)]


def quat_z_deg(q: list[float]) -> float:
    if abs(q[0]) > 1e-5 or abs(q[1]) > 1e-5:
        raise ValueError("expected z-axis quaternion")
    return math.degrees(2.0 * math.atan2(q[2], q[3]))


def parse_glb(data: bytes) -> tuple[dict[str, Any], bytearray]:
    magic, version, total = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or total != len(data):
        raise ValueError("invalid GLB v2 container")
    off = 12
    gltf = None
    binary = None
    while off + 8 <= len(data):
        length, kind = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off:off + length]
        off += length
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk.rstrip(b" \t\r\n\0").decode("utf-8"))
        elif kind == 0x004E4942:
            binary = bytearray(chunk)
    if gltf is None or binary is None:
        raise ValueError("Second Light must contain JSON and BIN chunks")
    return gltf, binary


def pack_glb(gltf: dict[str, Any], binary: bytearray) -> bytes:
    j = json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    j += b" " * ((-len(j)) % 4)
    b = bytes(binary)
    b += b"\0" * ((-len(b)) % 4)
    total = 12 + 8 + len(j) + 8 + len(b)
    out = struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<II", len(j), 0x4E4F534A) + j
    out += struct.pack("<II", len(b), 0x004E4942) + b
    return out


def accessor_values(gltf: dict[str, Any], binary: bytearray, accessor_id: int) -> list[list[float]]:
    accessor = gltf["accessors"][accessor_id]
    if accessor["componentType"] != 5126:
        raise ValueError("expression renderer only mutates float32 accessors")
    width = TYPE_WIDTH[accessor["type"]]
    view = gltf["bufferViews"][accessor["bufferView"]]
    if view.get("byteStride") not in (None, 4 * width):
        raise ValueError("strided accessors are not supported")
    off = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    vals = []
    for i in range(accessor["count"]):
        vals.append(list(struct.unpack_from("<" + "f" * width, binary, off + i * width * 4)))
    return vals


def write_accessor_values(
    gltf: dict[str, Any], binary: bytearray, accessor_id: int, values: list[list[float]]
) -> None:
    accessor = gltf["accessors"][accessor_id]
    width = TYPE_WIDTH[accessor["type"]]
    if len(values) != accessor["count"]:
        raise ValueError("accessor count mismatch")
    view = gltf["bufferViews"][accessor["bufferView"]]
    off = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    for i, value in enumerate(values):
        if len(value) != width:
            raise ValueError("accessor width mismatch")
        struct.pack_into("<" + "f" * width, binary, off + i * width * 4, *value)


def key_indices(interpolation: str, count: int) -> list[int]:
    if interpolation == "CUBICSPLINE":
        if count % 3:
            raise ValueError("invalid CUBICSPLINE accessor")
        return list(range(1, count, 3))
    return list(range(count))


def scale_translation_track(
    gltf: dict[str, Any], binary: bytearray, accessor_id: int, interpolation: str, factor: float
) -> None:
    values = accessor_values(gltf, binary, accessor_id)
    keys = key_indices(interpolation, len(values))
    if not keys:
        return
    origin = values[keys[0]][:]
    for idx in keys[1:]:
        values[idx] = [origin[k] + (values[idx][k] - origin[k]) * factor for k in range(3)]
    write_accessor_values(gltf, binary, accessor_id, values)


def scale_tail_track(
    gltf: dict[str, Any], binary: bytearray, accessor_id: int, interpolation: str, factor: float
) -> None:
    values = accessor_values(gltf, binary, accessor_id)
    keys = key_indices(interpolation, len(values))
    if not keys:
        return
    base = quat_z_deg(values[keys[0]])
    for idx in keys[1:]:
        angle = quat_z_deg(values[idx])
        values[idx] = quat_z(base + (angle - base) * factor)
    write_accessor_values(gltf, binary, accessor_id, values)


def scale_time_accessor(
    gltf: dict[str, Any], binary: bytearray, accessor_id: int, factor: float
) -> None:
    values = accessor_values(gltf, binary, accessor_id)
    values = [[row[0] * factor] for row in values]
    write_accessor_values(gltf, binary, accessor_id, values)
    accessor = gltf["accessors"][accessor_id]
    accessor["min"] = [min(row[0] for row in values)]
    accessor["max"] = [max(row[0] for row in values)]


def select_genome(doc: dict[str, Any], index: int, expression_id: str | None) -> dict[str, Any]:
    if doc.get("schema") != "purrtocol-expression-genome/v0":
        raise ValueError("expected purrtocol-expression-genome/v0")
    genomes = doc.get("genomes", [])
    if expression_id:
        matches = [g for g in genomes if g.get("expression_id") == expression_id]
        if len(matches) != 1:
            raise ValueError("expression_id must resolve to exactly one genome")
        genome = matches[0]
    else:
        if not 0 <= index < len(genomes):
            raise ValueError("genome index out of range")
        genome = genomes[index]
    if not genome.get("survives") or not genome.get("breeding_eligible"):
        raise ValueError("extinct or non-breeding genomes cannot render living descendants")
    if genome.get("implementation_target") != "purrtocol-second-light-generator/v0":
        raise ValueError("genome is not targeted at Second Light")
    if genome.get("canonical") is not False:
        raise ValueError("expression genome must remain non-canonical")
    if genome.get("human_reaction") != "UNKNOWN":
        raise ValueError("human reaction must remain UNKNOWN before observation")
    return genome


def apply_expression(gltf: dict[str, Any], binary: bytearray, genome: dict[str, Any]) -> None:
    exp = genome["expression"]
    silhouette = exp["silhouette"]
    motion = exp["motion"]
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
    gltf["materials"][1]["pbrMetallicRoughness"]["roughnessFactor"] = round(
        clamp(rough + 0.08, 0.20, 0.95), 4
    )

    time_factor = motion["timing_scale"]
    breath_factor = clamp(0.55 + 3.0 * motion["breath_amplitude"], 0.60, 1.25)
    step_factor = clamp(0.55 + motion["step_amplitude"], 0.75, 1.45)
    tail_factor = clamp(0.55 + 0.80 * motion["tail_secondary_motion"], 0.70, 1.35)

    idx_to_name = {i: node["name"] for i, node in enumerate(gltf["nodes"])}
    scaled_time: set[int] = set()

    for animation in gltf["animations"]:
        for sampler in animation["samplers"]:
            input_id = sampler["input"]
            if input_id not in scaled_time:
                scale_time_accessor(gltf, binary, input_id, time_factor)
                scaled_time.add(input_id)

        for channel in animation["channels"]:
            sampler = animation["samplers"][channel["sampler"]]
            target = channel["target"]
            node_name = idx_to_name[target["node"]]
            path = target["path"]
            if path == "translation":
                if node_name in {"body", "head"}:
                    factor = breath_factor
                elif animation["name"] == "provisional_step_E" and node_name in {"root", "paw_FR"}:
                    factor = step_factor
                else:
                    factor = 0.85 + 0.25 * motion["step_amplitude"]
                scale_translation_track(
                    gltf, binary, sampler["output"], sampler.get("interpolation", "LINEAR"), factor
                )
            elif path == "rotation" and node_name == "tail":
                scale_tail_track(
                    gltf, binary, sampler["output"], sampler.get("interpolation", "LINEAR"), tail_factor
                )

    extras = gltf["asset"].setdefault("extras", {})
    extras.update(
        {
            "variant_id": "PKV-SECOND-LIGHT-" + genome["expression_id"],
            "expression_id": genome["expression_id"],
            "source_organism_id": genome["source_organism_id"],
            "source_species_id": genome["source_species_id"],
            "source_niche_id": genome["source_niche_id"],
            "expression_signature": genome["expression_signature"],
            "classification": "visualization_not_evidence",
            "canonical": False,
            "human_reaction": "UNKNOWN",
            "expression_status": "simulation-derived-proposal",
            "technical_quality_not_equal_humor": True,
        }
    )


def render(doc: dict[str, Any], index: int, expression_id: str | None) -> tuple[bytes, dict[str, Any]]:
    genome = select_genome(doc, index, expression_id)
    base, base_metrics = build_base()
    gltf, binary = parse_glb(base)
    apply_expression(gltf, binary, genome)
    out = pack_glb(gltf, binary)
    metrics = {
        **base_metrics,
        "expression_id": genome["expression_id"],
        "source_organism_id": genome["source_organism_id"],
        "source_species_id": genome["source_species_id"],
        "source_niche_id": genome["source_niche_id"],
        "expression_signature": genome["expression_signature"],
        "presentation_regime": genome["expression"]["presentation"]["regime"],
    }
    return out, metrics


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--genomes", required=True)
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--expression-id")
    ap.add_argument("--output", required=True)
    ap.add_argument("--receipt")
    ns = ap.parse_args()

    doc = json.loads(Path(ns.genomes).read_text(encoding="utf-8"))
    data, metrics = render(doc, ns.index, ns.expression_id)
    path = Path(ns.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

    if ns.receipt:
        receipt = {
            "schema": "purrtocol-expressed-second-light-receipt/v0",
            "status": "experimental_implemented_visualization",
            "canonical": False,
            "promotion": "none",
            "evidence_status": "visualization_not_evidence",
            "human_reaction": "UNKNOWN",
            "asset": path.name,
            "asset_bytes": len(data),
            "asset_sha256": hashlib.sha256(data).hexdigest(),
            **metrics,
            "invariants": [
                "Simulation != Evidence",
                "Visualization != Evidence",
                "Generated variant != Canon",
                "UNKNOWN != SUCCESS",
                "Technical quality != humor",
                "Extinct != breeding eligible",
            ],
        }
        rp = Path(ns.receipt)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"bytes": len(data), **metrics}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
