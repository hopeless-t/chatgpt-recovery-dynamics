# RFC-0003 — HTTP 429 Survival Plane

Status: **PROPOSED / executable reference**

## Problem

A retry loop can transform a transient overload signal into more offered work.

This repository's public trace showed a specific cadence amplifier:

```text
cycle ~= service time + post-completion wait
```

so a fast failure can make a completion-coupled loop run faster even when the
explicit wait policy is unchanged.

A general HTTP client also faces a separate problem:

> transport uncertainty and retry timing do not by themselves establish that a
> side-effecting operation is safe to execute again.

## Decision

Define a vendor-neutral survival plane with two independent gates:

```text
retry authorization
        ×
retry timing
```

A request proceeds only when both permit it.

## Timing plane

```text
next_start =
    max(
        previous_start + minimum_period,
        now + retry_after_floor,
        now + experimental_draft_quota_floor,
        now + local_backoff
    )
    + nonnegative_herd_jitter
```

### Why nonnegative jitter?

`Retry-After` expresses a server-directed minimum wait.

If a client applies symmetric jitter after that signal, a negative sample can
return early.

The survival plane therefore treats server-directed timing as a floor and uses
jitter only to delay beyond the floor.

## Authorization plane

```text
known applied
    -> STOP_DUPLICATE

known not applied
    -> TIMED_RETRY

read-only observation
    -> TIMED_RETRY

UNKNOWN + non-idempotent + no explicit application/provider contract
    -> REOBSERVE
```

HTTP method idempotency is useful, but automatic retry remains bounded by the
same timing and budget controls.

## Standards boundary

Stable:

- RFC 6585 — 429 Too Many Requests
- RFC 9110 — Retry-After
- RFC 9457 — Problem Details

Snapshot 2026-10-03:

- `draft-ietf-httpapi-ratelimit-headers-11` is active but remains an
  Internet-Draft.
- `draft-ietf-httpapi-idempotency-key-header-07` is expired.

Draft semantics are isolated so a future draft/RFC change does not silently
rewrite the stable control plane.

## Identity

```text
operation_id = stable
attempt_id   = changes per network attempt
```

The survival plane reuses the repository/MVCA-style distinction:

> **Attempt != Operation.**

## Retry budget

Infinite retry is not recovery.

A bounded budget eventually transitions to:

```text
STOP_BUDGET
```

A later sparse probe can be a new observation policy without pretending the
failed attempt succeeded.

## Problem Details

RFC 9457 can carry structured machine-readable error information.

The human-readable `detail` member is not parsed to derive retry timing or
execution authorization.

## RateLimit draft

The reference code intentionally implements only a tiny draft hint:

```http
RateLimit: "default";r=0;t=30
```

When and only when stable `Retry-After` is absent, this may contribute an
experimental timing floor.

This is not a full Structured Fields parser and does not claim RFC maturity.

## Safety

All validation uses local deterministic scenarios.

Do not deliberately trigger production 429s or attempt rate-limit evasion.

## Implementation

- `data/http_429_survival_contract.json`
- `data/http_429_survival_scenarios.json`
- `scripts/http_429_survival.py`
- `scripts/validate_http_429_survival.py`
- `docs/429-survival-kit/`

**Recover. Don't amplify.**
