#!/usr/bin/env python3
"""Detect branch/base overlap before it becomes merge/reintegration rework.

This is a diagnostic, not a merge-conflict oracle.

It compares changes on the base and head since their merge base. If the base
advanced and both sides touched the same paths, the branch has a concrete
convergence risk worth resolving early.

The script never rewrites history and never force-updates refs.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        check=True,
        capture_output=True,
    )
    return proc.stdout.strip()


def changed_paths(a: str, b: str) -> set[str]:
    out = git("diff", "--name-only", f"{a}..{b}")
    return {line for line in out.splitlines() if line}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--output")
    args = parser.parse_args()

    merge_base = git("merge-base", args.base, args.head)
    base_ahead = int(git("rev-list", "--count", f"{merge_base}..{args.base}") or "0")
    head_ahead = int(git("rev-list", "--count", f"{merge_base}..{args.head}") or "0")

    base_paths = changed_paths(merge_base, args.base)
    head_paths = changed_paths(merge_base, args.head)
    overlap = sorted(base_paths & head_paths)

    if base_ahead == 0:
        status = "BASE_NOT_AHEAD"
    elif overlap:
        status = "CONVERGENCE_RISK"
    else:
        status = "BASE_AHEAD_NO_PATH_OVERLAP"

    result = {
        "schema": "branch-convergence-report/v1",
        "classification": "early_integration_risk_diagnostic_not_conflict_proof",
        "base": args.base,
        "head": args.head,
        "merge_base": merge_base,
        "base_ahead_commits": base_ahead,
        "head_ahead_commits": head_ahead,
        "base_changed_paths": sorted(base_paths),
        "head_changed_paths": sorted(head_paths),
        "overlapping_changed_paths": overlap,
        "overlap_count": len(overlap),
        "status": status,
        "recommendation": (
            "Reconcile with current base before extending the branch; prefer a "
            "fresh branch/rebuild when history is stale or conflict-prone. Do not "
            "force-update merely to make the diagnostic green."
            if status == "CONVERGENCE_RISK"
            else "No same-path convergence risk observed by this diagnostic."
        ),
        "limitations": [
            "Path overlap is not proof of a textual or semantic merge conflict.",
            "No path overlap is not proof that integration is semantically safe.",
            "The full promotion CI remains required.",
        ],
    }

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
