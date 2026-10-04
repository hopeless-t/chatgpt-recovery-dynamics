#!/usr/bin/env python3
"""Evaluate the shadow public-analysis router on predeclared history cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from route_public_analysis_jobs import route

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "data" / "public_analysis_observer_routing_policy.json"
DEFAULT_CASES = ROOT / "data" / "public_analysis_observer_routing_cases.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--output")
    args = parser.parse_args()

    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))["cases"]

    observed = []
    expectation_errors = []
    total_actual_jobs = 0
    total_candidate_jobs = 0

    for case in cases:
        result = route(case["paths"], policy)
        expected_route = case["expected_route_id"]
        expected_count = case["expected_candidate_job_count"]
        if result["route_id"] != expected_route:
            expectation_errors.append(
                f"{case['case_id']}: route {result['route_id']} != {expected_route}"
            )
        if result["candidate_job_count"] != expected_count:
            expectation_errors.append(
                f"{case['case_id']}: candidate job count "
                f"{result['candidate_job_count']} != {expected_count}"
            )

        actual = case.get("observed_public_analysis_jobs_launched")
        if actual is not None:
            total_actual_jobs += actual
            total_candidate_jobs += result["candidate_job_count"]

        observed.append(
            {
                "case_id": case["case_id"],
                "source_pr": case["source_pr"],
                "route_id": result["route_id"],
                "candidate_jobs": result["candidate_jobs"],
                "candidate_job_count": result["candidate_job_count"],
                "full_job_count": result["full_job_count"],
                "candidate_avoided_jobs": result["candidate_avoided_jobs"],
                "candidate_avoided_job_count": result["candidate_avoided_job_count"],
                "fail_closed": result["fail_closed"],
                "jobs_actually_skipped": result["jobs_actually_skipped"],
            }
        )

    report = {
        "schema": "public-analysis-observer-routing-evaluation/v1",
        "classification": "shadow_counterfactual_not_execution_authority",
        "case_count": len(observed),
        "cases": observed,
        "expectation_errors": expectation_errors,
        "expectations_pass": not expectation_errors,
        "observed_run_subset": {
            "cases_with_actual_launch_count": sum(
                1 for case in cases if case.get("observed_public_analysis_jobs_launched") is not None
            ),
            "actual_jobs_launched": total_actual_jobs,
            "candidate_jobs_if_router_were_promoted": total_candidate_jobs,
            "candidate_jobs_avoided": total_actual_jobs - total_candidate_jobs,
        },
        "authority": {
            "execution_authority": False,
            "jobs_actually_skipped": False,
            "full_public_analysis_still_runs": True,
        },
        "next_evidence": (
            "Run the router in shadow mode on live PRs and compare its candidate route "
            "with the still-executed full public-analysis result before any skip proposal."
        ),
    }

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    if expectation_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
