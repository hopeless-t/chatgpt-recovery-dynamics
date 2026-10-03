#!/usr/bin/env python3
"""Vendor-neutral HTTP 429 survival scheduler.

Standard-library only. This is a defensive client-control reference:
- honors Retry-After as a floor;
- prevents fast failure from shortening the retry cycle;
- adds only nonnegative herd jitter after all timing floors;
- keeps retry authorization separate from timing;
- treats ambiguous non-idempotent outcomes as re-observation problems.

It does not send network traffic.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import email.utils
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data" / "http_429_survival_contract.json"

_IDEMPOTENT_METHODS = {"GET", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE"}
_RATELIMIT_ZERO_RE = re.compile(
    r'(?:^|,)\s*(?:"[^"]*"|[A-Za-z0-9._~-]+)\s*;[^,]*\br=0\b[^,]*\bt=(\d+)\b',
    re.IGNORECASE,
)


@dataclasses.dataclass(frozen=True)
class RetryDecision:
    action: str
    reason: str
    next_start_s: float | None
    retry_after_floor_s: float
    draft_ratelimit_floor_s: float
    local_backoff_s: float
    herd_jitter_s: float
    operation_id: str
    attempt_id: str
    attempt_number: int
    budget_remaining_after_attempt: int
    standards_used: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def parse_retry_after(value: str | None, *, now: dt.datetime) -> float | None:
    """Return seconds to wait from now, or None for invalid/absent input."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None

    if value.isdigit():
        return float(int(value))

    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)

    now_utc = now.astimezone(dt.timezone.utc)
    return max(
        0.0,
        (parsed.astimezone(dt.timezone.utc) - now_utc).total_seconds(),
    )


def parse_draft_ratelimit_zero_window(value: str | None) -> float | None:
    """Parse the deliberately tiny draft hint supported by this repo.

    Supported example:
        RateLimit: "default";r=0;t=30

    This is NOT a complete RFC 8941 Structured Fields parser.
    """
    if value is None:
        return None
    match = _RATELIMIT_ZERO_RE.search(value)
    if not match:
        return None
    return float(int(match.group(1)))


def deterministic_unit_interval(key: str) -> float:
    raw = hashlib.sha256(key.encode("utf-8")).digest()
    number = int.from_bytes(raw[:8], "big")
    return number / float((1 << 64) - 1)


def exponential_backoff(
    attempt_number: int,
    *,
    base_s: float,
    cap_s: float,
) -> float:
    if attempt_number < 1:
        raise ValueError("attempt_number must be >= 1")
    if base_s < 0 or cap_s < 0:
        raise ValueError("backoff values must be non-negative")
    if cap_s < base_s:
        raise ValueError("cap_s must be >= base_s")
    exponent = min(attempt_number - 1, 30)
    return min(cap_s, base_s * (2 ** exponent))


def retry_authorization(
    *,
    method: str,
    operation_state: str,
    application_idempotency_contract: bool,
) -> tuple[str, str]:
    method = method.upper()

    if operation_state == "known_applied":
        return "STOP_DUPLICATE", "operation already known applied"

    if operation_state in {"known_not_applied", "read_only_observation"}:
        return "TIMED_RETRY", "operation state permits a timed retry"

    if operation_state != "unknown":
        raise ValueError(f"unknown operation_state: {operation_state}")

    if method in _IDEMPOTENT_METHODS:
        return (
            "TIMED_RETRY",
            "unknown outcome but HTTP method semantics are idempotent; timing and budget still apply",
        )

    if application_idempotency_contract:
        return (
            "TIMED_RETRY",
            "unknown non-idempotent outcome covered by explicit application/provider idempotency contract",
        )

    return (
        "REOBSERVE",
        "unknown non-idempotent outcome without explicit idempotency contract",
    )


def decide(
    *,
    status: int | None,
    method: str,
    operation_state: str,
    application_idempotency_contract: bool,
    attempt_number: int,
    retry_budget: int,
    operation_id: str,
    now_s: float,
    previous_start_s: float,
    minimum_period_s: float,
    retry_after: str | None,
    draft_ratelimit: str | None,
    local_base_s: float,
    local_cap_s: float,
    herd_jitter_fraction: float,
    now_datetime: dt.datetime,
) -> RetryDecision:
    if attempt_number < 1:
        raise ValueError("attempt_number must be >= 1")
    if retry_budget < 1:
        raise ValueError("retry_budget must be >= 1")
    if minimum_period_s < 0:
        raise ValueError("minimum_period_s must be non-negative")
    if herd_jitter_fraction < 0:
        raise ValueError("herd_jitter_fraction must be non-negative")
    if now_s < previous_start_s:
        raise ValueError("now_s must be >= previous_start_s")

    attempt_id = f"{operation_id}:attempt:{attempt_number}"
    budget_remaining = max(0, retry_budget - attempt_number)

    auth_action, auth_reason = retry_authorization(
        method=method,
        operation_state=operation_state,
        application_idempotency_contract=application_idempotency_contract,
    )

    if auth_action == "STOP_DUPLICATE":
        return RetryDecision(
            action="STOP_DUPLICATE",
            reason=auth_reason,
            next_start_s=None,
            retry_after_floor_s=0.0,
            draft_ratelimit_floor_s=0.0,
            local_backoff_s=0.0,
            herd_jitter_s=0.0,
            operation_id=operation_id,
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            budget_remaining_after_attempt=budget_remaining,
            standards_used=(),
        )

    if auth_action == "REOBSERVE":
        return RetryDecision(
            action="REOBSERVE",
            reason=auth_reason,
            next_start_s=None,
            retry_after_floor_s=0.0,
            draft_ratelimit_floor_s=0.0,
            local_backoff_s=0.0,
            herd_jitter_s=0.0,
            operation_id=operation_id,
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            budget_remaining_after_attempt=budget_remaining,
            standards_used=("RFC9110-idempotent-method-semantics",),
        )

    if attempt_number >= retry_budget:
        return RetryDecision(
            action="STOP_BUDGET",
            reason="retry budget exhausted",
            next_start_s=None,
            retry_after_floor_s=0.0,
            draft_ratelimit_floor_s=0.0,
            local_backoff_s=0.0,
            herd_jitter_s=0.0,
            operation_id=operation_id,
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            budget_remaining_after_attempt=0,
            standards_used=(),
        )

    retry_after_s = parse_retry_after(retry_after, now=now_datetime)
    retry_after_floor = retry_after_s or 0.0

    draft_floor = 0.0
    draft_hint = parse_draft_ratelimit_zero_window(draft_ratelimit)
    if retry_after_s is None and draft_hint is not None:
        draft_floor = draft_hint

    local_backoff_s = exponential_backoff(
        attempt_number,
        base_s=local_base_s,
        cap_s=local_cap_s,
    )

    base_next = max(
        previous_start_s + minimum_period_s,
        now_s + retry_after_floor,
        now_s + draft_floor,
        now_s + local_backoff_s,
    )

    jitter_window = max(
        minimum_period_s,
        retry_after_floor,
        draft_floor,
        local_backoff_s,
        1.0,
    ) * herd_jitter_fraction

    herd_jitter_s = jitter_window * deterministic_unit_interval(
        f"{operation_id}:{attempt_number}:herd-jitter"
    )
    next_start_s = base_next + herd_jitter_s

    used = []
    if status == 429:
        used.append("RFC6585-429")
    if retry_after_s is not None:
        used.append("RFC9110-Retry-After")
    if draft_floor > 0:
        used.append("draft-ietf-httpapi-ratelimit-headers-11")

    return RetryDecision(
        action="WAIT_THEN_RETRY",
        reason=auth_reason,
        next_start_s=next_start_s,
        retry_after_floor_s=retry_after_floor,
        draft_ratelimit_floor_s=draft_floor,
        local_backoff_s=local_backoff_s,
        herd_jitter_s=herd_jitter_s,
        operation_id=operation_id,
        attempt_id=attempt_id,
        attempt_number=attempt_number,
        budget_remaining_after_attempt=budget_remaining,
        standards_used=tuple(used),
    )


def scenario_decision(scenario: dict[str, Any]) -> dict[str, Any]:
    now_datetime = dt.datetime.fromisoformat(
        scenario["now_datetime"].replace("Z", "+00:00")
    )
    result = decide(
        status=scenario.get("status"),
        method=scenario["method"],
        operation_state=scenario["operation_state"],
        application_idempotency_contract=scenario.get(
            "application_idempotency_contract",
            False,
        ),
        attempt_number=scenario["attempt_number"],
        retry_budget=scenario["retry_budget"],
        operation_id=scenario["operation_id"],
        now_s=scenario["now_s"],
        previous_start_s=scenario["previous_start_s"],
        minimum_period_s=scenario["minimum_period_s"],
        retry_after=scenario.get("retry_after"),
        draft_ratelimit=scenario.get("draft_ratelimit"),
        local_base_s=scenario["local_base_s"],
        local_cap_s=scenario["local_cap_s"],
        herd_jitter_fraction=scenario["herd_jitter_fraction"],
        now_datetime=now_datetime,
    )
    return result.as_dict()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    scenarios = json.loads(
        Path(args.scenarios).read_text(encoding="utf-8")
    )
    output = {
        "schema": "http-429-survival-reference/v1",
        "contract": str(CONTRACT_PATH.relative_to(ROOT)),
        "results": [
            {
                "scenario_id": row["scenario_id"],
                "description": row["description"],
                "decision": scenario_decision(row),
            }
            for row in scenarios["scenarios"]
        ],
    }
    text_output = json.dumps(output, indent=2, sort_keys=True) + "\n"
    print(text_output, end="")
    if args.output:
        Path(args.output).write_text(text_output, encoding="utf-8")


if __name__ == "__main__":
    main()
