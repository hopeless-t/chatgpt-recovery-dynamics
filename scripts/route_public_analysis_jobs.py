#!/usr/bin/env python3
"""Shadow-route Validate public analysis jobs without skipping anything.

This tool is diagnostic only. It classifies a changed-path set into either one
known safe island or the fail-closed FULL route. It never edits workflows,
never skips jobs, and never grants promotion authority.

A reduced-route candidate is allowed only when every changed path is also
covered by at least one source-proximate HTTP 429 pull-request workflow trigger.
This closes the gap between a broad router prefix such as ``scripts/http_429_*``
and narrower dedicated workflow path filters.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "data" / "public_analysis_observer_routing_policy.json"
HTTP_429_WORKFLOW_GLOB = "validate-http-429*.yml"


def matches(path: str, island: dict) -> bool:
    if path in island.get("exact_paths", []):
        return True
    return any(path.startswith(prefix) for prefix in island.get("prefixes", []))


def _extract_pull_request_paths(workflow: Path) -> list[str]:
    """Extract the small YAML subset used by workflow pull_request.paths.

    No third-party YAML parser is needed because the repository uses the simple
    block shape:

        on:
          pull_request:
            paths:
              - "..."

    If that structure is absent, the workflow contributes no explicit path
    coverage for this audit.
    """

    patterns: list[str] = []
    in_pull_request = False
    in_paths = False

    for raw in workflow.read_text(encoding="utf-8").splitlines():
        if raw.startswith("  pull_request:"):
            in_pull_request = True
            in_paths = False
            continue

        if in_pull_request and raw.startswith("  ") and not raw.startswith("    "):
            break

        if in_pull_request and raw.startswith("    paths:"):
            in_paths = True
            continue

        if in_paths:
            if raw.startswith("      - "):
                value = raw[len("      - ") :].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                    value = value[1:-1]
                patterns.append(value)
                continue
            if raw.strip() and not raw.startswith("      "):
                in_paths = False

    return patterns


def _github_glob_regex(pattern: str) -> re.Pattern[str]:
    """Translate the workflow path glob subset used in this repository."""

    out = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(char))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def source_gate_trigger_coverage(paths: list[str]) -> dict:
    workflow_dir = ROOT / ".github" / "workflows"
    workflows = sorted(workflow_dir.glob(HTTP_429_WORKFLOW_GLOB))
    triggers = {
        str(path.relative_to(ROOT)): _extract_pull_request_paths(path)
        for path in workflows
    }

    covered_by: dict[str, list[str]] = {}
    for changed in sorted(set(paths)):
        matches_for_path = []
        for workflow_name, patterns in triggers.items():
            if any(_github_glob_regex(pattern).match(changed) for pattern in patterns):
                matches_for_path.append(workflow_name)
        covered_by[changed] = matches_for_path

    uncovered = [path for path, names in covered_by.items() if not names]
    return {
        "schema": "public-analysis-source-gate-coverage/v1",
        "workflow_glob": f".github/workflows/{HTTP_429_WORKFLOW_GLOB}",
        "workflow_count": len(workflows),
        "workflow_triggers": triggers,
        "covered_by": covered_by,
        "uncovered_paths": uncovered,
        "all_paths_covered": bool(paths) and not uncovered,
    }


def route(paths: list[str], policy: dict) -> dict:
    clean = sorted(set(paths))
    full_jobs = list(policy["full_job_set"])
    matching_islands = [
        island
        for island in policy.get("safe_islands", [])
        if clean and all(matches(path, island) for path in clean)
    ]

    coverage = source_gate_trigger_coverage(clean)
    candidate_route_before_coverage = None
    coverage_fail_closed = False

    if len(matching_islands) == 1:
        island = matching_islands[0]
        candidate_route_before_coverage = island["route_id"]

        if policy.get("source_gate_trigger_coverage_required", False) and not coverage[
            "all_paths_covered"
        ]:
            candidate_jobs = full_jobs
            route_id = policy["fallback"]["route_id"]
            reason = (
                "Safe-island path match found, but one or more changed paths are not "
                "covered by an actual source-proximate HTTP 429 pull-request trigger."
            )
            external_gates = []
            fail_closed = True
            coverage_fail_closed = True
        else:
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
        "candidate_route_before_coverage": candidate_route_before_coverage,
        "candidate_jobs": candidate_jobs,
        "candidate_job_count": len(candidate_jobs),
        "full_job_count": len(full_jobs),
        "candidate_avoided_jobs": avoided,
        "candidate_avoided_job_count": len(avoided),
        "candidate_avoided_fraction": (
            len(avoided) / len(full_jobs) if full_jobs else 0.0
        ),
        "required_external_gates": external_gates,
        "source_gate_trigger_coverage": coverage,
        "coverage_fail_closed": coverage_fail_closed,
        "fail_closed": fail_closed,
        "reason": reason,
        "execution_authority": False,
        "jobs_actually_skipped": False,
        "interpretation": {
            "candidate_route_is_not_permission_to_skip": True,
            "unknown_or_mixed_surface_routes_full": True,
            "uncovered_source_gate_path_routes_full": True,
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
