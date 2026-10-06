#!/usr/bin/env python3
"""Evaluate Purrtocol renderer strategies without collapsing them to one score.

The arena uses hard safety/semantic gates followed by a Pareto frontier over
machine-observable engineering dimensions. Human response is deliberately not
an automated objective until separately observed. Transfer measurements may be
carried as diagnostics, but are not a Pareto objective in v0.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

INPUT_SCHEMA = "purrtocol-renderer-arena-input/v0"
OUTPUT_SCHEMA = "purrtocol-renderer-arena/v0"
TRANSFER_SCHEMA = "purrtocol-transfer-proxy/v0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_ENTRANTS = 64
MAX_ASSET_BYTES = 4 * 1024 * 1024


class ArenaError(ValueError):
    pass


def unit_float(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ArenaError(f"{field} must be numeric")
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ArenaError(f"{field} must be within [0,1]")
    return round(value, 6)


def positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ArenaError(f"{field} must be a positive integer")
    if value > MAX_ASSET_BYTES:
        raise ArenaError(f"{field} exceeds bounded arena asset limit")
    return value


def require_bool(row: dict[str, Any], key: str) -> bool:
    value = row.get(key)
    if not isinstance(value, bool):
        raise ArenaError(f"{key} must be boolean")
    return value


def validate_sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ArenaError(f"{field} must be a lowercase sha256 hex digest")
    return value


def normalize_transfer_proxy(value: Any, renderer_id: str, asset_sha256: str, asset_bytes: int) -> dict[str, Any]:
    if value is None:
        return {"status": "UNMEASURED", "included_in_pareto": False}
    if not isinstance(value, dict) or value.get("schema") != TRANSFER_SCHEMA:
        raise ArenaError(f"transfer_proxy must use {TRANSFER_SCHEMA}")
    if value.get("renderer_id") != renderer_id:
        raise ArenaError("transfer_proxy renderer_id mismatch")
    if value.get("asset_sha256") != asset_sha256:
        raise ArenaError("transfer_proxy asset_sha256 mismatch")
    raw_bytes = positive_int(value.get("raw_bytes"), "transfer_proxy.raw_bytes")
    if raw_bytes != asset_bytes:
        raise ArenaError("transfer_proxy raw_bytes mismatch")
    gzip_bytes = positive_int(value.get("gzip_bytes"), "transfer_proxy.gzip_bytes")
    ratio = value.get("compression_ratio")
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or ratio <= 0:
        raise ArenaError("transfer_proxy compression_ratio must be positive numeric")
    contract = value.get("contract")
    if not isinstance(contract, dict):
        raise ArenaError("transfer_proxy contract must be object")
    if contract.get("codec") != "gzip" or contract.get("compresslevel") != 9 or contract.get("mtime") != 0:
        raise ArenaError("transfer_proxy contract mismatch")
    if contract.get("deterministic_proxy") is not True:
        raise ArenaError("transfer_proxy must be deterministic")
    if contract.get("included_in_pareto") is not False:
        raise ArenaError("transfer_proxy cannot enter Pareto in arena v0")
    if contract.get("proxy_not_wire_truth") is not True:
        raise ArenaError("transfer_proxy must declare proxy_not_wire_truth")
    return {
        "status": "MEASURED_DIAGNOSTIC",
        "schema": TRANSFER_SCHEMA,
        "raw_bytes": raw_bytes,
        "gzip_bytes": gzip_bytes,
        "compression_ratio": round(float(ratio), 9),
        "gzip_sha256": validate_sha(value.get("gzip_sha256"), "transfer_proxy.gzip_sha256"),
        "included_in_pareto": False,
        "proxy_not_wire_truth": True,
    }


def normalize_entrant(row: dict[str, Any]) -> dict[str, Any]:
    renderer_id = row.get("renderer_id")
    if not isinstance(renderer_id, str) or not renderer_id.strip():
        raise ArenaError("renderer_id must be a non-empty string")
    renderer_id = renderer_id.strip()

    human_reaction = row.get("human_reaction")
    if human_reaction != "UNKNOWN":
        raise ArenaError("arena v0 only accepts human_reaction=UNKNOWN")

    runtime = row.get("runtime")
    if runtime is None:
        runtime_out = {"status": "UNMEASURED", "included_in_pareto": False}
    else:
        if not isinstance(runtime, dict):
            raise ArenaError("runtime must be an object when provided")
        samples = runtime.get("samples_ms", [])
        controlled = runtime.get("controlled_environment") is True
        if not isinstance(samples, list) or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 for v in samples
        ):
            raise ArenaError("runtime.samples_ms must contain non-negative numbers")
        ordered = sorted(float(v) for v in samples)
        median = None
        if ordered:
            n = len(ordered)
            median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0
        runtime_out = {
            "status": "MEASURED_CONTROLLED" if controlled and len(ordered) >= 3 else "MEASURED_UNSTABLE",
            "samples_ms": ordered,
            "median_ms": round(median, 6) if median is not None else None,
            "included_in_pareto": False,
            "reason": "runtime remains diagnostic in arena v0 because hosted-runner timing is environment-sensitive",
        }

    asset_sha256 = validate_sha(row.get("asset_sha256"), "asset_sha256")
    asset_bytes = positive_int(row.get("asset_bytes"), "asset_bytes")

    normalized = {
        "renderer_id": renderer_id,
        "specimen_id": str(row.get("specimen_id", renderer_id)).strip(),
        "asset_sha256": asset_sha256,
        "physical_sha256": validate_sha(row.get("physical_sha256"), "physical_sha256"),
        "asset_bytes": asset_bytes,
        "semantic_contract_coverage": unit_float(
            row.get("semantic_contract_coverage"), "semantic_contract_coverage"
        ),
        "lineage_expression_coverage": unit_float(
            row.get("lineage_expression_coverage"), "lineage_expression_coverage"
        ),
        "deterministic_replay": require_bool(row, "deterministic_replay"),
        "semantic_contract_pass": require_bool(row, "semantic_contract_pass"),
        "extinction_gate_pass": require_bool(row, "extinction_gate_pass"),
        "provenance_bound": require_bool(row, "provenance_bound"),
        "canonical": require_bool(row, "canonical"),
        "human_reaction": human_reaction,
        "evidence_status": row.get("evidence_status"),
        "runtime": runtime_out,
        "transfer_proxy": normalize_transfer_proxy(row.get("transfer_proxy"), renderer_id, asset_sha256, asset_bytes),
    }
    if normalized["evidence_status"] not in {
        "visualization_not_evidence",
        "engineering_observation",
    }:
        raise ArenaError("unsupported evidence_status")
    return normalized


def gate(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not row["deterministic_replay"]:
        reasons.append("nondeterministic-replay")
    if not row["semantic_contract_pass"]:
        reasons.append("semantic-contract-failed")
    if row["semantic_contract_coverage"] < 1.0:
        reasons.append("semantic-contract-incomplete")
    if not row["extinction_gate_pass"]:
        reasons.append("extinction-gate-failed")
    if not row["provenance_bound"]:
        reasons.append("provenance-unbound")
    if row["canonical"]:
        reasons.append("experimental-renderer-claimed-canon")
    return reasons


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Pareto dominance for v0: smaller bytes, more lineage expression.

    Semantic coverage is a hard gate at 1.0, so it is not useful as a
    post-gate ranking dimension. Runtime and transfer proxy are diagnostic-only.
    """
    no_worse = (
        a["asset_bytes"] <= b["asset_bytes"]
        and a["lineage_expression_coverage"] >= b["lineage_expression_coverage"]
    )
    strictly_better = (
        a["asset_bytes"] < b["asset_bytes"]
        or a["lineage_expression_coverage"] > b["lineage_expression_coverage"]
    )
    return no_worse and strictly_better


def build(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") != INPUT_SCHEMA:
        raise ArenaError(f"expected {INPUT_SCHEMA}")
    rows = doc.get("entrants")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ENTRANTS:
        raise ArenaError(f"entrants must contain 1..{MAX_ENTRANTS} entries")

    normalized = [normalize_entrant(row) for row in rows]
    ids = [row["renderer_id"] for row in normalized]
    if len(ids) != len(set(ids)):
        raise ArenaError("renderer_id values must be unique")
    normalized.sort(key=lambda row: row["renderer_id"])

    evaluated = []
    valid = []
    for row in normalized:
        reasons = gate(row)
        enriched = {
            **row,
            "gate": {"pass": not reasons, "reasons": reasons},
            "pareto": {"frontier": False, "dominated_by": []},
        }
        evaluated.append(enriched)
        if not reasons:
            valid.append(enriched)

    edges: list[dict[str, str]] = []
    for candidate in valid:
        dominators = []
        for other in valid:
            if other is candidate:
                continue
            if dominates(other, candidate):
                dominators.append(other["renderer_id"])
                edges.append({"dominates": other["renderer_id"], "dominated": candidate["renderer_id"]})
        candidate["pareto"]["dominated_by"] = sorted(dominators)
        candidate["pareto"]["frontier"] = not dominators

    frontier = sorted(row["renderer_id"] for row in valid if row["pareto"]["frontier"])
    disqualified = sorted(row["renderer_id"] for row in evaluated if not row["gate"]["pass"])

    return {
        "schema": OUTPUT_SCHEMA,
        "status": "pareto-no-single-winner",
        "evidence_status": "engineering_observation",
        "objective_policy": {
            "hard_gates_before_optimization": True,
            "single_scalar_score": False,
            "pareto_dimensions": {
                "asset_bytes": "minimize",
                "lineage_expression_coverage": "maximize",
            },
            "diagnostic_only": ["runtime", "transfer_proxy"],
            "excluded_until_observed": ["human_reaction", "humor", "comprehension", "replay_value"],
        },
        "world_laws": {
            "invalid_cannot_win_by_being_small": True,
            "human_unknown_is_not_zero": True,
            "metadata_difference_is_not_physical_difference": True,
            "no_automatic_canonical_promotion": True,
            "no_single_winner_required": True,
            "compressed_bytes_are_not_network_load": True,
        },
        "summary": {
            "entrants": len(evaluated),
            "gate_pass": len(valid),
            "disqualified": len(disqualified),
            "pareto_frontier": len(frontier),
        },
        "frontier": frontier,
        "disqualified": disqualified,
        "dominance_edges": sorted(edges, key=lambda edge: (edge["dominates"], edge["dominated"])),
        "entrants": evaluated,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = build(doc)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
