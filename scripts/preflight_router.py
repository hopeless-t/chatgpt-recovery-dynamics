#!/usr/bin/env python3
"""Route changed paths to cheap source-proximate preflight diagnostics."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "data" / "preflight_routes.json"


def changed_from(base: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def route(paths: list[str], spec: dict[str, Any]) -> dict[str, Any]:
    matched = []
    matched_paths: set[str] = set()

    for rule in sorted(spec["rules"], key=lambda row: row["priority"]):
        hits = sorted(path for path in paths if matches(path, rule["patterns"]))
        if not hits:
            continue
        matched_paths.update(hits)
        matched.append(
            {
                "route_id": rule["route_id"],
                "priority": rule["priority"],
                "matched_paths": hits,
                "commands": rule["commands"],
                "promotion_gate": rule["promotion_gate"],
                "rationale": rule["rationale"],
            }
        )

    commands = []
    seen = set()
    for row in matched:
        for command in row["commands"]:
            if command not in seen:
                seen.add(command)
                commands.append(command)

    for row in spec["always"]:
        command = row["command"]
        if command not in seen:
            seen.add(command)
            commands.append(command)

    return {
        "schema": "preflight-route-result/v1",
        "paths": paths,
        "matched_routes": matched,
        "unmatched_paths": sorted(set(paths) - matched_paths),
        "commands": commands,
        "always": spec["always"],
        "promotion_gates": sorted(
            {
                row["promotion_gate"]
                for row in matched
            }
            | {
                row["promotion_gate"]
                for row in spec["always"]
            }
        ),
        "interpretation": {
            "preflight_pass_means": "cheap diagnostic passed",
            "preflight_pass_does_not_mean": "promotion gate passed",
            "unmatched_policy": spec["unmatched_policy"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--diff-base")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    paths = list(args.path)
    if args.diff_base:
        paths.extend(changed_from(args.diff_base))
    paths = sorted(set(paths))

    if not paths:
        parser.error("provide --path and/or --diff-base")

    spec = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    result = route(paths, spec)

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")

    if args.run:
        for command in result["commands"]:
            print(f"\n>>> {command}", flush=True)
            subprocess.run(
                command,
                cwd=ROOT,
                shell=True,
                check=True,
            )


if __name__ == "__main__":
    main()
