# Recovery design proposal

This document is a client-side design proposal derived from the observed
failure dynamics. It is **not** a description of OpenAI's implementation.

## Goal

Recover a readable view of an already-existing conversation without turning
transport/recovery failure into an uncontrolled observation loop.

The target is synchronization recovery, not message regeneration:

~~~text
existing canonical conversation
        |
        v
cheap re-observation
        |
        v
version/snapshot reconciliation
        |
        v
stream reattachment
        |
        v
readable UI
~~~

## Invariants

1. **Transport failure is not canonical-data loss.**
2. **Re-observation is not re-execution.**
3. **An unknown recovery state is not permission to retry immediately.**
4. **At most one expensive snapshot recovery should be in flight per
   conversation recovery epoch.**
5. **429 is a control signal:** it should increase spacing, not shorten the next
   cycle indirectly through fast failure.
6. **A brief accessible excursion is not necessarily stable recovery.**

## Why completion-coupled polling is risky here

The public trace is well approximated by:

~~~text
cycle_time ~= service_time + ~5.6 s
~~~

When an accessible snapshot takes about 5 s, the whole cycle is roughly 10 s.
When a blocked request fails in roughly 0.3 s, the same post-completion delay
produces roughly a 6 s cycle.

So even an unchanged logical wait policy can produce a much higher attempt rate
during fast failure.

## Proposed scheduler

Anchor retry spacing to the previous **start time** and to the error class, not
only to completion time:

~~~text
next_start =
    max(
        last_start + minimum_period,
        now + error_backoff(error_class, consecutive_failures)
    )
~~~

For throttling / 429:

- honor a server-provided retry delay when available;
- otherwise use exponential backoff with jitter;
- cap attempts with a retry budget;
- open a circuit after repeated throttling and allow only sparse probes.

This prevents a fast rejection from automatically increasing request frequency.

General retry/backoff guidance:
https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html

## Recovery state machine

~~~mermaid
flowchart TD
    H[Healthy / readable] -->|stream or load anomaly| O[Observe]
    O -->|cheap observation succeeds| S[Sync]
    O -->|429 / throttled| C[Circuit open / backoff]
    O -->|ambiguous transport failure| W[Wait + bounded probe]
    W --> O
    C -->|probe window| O
    S -->|snapshot/version reconciled| R[Reattach stream]
    R -->|stable confirmation| H
    R -->|unstable / contradictory| O
~~~

## Recovery actions by cost

### 1. Preserve last-known-good UI

If a readable cached conversation exists, keep it visible while recovery occurs.
Mark it stale/reconnecting rather than replacing it with an empty or failed
view.

### 2. Re-observe cheaply

Prefer a lightweight status/version observation over downloading the full
conversation repeatedly.

If the service supports a version token, cursor, ETag-like validator, or other
conditional mechanism, use it to answer:

~~~text
Has canonical state changed?
Is a newer snapshot required?
Can the stream resume from the known point?
~~~

This repository does not assert that any specific validator exists internally.

### 3. Single-flight the expensive snapshot

Coalesce concurrent requests for the same conversation recovery epoch:

~~~text
many local recovery triggers
        -> one snapshot fetch
        -> shared result
~~~

If multiple same-origin tabs/windows can coordinate safely, a shared recovery
lease can further avoid duplicate full-snapshot work. This is an optional
client design idea, not a claim about the observed implementation.

### 4. Reconcile atomically

Apply a successful snapshot/version result as one state transition. Do not let
an older late response overwrite a newer local view.

### 5. Reattach the stream

Only after the snapshot/version state is coherent, attempt stream/realtime
reattachment from the latest known position.

### 6. Require recovery hysteresis

The trace contains brief accessible observations inside longer blocked periods.
Therefore, declaring recovery after one success can cause oscillation.

Possible policy:

~~~text
Recovered =
    snapshot readable
    AND stream/status healthy
    AND no throttling during a short stability window
~~~

The exact thresholds should be measured rather than copied from this single
capture.

## Retry budget

A simple token-bucket style recovery budget can prevent local positive feedback.

Conceptually:

~~~text
budget_(t+1) =
    min(max_budget,
        budget_t
        + success_refill
        - retry_cost)
~~~

When the budget is exhausted, stop active recovery and wait for a later probe
window. This is analogous to retry-quota designs used in production SDKs.

## Proposed control objective

Let:

- D_t = divergence between local readable state and canonical state;
- Q_t = retry/rate-limit pressure;
- B_t = bytes transferred by recovery;
- E_t = user-visible unavailability.

A recovery controller should minimize a cost such as:

~~~text
J = E[ sum_t (
      w_D * D_t
    + w_Q * Q_t
    + w_B * B_t
    + w_E * E_t
) ]
~~~

subject to the invariant that recovery observations do not themselves create
new conversation operations.

This is naturally a partially observed control problem: the client observes
HTTP/transport outcomes and cached state, but not the service's internal
capacity/rate-limit state.

## Testable predictions

A safer recovery design should produce all of the following under injected
failure:

1. failure latency can fall without increasing start-to-start attempt rate;
2. 429 causes attempt spacing to increase;
3. duplicate recovery triggers coalesce into one expensive snapshot;
4. brief one-cycle success does not immediately reset all backoff state;
5. stale-but-readable UI survives transient observation failure;
6. successful reattachment converges to a stable healthy state without an
   immediate blocked rebound.

These can be tested in a local simulator or mock service without load-testing a
production endpoint.
