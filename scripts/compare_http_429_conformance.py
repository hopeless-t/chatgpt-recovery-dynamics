#!/usr/bin/env python3
"""Compare Python and an independent candidate HTTP 429 conformance report.

This comparison intentionally ignores implementation-specific transport error
names while requiring semantic parity for retry timing, authorization,
operation/attempt identity, request counts, and side-effect counts.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


FLOAT_TOL = 1e-9


def close(a: float | int | None, b: float | int | None) -> bool:
    if a is None or b is None:
        return a is b
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=FLOAT_TOL)


def compare_decision(a: dict[str, Any], b: dict[str, Any], where: str, errors: list[str]) -> None:
    exact = [
        "action",
        "operation_id",
        "attempt_id",
        "attempt_number",
        "budget_remaining_after_attempt",
        "standards_used",
    ]
    numeric = [
        "next_start_s",
        "retry_after_floor_s",
        "draft_ratelimit_floor_s",
        "local_backoff_s",
        "herd_jitter_s",
    ]
    for key in exact:
        if a.get(key) != b.get(key):
            errors.append(f"{where}.{key}: {a.get(key)!r} != {b.get(key)!r}")
    for key in numeric:
        if not close(a.get(key), b.get(key)):
            errors.append(f"{where}.{key}: {a.get(key)!r} != {b.get(key)!r}")


def by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["scenario_id"]: row for row in report["results"]}


def compare_scripted(a: dict[str, Any], b: dict[str, Any], errors: list[str]) -> None:
    sid = a["scenario_id"]
    for key in ["terminal", "operation_id", "server_requests"]:
        if a.get(key) != b.get(key):
            errors.append(f"{sid}.{key}: {a.get(key)!r} != {b.get(key)!r}")

    if len(a["start_times_s"]) != len(b["start_times_s"]):
        errors.append(f"{sid}.start_times length differs")
    else:
        for i, (x, y) in enumerate(zip(a["start_times_s"], b["start_times_s"])):
            if not close(x, y):
                errors.append(f"{sid}.start_times_s[{i}]: {x!r} != {y!r}")

    if len(a["attempts"]) != len(b["attempts"]):
        errors.append(f"{sid}.attempt count differs")
        return

    for i, (pa, pb) in enumerate(zip(a["attempts"], b["attempts"])):
        where = f"{sid}.attempts[{i}]"
        for key in [
            "attempt_number",
            "operation_id",
            "attempt_id",
            "status",
            "decision",
            "retry_after",
            "ratelimit",
        ]:
            if pa.get(key) != pb.get(key):
                errors.append(f"{where}.{key}: {pa.get(key)!r} != {pb.get(key)!r}")
        if "retry_decision" in pa or "retry_decision" in pb:
            compare_decision(
                pa.get("retry_decision", {}),
                pb.get("retry_decision", {}),
                f"{where}.retry_decision",
                errors,
            )


def compare_ambiguous(a: dict[str, Any], b: dict[str, Any], errors: list[str]) -> None:
    sid = a["scenario_id"]
    for key in ["post_requests", "side_effects"]:
        if a.get(key) != b.get(key):
            errors.append(f"{sid}.{key}: {a.get(key)!r} != {b.get(key)!r}")

    if sid == "unknown-post-reobserve":
        compare_decision(a["decision"], b["decision"], f"{sid}.decision", errors)
        if a["reobserved_state"] != b["reobserved_state"]:
            errors.append(f"{sid}.reobserved_state differs")
    elif sid == "explicit-contract-deduplicates":
        compare_decision(
            a["first_decision"],
            b["first_decision"],
            f"{sid}.first_decision",
            errors,
        )
        for key in [
            "terminal",
            "operation_id",
            "attempt_ids",
            "server_operation_ids",
            "server_attempt_ids",
            "response",
        ]:
            if a.get(key) != b.get(key):
                errors.append(f"{sid}.{key}: {a.get(key)!r} != {b.get(key)!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-report", required=True)
    parser.add_argument("--node-report", required=True, help="candidate report path; retained for backward-compatible CLI")
    parser.add_argument("--candidate-label", default="node-standard-library")
    parser.add_argument("--output")
    args = parser.parse_args()

    py = json.loads(Path(args.python_report).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.node_report).read_text(encoding="utf-8"))

    errors: list[str] = []
    py_by = by_id(py)
    candidate_by = by_id(candidate)

    if set(py_by) != set(candidate_by):
        errors.append(
            f"scenario ids differ: python={sorted(py_by)} candidate={sorted(candidate_by)}"
        )

    for sid in sorted(set(py_by) & set(candidate_by)):
        a = py_by[sid]
        b = candidate_by[sid]
        if sid in {
            "unknown-post-reobserve",
            "explicit-contract-deduplicates",
        }:
            compare_ambiguous(a, b, errors)
        else:
            compare_scripted(a, b, errors)

    report = {
        "schema": "http-429-cross-language-conformance/v1",
        "implementations": [
            "python-standard-library",
            args.candidate_label,
        ],
        "scenario_count": len(set(py_by) & set(candidate_by)),
        "semantic_parity": not errors,
        "float_tolerance_abs": FLOAT_TOL,
        "ignored_as_implementation_specific": [
            "transport_error_name",
            "classification_label",
        ],
        "errors": errors,
        "interpretation": {
            "pass_means": (
                "The Python reference and an independent candidate implementation "
                "reproduced the same repository contract semantics across the shared loopback scenarios."
            ),
            "pass_does_not_mean": (
                "universal provider behavior, production reliability, or RFC conformance certification"
            ),
        },
    }

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
