#!/usr/bin/env python3
"""Generate a deterministic metamorphic HTTP 429 conformance swarm.

The output is local-lab input only. It contains no remote URL and creates no
production traffic. Cases are derived from contract invariants rather than from
provider-specific behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def client(
    *,
    minimum_period_s: float,
    local_base_s: float = 0.15,
    local_cap_s: float = 4.0,
    herd_jitter_fraction: float = 0.1,
    retry_budget: int = 5,
) -> dict:
    return {
        "minimum_period_s": minimum_period_s,
        "local_base_s": local_base_s,
        "local_cap_s": local_cap_s,
        "herd_jitter_fraction": herd_jitter_fraction,
        "retry_budget": retry_budget,
    }


def response(status: int, service_s: float, *, headers=None, body=None) -> dict:
    return {
        "status": status,
        "service_s": service_s,
        "headers": headers or {},
        "body": body or {},
    }


def build() -> dict:
    scripted: list[dict] = []

    # 6 Retry-After floor cases.
    for retry_after in (1, 3, 7):
        for minimum_period in (0.25, 1.0):
            sid = f"meta-floor-ra{retry_after}-mp{str(minimum_period).replace('.', 'p')}"
            scripted.append(
                {
                    "scenario_id": sid,
                    "description": "Metamorphic Retry-After floor case.",
                    "operation_id": f"swarm-{sid}",
                    "method": "GET",
                    "client": client(
                        minimum_period_s=minimum_period,
                        herd_jitter_fraction=0.2,
                    ),
                    "responses": [
                        response(
                            429,
                            0.03,
                            headers={"Retry-After": str(retry_after)},
                            body={"error": "metamorphic-floor"},
                        ),
                        response(200, 0.07, body={"ok": True}),
                    ],
                    "expect": {
                        "terminal": "SUCCESS",
                        "requests": 2,
                        "min_second_start_s": retry_after + 0.03,
                    },
                }
            )

    # 6 fast-fail anchor cases. Local backoff may dominate later attempts, but
    # it must never make start-to-start spacing smaller than minimum_period.
    for minimum_period in (0.5, 1.5, 3.0):
        for local_base in (0.1, 0.4):
            sid = (
                f"meta-anchor-mp{str(minimum_period).replace('.', 'p')}"
                f"-base{str(local_base).replace('.', 'p')}"
            )
            scripted.append(
                {
                    "scenario_id": sid,
                    "description": "Metamorphic fast-failure start-anchor case.",
                    "operation_id": f"swarm-{sid}",
                    "method": "GET",
                    "client": client(
                        minimum_period_s=minimum_period,
                        local_base_s=local_base,
                        herd_jitter_fraction=0.15,
                        retry_budget=6,
                    ),
                    "responses": [
                        response(429, 0.005, body={"error": "fast-1"}),
                        response(429, 0.005, body={"error": "fast-2"}),
                        response(429, 0.005, body={"error": "fast-3"}),
                        response(200, 0.05, body={"ok": True}),
                    ],
                    "expect": {
                        "terminal": "SUCCESS",
                        "requests": 4,
                        "min_start_gap_s": minimum_period,
                    },
                }
            )

    # 6 experimental draft zero-window cases with no Retry-After.
    for draft_t in (1, 3, 6):
        for minimum_period in (0.25, 1.0):
            sid = f"meta-draft-t{draft_t}-mp{str(minimum_period).replace('.', 'p')}"
            scripted.append(
                {
                    "scenario_id": sid,
                    "description": "Metamorphic draft RateLimit zero-window case.",
                    "operation_id": f"swarm-{sid}",
                    "method": "GET",
                    "client": client(
                        minimum_period_s=minimum_period,
                        local_base_s=0.1,
                        herd_jitter_fraction=0.1,
                    ),
                    "responses": [
                        response(
                            429,
                            0.02,
                            headers={"RateLimit": f'"default";r=0;t={draft_t}'},
                            body={"error": "draft-window"},
                        ),
                        response(200, 0.05, body={"ok": True}),
                    ],
                    "expect": {
                        "terminal": "SUCCESS",
                        "requests": 2,
                        "min_second_start_s": draft_t + 0.02,
                        "draft_floor_s": draft_t,
                    },
                }
            )

    # 6 precedence cases: Retry-After exists, therefore the draft hint is not
    # admitted as a timing authority.
    for retry_after, draft_t in ((2, 1), (5, 2), (7, 3)):
        for jitter in (0.0, 0.2):
            sid = (
                f"meta-precedence-ra{retry_after}-t{draft_t}"
                f"-j{str(jitter).replace('.', 'p')}"
            )
            scripted.append(
                {
                    "scenario_id": sid,
                    "description": "Metamorphic Retry-After-over-draft precedence case.",
                    "operation_id": f"swarm-{sid}",
                    "method": "GET",
                    "client": client(
                        minimum_period_s=0.5,
                        local_base_s=0.1,
                        herd_jitter_fraction=jitter,
                    ),
                    "responses": [
                        response(
                            429,
                            0.02,
                            headers={
                                "Retry-After": str(retry_after),
                                "RateLimit": f'"default";r=0;t={draft_t}',
                            },
                            body={"error": "precedence"},
                        ),
                        response(200, 0.05, body={"ok": True}),
                    ],
                    "expect": {
                        "terminal": "SUCCESS",
                        "requests": 2,
                        "min_second_start_s": retry_after + 0.02,
                        "draft_floor_s": 0,
                    },
                }
            )

    # 6 budget cases: an endless 429 tail must stop exactly at the configured
    # request budget, independent of Retry-After duration.
    for retry_budget in (2, 3, 5):
        for retry_after in (1, 2):
            sid = f"meta-budget-b{retry_budget}-ra{retry_after}"
            repeated = [
                response(
                    429,
                    0.01,
                    headers={"Retry-After": str(retry_after)},
                    body={"error": f"budget-{i}"},
                )
                for i in range(retry_budget + 2)
            ]
            scripted.append(
                {
                    "scenario_id": sid,
                    "description": "Metamorphic bounded retry-budget case.",
                    "operation_id": f"swarm-{sid}",
                    "method": "GET",
                    "client": client(
                        minimum_period_s=0.25,
                        local_base_s=0.1,
                        herd_jitter_fraction=0.0,
                        retry_budget=retry_budget,
                    ),
                    "responses": repeated,
                    "expect": {
                        "terminal": "STOP_BUDGET",
                        "requests": retry_budget,
                    },
                }
            )

    assert len(scripted) == 30
    assert len({row["scenario_id"] for row in scripted}) == 30

    return {
        "schema": "http-429-metamorphic-scenarios/v1",
        "base_datetime": "2026-10-04T10:30:00Z",
        "generator": {
            "id": "metamorphic-kitten-swarm-v1",
            "deterministic": True,
            "case_count": 30,
            "families": {
                "retry_after_floor": 6,
                "fast_fail_anchor": 6,
                "draft_zero_window": 6,
                "retry_after_precedence": 6,
                "budget_stop": 6,
            },
        },
        "safety": {
            "network_scope": "loopback_only",
            "allowed_host": "127.0.0.1",
            "production_traffic": False,
        },
        "scripted": scripted,
        "ambiguous": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = build()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(
        "Metamorphic Kitten Swarm:",
        result["generator"]["case_count"],
        "deterministic loopback-only cases",
    )


if __name__ == "__main__":
    main()
