# HTTP 429 Survival Kit / 429救難キット

> **When the network says "slow down", do not turn recovery into a denial-of-service against yourself.**

This is a vendor-neutral client-control reference for HTTP throttling and ambiguous recovery.

It sends **no production traffic**.

## Stable standards layer

| Surface | Status | Repository interpretation |
|---|---|---|
| HTTP 429 | RFC 6585 | Backpressure/status signal. Limiter scope and root cause remain unknown. |
| `Retry-After` | RFC 9110 §10.2.3 | Minimum wait floor. Never jitter earlier than it. |
| Problem Details | RFC 9457 | Structured error representation. Do not parse human `detail` as a machine control channel. |

References:

- https://www.rfc-editor.org/rfc/rfc6585.html#section-4
- https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3
- https://www.rfc-editor.org/rfc/rfc9457.html

## Draft layer — deliberately isolated

As of the repository snapshot date **2026-10-03**:

- `draft-ietf-httpapi-ratelimit-headers-11` is an active Internet-Draft, **not an RFC**.
- `draft-ietf-httpapi-idempotency-key-header-07` is expired.

References:

- https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
- https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/

The reference client supports only one tiny experimental RateLimit hint:

```http
RateLimit: "default";r=0;t=30
```

and only when a stronger stable `Retry-After` signal is absent.

This is not a complete Structured Fields implementation.

## The central timing rule

```text
next_start =
    max(
        previous_start + minimum_period,
        now + Retry-After floor,
        now + experimental draft RateLimit zero-quota hint,
        now + local exponential backoff
    )
    + nonnegative herd jitter
```

The nonnegative part matters.

A common retry recipe says “Retry-After + ±20% jitter”. If negative jitter is applied after a server-provided minimum delay, a client can return **before the requested floor**.

This kit instead uses:

> **server floor first, jitter only later**

## Authorization is separate from timing

Knowing **when** a retry is allowed does not tell us **whether** execution is safe.

```text
known applied
    -> STOP_DUPLICATE

known not applied
    -> TIMED_RETRY

read-only observation
    -> TIMED_RETRY

unknown non-idempotent outcome
    + no explicit application/provider idempotency contract
    -> REOBSERVE

unknown non-idempotent outcome
    + explicit application/provider idempotency contract
    -> TIMED_RETRY
```

An expired IETF Idempotency-Key draft is not treated as universal provider support.

## Identity

```text
operation_id = stable logical operation identity
attempt_id   = changes per network attempt
```

Transport/retry churn does not mint a new logical operation.

## Retry budget

Attempts are bounded.

When the retry budget is exhausted:

```text
STOP_BUDGET
```

The correct response to overload is not infinite optimism.

## First recovery success

The existing Recovery Dynamics rule remains:

```text
Blocked
  -> first successful observation
  -> Recovering / E
  -> stable confirmation
  -> Healthy / H
```

One green response is not automatically stable recovery.

## Reproduce

```bash
python scripts/http_429_survival.py \
  --scenarios data/http_429_survival_scenarios.json \
  --output /tmp/http-429-survival.json

python scripts/validate_http_429_survival.py
```

## Safety

Do not use this repository to:

- deliberately create production 429 storms;
- evade or bypass rate limits;
- probe private limiter implementation;
- retry non-idempotent side effects blindly;
- treat a status code as proof of internal architecture.

## Purrtocol rescue doctrine

> **Retry less. Observe more.**

The fire extinguisher is not another POST button.
