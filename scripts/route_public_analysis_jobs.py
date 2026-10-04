#!/usr/bin/env python3
"""Shadow-route Validate public analysis jobs without skipping anything.

This tool is diagnostic only. It classifies a changed-path set into either one
known safe island or the fail-closed FULL route. It never edits workflows,
never skips jobs, and never grants promotion authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "data" / "public_analysis_observer_routing_policy.json"


def matches(path: str, island: dict) -> bool:
    if path in island.get("exact_paths", []):
        return True
    return any(path.startswith(prefix) for prefix in island.get("prefixes", []))


def route(paths: list[str], policy: dict) -> dict:
    clean = sorted(set(paths))
    full_jobs = list(policy["full_job_set"])
    matching_islands = [
        island
        for island in policy.get("safe_islands", [])
        if clean and all(matches(path, island) for path in clean)
    ]

    if len(matching_islands) == 1:
        island = matching_islands[0]
        jobs = list(island.get("candidate_jobs_always", []))
        if any(path.endswith(".py") for path in clean):
            jobs.extend(island.get("candidate_jobs_if_python_changed", []))
        candidate_jobs = [job for job in full_jobs if job in set(jobs)]
        route_id = island["route_id"]
        reason = island["description"]
        external_gates = island.get("required_external_gates", [])
        fail_closed = False
    else:
        candidate_jobs = full_jobs
        route_id = policy["fallback"]["route_id"]
        reason = policy["fallback"]["reason"]
        external_gates = []
        fail_closed = True

    avoided = [job for job in full_jobs if job not in set(candidate_jobs)]
    result = {
        "schema": "public-analysis-observer-route/v1",
        "classification": policy["classification"],
        "changed_paths": clean,
        "route_id": route_id,
        "candidate_jobs": candidate_jobs,
        "candidate_job_count": len(candidate_jobs),
        "full_job_count": len(full_jobs),
        "candidate_avoided_jobs": avoided,
        "candidate_avoided_job_count": len(avoided),
        "candidate_avoided_fraction": (
            len(avoided) / len(full_jobs) if full_jobs else 0.0
        ),
        "required_external_gates": external_gates,
        "fail_closed": fail_closed,
        "reason": reason,
        "execution_authority": False,
        "jobs_actually_skipped": False,
        "interpretation": {
            "candidate_route_is_not_permission_to_skip": True,
            "unknown_or_mixed_surface_routes_full": True,
            "full_public_analysis_remains_authoritative_during_shadow_phase": True,
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--paths-file")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--output")
    args = parser.parse_args()

    paths = list(args.path)
    if args.paths_file:
        data = json.loads(Path(args.paths_file).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            paths.extend(data.get("paths", []))
        else:
            paths.extend(data)

    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    result = route(paths, policy)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
