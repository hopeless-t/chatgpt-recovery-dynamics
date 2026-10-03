#!/usr/bin/env python3
"""Validate the vendor-neutral HTTP 429 survival kit."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from http_429_survival import (
    decide,
    parse_draft_ratelimit_zero_window,
    parse_retry_after,
    scenario_decision,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    contract = json.loads(
        (ROOT / "data" / "http_429_survival_contract.json").read_text(
            encoding="utf-8"
        )
    )
    scenarios_doc = json.loads(
        (ROOT / "data" / "http_429_survival_scenarios.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["schema"] == "http-429-survival-contract/v1"
    assert contract["snapshot_date"] == "2026-10-03"

    standards = {row["id"]: row for row in contract["standards"]}
    assert standards["RFC6585-429"]["status"] == "stable"
    assert standards["RFC9110-Retry-After"]["status"] == "stable"
    assert standards["RFC9457-Problem-Details"]["status"] == "stable"
    assert (
        standards["draft-ietf-httpapi-ratelimit-headers-11"]["status"]
        == "active_draft_not_rfc"
    )
    assert (
        standards["draft-ietf-httpapi-idempotency-key-header-07"]["status"]
        == "expired"
    )

    now = dt.datetime(2026, 10, 3, 13, 0, 0, tzinfo=dt.timezone.utc)
    assert parse_retry_after("120", now=now) == 120.0
    assert (
        parse_retry_after(
            "Sat, 03 Oct 2026 13:02:00 GMT",
            now=now,
        )
        == 120.0
    )
    assert parse_retry_after("definitely-not-a-date", now=now) is None
    assert parse_retry_after(None, now=now) is None

    assert (
        parse_draft_ratelimit_zero_window('"default";r=0;t=30')
        == 30.0
    )
    assert parse_draft_ratelimit_zero_window('"default";r=1;t=30') is None
    assert parse_draft_ratelimit_zero_window(None) is None

    results = {
        row["scenario_id"]: scenario_decision(row)
        for row in scenarios_doc["scenarios"]
    }

    retry_seconds = results["retry-after-seconds"]
    assert retry_seconds["action"] == "WAIT_THEN_RETRY"
    assert retry_seconds["retry_after_floor_s"] == 120.0
    assert retry_seconds["next_start_s"] >= 220.3
    assert retry_seconds["herd_jitter_s"] >= 0.0
    assert "RFC6585-429" in retry_seconds["standards_used"]
    assert "RFC9110-Retry-After" in retry_seconds["standards_used"]

    retry_date = results["retry-after-http-date"]
    assert retry_date["retry_after_floor_s"] == 120.0
    assert retry_date["next_start_s"] >= 320.1

    fast_fail = results["fast-fail-no-server-delay"]
    assert fast_fail["action"] == "WAIT_THEN_RETRY"
    assert fast_fail["next_start_s"] >= 310.0
    assert fast_fail["local_backoff_s"] == 8.0

    draft_hint = results["draft-ratelimit-zero"]
    assert draft_hint["draft_ratelimit_floor_s"] == 30.0
    assert draft_hint["next_start_s"] >= 430.2
    assert (
        "draft-ietf-httpapi-ratelimit-headers-11"
        in draft_hint["standards_used"]
    )

    precedence = results["retry-after-dominates-draft"]
    assert precedence["retry_after_floor_s"] == 90.0
    assert precedence["draft_ratelimit_floor_s"] == 0.0
    assert precedence["next_start_s"] >= 590.2

    ambiguous = results["ambiguous-post"]
    assert ambiguous["action"] == "REOBSERVE"
    assert ambiguous["next_start_s"] is None

    explicit = results["ambiguous-post-explicit-contract"]
    assert explicit["action"] == "WAIT_THEN_RETRY"
    assert explicit["next_start_s"] >= 710.0

    applied = results["known-applied"]
    assert applied["action"] == "STOP_DUPLICATE"
    assert applied["next_start_s"] is None

    budget = results["budget-exhausted"]
    assert budget["action"] == "STOP_BUDGET"
    assert budget["next_start_s"] is None

    malformed = results["malformed-retry-after"]
    assert malformed["retry_after_floor_s"] == 0.0
    assert malformed["next_start_s"] >= 1010.0

    # operation_id stays stable while attempt_id changes.
    base_args = dict(
        status=429,
        method="GET",
        operation_state="read_only_observation",
        application_idempotency_contract=False,
        retry_budget=6,
        operation_id="op-stable",
        now_s=1100.2,
        previous_start_s=1100.0,
        minimum_period_s=10.0,
        retry_after=None,
        draft_ratelimit=None,
        local_base_s=2.0,
        local_cap_s=60.0,
        herd_jitter_fraction=0.2,
        now_datetime=now,
    )
    a1 = decide(attempt_number=1, **base_args)
    a2 = decide(attempt_number=2, **base_args)
    assert a1.operation_id == a2.operation_id == "op-stable"
    assert a1.attempt_id != a2.attempt_id

    # Server floor can never be violated by herd jitter.
    for n in range(1, 6):
        d = decide(
            status=429,
            method="GET",
            operation_state="read_only_observation",
            application_idempotency_contract=False,
            attempt_number=n,
            retry_budget=10,
            operation_id=f"op-floor-{n}",
            now_s=1200.2,
            previous_start_s=1200.0,
            minimum_period_s=10.0,
            retry_after="45",
            draft_ratelimit='"default";r=0;t=5',
            local_base_s=2.0,
            local_cap_s=60.0,
            herd_jitter_fraction=0.2,
            now_datetime=now,
        )
        assert d.next_start_s is not None
        assert d.next_start_s >= 1245.2
        assert d.draft_ratelimit_floor_s == 0.0
        assert d.herd_jitter_s >= 0.0

    print(
        json.dumps(
            {
                "status": "PASS",
                "scenarios": len(results),
                "stable_rfc_rules": 3,
                "active_draft_rules": 1,
                "expired_draft_rules": 1,
                "retry_after_is_floor": True,
                "negative_jitter_allowed": False,
                "ambiguous_post_without_contract": "REOBSERVE",
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
