#!/usr/bin/env python3
"""Repository-local observatory for the closed improvement loop.

Standard-library only. This script observes repository state; it does not mutate it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HEX40 = re.compile(r"^[0-9a-f]{40}$")
STALE_PHRASES = (
    "PKE-106 is PREPRODUCTION",
    "no runtime 3D model has been promoted",
    "6 promoted / 1 waiting",
    "unimplemented concept: future 3D model",
    "3D modelだけはまだ未来",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def parse_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("GLB too small")
    magic, version, total_length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise ValueError(f"bad GLB magic: {magic!r}")
    if version != 2:
        raise ValueError(f"unsupported GLB version: {version}")
    if total_length != len(data):
        raise ValueError(
            f"GLB length header {total_length} != actual {len(data)}"
        )

    offset = 12
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            text = chunk.rstrip(b" \t\r\n\x00").decode("utf-8")
            return json.loads(text), data
    raise ValueError("GLB JSON chunk missing")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out")
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    checks: list[dict[str, str]] = []
    failures: list[str] = []
    warnings: list[str] = []

    def check(check_id: str, ok: bool, detail: str, *, critical: bool = True) -> None:
        status = "PASS" if ok else ("FAIL" if critical else "WARN")
        checks.append({"id": check_id, "status": status, "detail": detail})
        if not ok:
            (failures if critical else warnings).append(f"{check_id}: {detail}")

    concepts = read_jsonl(ROOT / "data" / "pakenya_concepts.jsonl")
    promotions = read_jsonl(ROOT / "data" / "pakenya_promotions.jsonl")
    events = read_jsonl(ROOT / "data" / "pakenya_events.jsonl")
    variants = read_jsonl(ROOT / "data" / "purrtocol_variants.jsonl")
    improvement = read_jsonl(ROOT / "data" / "improvement_events.jsonl")
    state = read_json(ROOT / "docs" / "repository-observatory" / "state.json")
    improvement_schema = read_json(ROOT / "data" / "improvement_event_schema.json")
    published_improvement_schema = read_json(
        ROOT / "docs" / "repository-observatory" / "improvement-event.schema.json"
    )
    check(
        "observatory.schema_mirror",
        improvement_schema == published_improvement_schema,
        "data schema and Pages schema must be byte-semantically identical",
    )

    concept_ids = {row["event_id"] for row in concepts}
    promotion_by_concept = {row["concept_id"]: row for row in promotions}
    event_by_id = {row["event_id"]: row for row in events}

    check(
        "purrtocol.original_concepts_all_promoted",
        concept_ids == set(promotion_by_concept),
        f"{len(promotion_by_concept)}/{len(concept_ids)} concept origins have explicit promotions",
    )

    p106 = next(row for row in concepts if row["event_id"] == "PKE-106")
    p106p = promotion_by_concept.get("PKE-106")
    check(
        "purrtocol.pke106_origin_immutable",
        p106["status"] == "concept"
        and p106["timestamp_utc"] is None
        and p106["source_commit"] is None,
        "PKE-106 remains a null-timestamp/null-commit historical concept origin",
    )
    check(
        "purrtocol.pke106_promoted_to_pke033",
        bool(p106p)
        and p106p["implemented_event_id"] == "PKE-033"
        and p106p["implementation_commit"]
        == event_by_id["PKE-033"]["source_commit"],
        "PKE-106 promotion and PKE-033 event share one implementation identity",
    )

    contract = read_json(ROOT / "data" / "purrtocol_3d_contract.json")
    glb_path = ROOT / contract["runtime_asset"]
    try:
        gltf, glb_bytes = parse_glb(glb_path)
        actual_sha = hashlib.sha256(glb_bytes).hexdigest()
        first_light = contract["first_light"]
        check(
            "3d.binary_hash",
            actual_sha == first_light["sha256"],
            f"actual={actual_sha} expected={first_light['sha256']}",
        )
        check(
            "3d.binary_size",
            len(glb_bytes) == first_light["asset_bytes"],
            f"{len(glb_bytes)} bytes",
        )
        node_names = {
            node.get("name")
            for node in gltf.get("nodes", [])
            if isinstance(node, dict)
        }
        animation_names = {
            anim.get("name")
            for anim in gltf.get("animations", [])
            if isinstance(anim, dict)
        }
        missing_nodes = sorted(set(contract["required_nodes"]) - node_names)
        missing_animations = sorted(
            set(contract["required_animations"]) - animation_names
        )
        check(
            "3d.required_nodes",
            not missing_nodes,
            "missing=" + repr(missing_nodes),
        )
        check(
            "3d.required_animations",
            not missing_animations,
            "missing=" + repr(missing_animations),
        )
        asset_extras = gltf.get("asset", {}).get("extras", {})
        check(
            "3d.asset_epistemic_metadata",
            asset_extras.get("variant_id") == "PKV-CANONICAL"
            and asset_extras.get("classification") == "visualization_not_evidence",
            repr(asset_extras),
        )
    except Exception as exc:
        actual_sha = None
        gltf = {}
        glb_bytes = b""
        check("3d.parse", False, repr(exc))

    discovery = read_json(ROOT / "docs" / "purrtocol.json")
    frontier = discovery.get("current_frontier", {})
    check(
        "discovery.3d_implemented",
        frontier.get("implemented") is True
        and frontier.get("implemented_event_id") == "PKE-033",
        repr(frontier),
    )

    canonical = next(row for row in variants if row["variant_id"] == "PKV-CANONICAL")
    check(
        "variants.canonical_contains_glb",
        "docs/assets/purrtocol/purrtocol.glb" in canonical.get("assets", []),
        repr(canonical.get("assets", [])),
    )

    machine_surfaces = [
        "docs/llms.txt",
        "docs/index.md",
        "docs/purrtocol.json",
        "docs/purrtocol-variant.schema.json",
        "docs/purrtocol-variant-foundry/llms.txt",
        "docs/purrtocol-3d/llms.txt",
        "docs/repository-observatory/state.json",
        "IMPROVEMENT_LOOP.md",
    ]
    missing_surfaces = [p for p in machine_surfaces if not (ROOT / p).exists()]
    check(
        "discovery.machine_surfaces",
        not missing_surfaces,
        "missing=" + repr(missing_surfaces),
    )

    public_roots = [ROOT / "docs", ROOT / "README.md", ROOT / "BRANDING.md"]
    stale_hits: list[str] = []
    for root in public_roots:
        paths = [root] if root.is_file() else list(root.rglob("*"))
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in {
                ".md", ".html", ".json", ".txt", ".xml"
            }:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for phrase in STALE_PHRASES:
                if phrase in text:
                    stale_hits.append(f"{path.relative_to(ROOT)}: {phrase}")
    check(
        "content.no_stale_3d_frontier_phrases",
        not stale_hits,
        "hits=" + repr(stale_hits),
    )

    cycle_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in improvement:
        cycle_rows[row["cycle_id"]].append(row)
        check(
            f"ledger.{row['cycle_id']}.{row['seq']}.source_commit",
            bool(HEX40.fullmatch(row["source_commit"])),
            row["source_commit"],
        )
        try:
            datetime.fromisoformat(row["wall_time_utc"].replace("Z", "+00:00"))
        except ValueError:
            check(
                f"ledger.{row['cycle_id']}.{row['seq']}.timestamp",
                False,
                row["wall_time_utc"],
            )

    for cycle_id, rows in sorted(cycle_rows.items()):
        ordered = sorted(rows, key=lambda row: row["seq"])
        seqs = [row["seq"] for row in ordered]
        check(
            f"ledger.{cycle_id}.sequence",
            seqs == list(range(len(ordered))),
            repr(seqs),
        )
        check(
            f"ledger.{cycle_id}.lifecycle",
            ordered[0]["record_type"] == "cycle_start"
            and ordered[-1]["record_type"] == "cycle_end",
            f"{ordered[0]['record_type']} -> {ordered[-1]['record_type']}",
        )

    check(
        "observatory.north_star_present",
        bool(state.get("north_star")),
        state.get("north_star", ""),
    )
    check(
        "observatory.frontiers_present",
        len(state.get("frontiers", [])) >= 4,
        f"{len(state.get('frontiers', []))} declared frontiers",
    )

    docs_dir = ROOT / "docs"
    metrics = {
        "purrtocol": {
            "implemented_events": len(events),
            "concept_origins": len(concepts),
            "promotions": len(promotions),
            "registered_variants": len(variants),
        },
        "repository": {
            "html_index_pages": len(list(docs_dir.rglob("index.html"))),
            "markdown_files": len(list(ROOT.rglob("*.md"))),
            "python_scripts": len(list((ROOT / "scripts").glob("*.py"))),
            "github_workflows": len(list((ROOT / ".github" / "workflows").glob("*.yml"))),
            "improvement_cycles": len(cycle_rows),
        },
        "3d": {
            "asset_bytes": len(glb_bytes),
            "sha256": actual_sha,
            "nodes": len(gltf.get("nodes", [])) if gltf else None,
            "animations": len(gltf.get("animations", [])) if gltf else None,
        },
        "frontiers": {
            "open": sum(1 for item in state.get("frontiers", []) if item.get("status") == "open")
        },
    }

    result = {
        "schema": "repository-observatory-audit/v1",
        "status": "FAIL" if failures else ("WARN" if warnings else "PASS"),
        "north_star": state.get("north_star"),
        "checks": checks,
        "failures": failures,
        "warnings": warnings,
        "metrics": metrics,
        "open_frontiers": state.get("frontiers", []),
        "observer_effect_note": (
            "This audit is itself repository machinery. Its files/workflows are not "
            "free measurement; maintenance and CI load remain part of the system."
        ),
    }

    json_text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(json_text)
    if args.json_out:
        Path(args.json_out).write_text(json_text + "\n", encoding="utf-8")

    md = [
        "# Repository Observatory Audit",
        "",
        f"**Status:** {result['status']}",
        "",
        f"> {result['north_star']}",
        "",
        "## Metrics",
        "",
        f"- implemented Purrtocol events: {metrics['purrtocol']['implemented_events']}",
        f"- concept promotions: {metrics['purrtocol']['promotions']}/{metrics['purrtocol']['concept_origins']}",
        f"- registered variants: {metrics['purrtocol']['registered_variants']}",
        f"- HTML index pages: {metrics['repository']['html_index_pages']}",
        f"- improvement cycles: {metrics['repository']['improvement_cycles']}",
        f"- 3D GLB: {metrics['3d']['asset_bytes']} bytes / {metrics['3d']['nodes']} nodes / {metrics['3d']['animations']} animations",
        "",
        "## Checks",
        "",
    ]
    md += [f"- **{row['status']}** `{row['id']}` — {row['detail']}" for row in checks]
    md += ["", "## Open frontiers", ""]
    md += [
        f"- **{item['id']}** ({item['lane']}) — {item['target']}"
        for item in state.get("frontiers", [])
    ]
    md += [
        "",
        "## Observer-effect note",
        "",
        result["observer_effect_note"],
        "",
    ]
    md_text = "\n".join(md)
    if args.markdown_out:
        Path(args.markdown_out).write_text(md_text, encoding="utf-8")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
