#!/usr/bin/env python3
"""Route Purrtocol rendering requests to feasible Pareto renderer habitats.

The router consumes a Renderer Arena ledger and explicit resource/expression
constraints. It returns every feasible frontier strategy instead of inventing a
single winner. If no strategy satisfies the request, it fails closed with
NO_FEASIBLE_RENDERER rather than silently degrading requirements.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ARENA_SCHEMA = "purrtocol-renderer-arena/v0"
REQUEST_SCHEMA = "purrtocol-renderer-habitat-request/v0"
OUTPUT_SCHEMA = "purrtocol-renderer-habitat-route/v0"


class RouteError(ValueError):
    pass


def optional_positive_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RouteError(f"{field} must be a positive integer or null")
    return value


def unit_float(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RouteError(f"{field} must be numeric")
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise RouteError(f"{field} must be within [0,1]")
    return round(value, 6)


def normalize_request(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") != REQUEST_SCHEMA:
        raise RouteError(f"expected {REQUEST_SCHEMA}")
    max_bytes = optional_positive_int(doc.get("max_asset_bytes"), "max_asset_bytes")
    min_coverage = unit_float(doc.get("min_lineage_expression_coverage", 0.0), "min_lineage_expression_coverage")
    require_frontier = doc.get("require_pareto_frontier", True)
    if not isinstance(require_frontier, bool):
        raise RouteError("require_pareto_frontier must be boolean")
    return {
        "schema": REQUEST_SCHEMA,
        "request_id": str(doc.get("request_id", "anonymous-request")),
        "max_asset_bytes": max_bytes,
        "min_lineage_expression_coverage": min_coverage,
        "require_pareto_frontier": require_frontier,
        "human_reaction_policy": "UNKNOWN-is-not-a-routing-score",
    }


def evaluate(row: dict[str, Any], request: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not row.get("gate", {}).get("pass"):
        reasons.append("arena-gate-failed")
    if request["require_pareto_frontier"] and not row.get("pareto", {}).get("frontier"):
        reasons.append("not-on-pareto-frontier")
    max_bytes = request["max_asset_bytes"]
    if max_bytes is not None and row["asset_bytes"] > max_bytes:
        reasons.append("asset-budget-exceeded")
    if row["lineage_expression_coverage"] < request["min_lineage_expression_coverage"]:
        reasons.append("expression-coverage-insufficient")
    if row.get("human_reaction") != "UNKNOWN":
        reasons.append("unexpected-human-reaction-state")
    return not reasons, reasons


def build(arena: dict[str, Any], request_doc: dict[str, Any]) -> dict[str, Any]:
    if arena.get("schema") != ARENA_SCHEMA:
        raise RouteError(f"expected {ARENA_SCHEMA}")
    if arena.get("status") != "pareto-no-single-winner":
        raise RouteError("arena status is not routable")
    request = normalize_request(request_doc)

    candidates = []
    rejected = []
    for row in arena.get("entrants", []):
        feasible, reasons = evaluate(row, request)
        compact = {
            "renderer_id": row["renderer_id"],
            "asset_bytes": row["asset_bytes"],
            "lineage_expression_coverage": row["lineage_expression_coverage"],
            "physical_sha256": row["physical_sha256"],
        }
        if feasible:
            candidates.append(compact)
        else:
            rejected.append({**compact, "reasons": reasons})

    candidates.sort(
        key=lambda row: (
            row["asset_bytes"],
            -row["lineage_expression_coverage"],
            row["renderer_id"],
        )
    )
    rejected.sort(key=lambda row: row["renderer_id"])

    if candidates:
        status = "FEASIBLE_SET"
    else:
        status = "NO_FEASIBLE_RENDERER"

    return {
        "schema": OUTPUT_SCHEMA,
        "status": status,
        "selection_policy": "return-feasible-set-no-hidden-degradation",
        "evidence_status": "engineering_observation",
        "request": request,
        "world_laws": {
            "no_silent_requirement_relaxation": True,
            "no_single_winner_invented": True,
            "unknown_human_response_not_used": True,
            "arena_gates_remain_binding": True,
            "no_feasible_renderer_is_valid_output": True,
        },
        "summary": {
            "feasible": len(candidates),
            "rejected": len(rejected),
        },
        "feasible_renderers": candidates,
        "rejected_renderers": rejected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arena", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    arena = json.loads(Path(args.arena).read_text(encoding="utf-8"))
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    result = build(arena, request)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], **result["summary"]}, sort_keys=True))


if __name__ == "__main__":
    main()
