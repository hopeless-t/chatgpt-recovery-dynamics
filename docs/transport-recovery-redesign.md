# Transport and recovery-path redesign

## Scope

This is a client-side design proposal informed by the observed recovery dynamics.
It is not a description of ChatGPT's internal architecture.

Goal:

> preserve correctness and readable conversation state across transport failure without turning recovery itself into a retry/429 amplifier.

The design separates application state, transport attempts, recovery observation, and realtime notification.

## Evidence that changes the design

The A -> B biopsy found:

~~~text
B -> E -> B : 8 observed
B -> E -> H : 0 observed
~~~

where H is established Accessible, E is the first Accessible excursion immediately after Blocked, and B is Blocked.

Therefore a first successful observation enters Recovering/E, not Healthy/H.

## Proposed Conversation Recovery Survival Plane

### 1. Durable application identity

Transport retries must not create new logical work.

~~~text
conversation_id
conversation_version
recovery_id
operation_id        # when an operation exists
attempt_id
~~~

Rules:

~~~text
transport retry: recovery_id / operation_id stays fixed
transport retry: attempt_id changes

transport failure != operation failure
re-observation != re-execution
UNKNOWN != permission to retry execution
~~~

### 2. Cheap observation before expensive materialization

Do not repeatedly download the full conversation merely to learn whether it is readable again.

~~~text
cheap state/version observation
        |
        +-- blocked/throttled --> bounded retry controller
        +-- first success ------> E / Recovering
        +-- stable success -----> full snapshot once -> atomic reconcile
~~~

A lightweight state request could use a conditional validator, explicit conversation-version token, or small metadata resource. The repository does not claim such an endpoint currently exists.

### 3. Single-flight recovery ownership

Multiple tabs/windows should share one per-conversation recovery lease rather than run independent expensive recovery loops.

~~~text
many local triggers -> one recovery owner -> one expensive snapshot -> shared result
~~~

### 4. Start-anchored retry scheduling

The observed cycle law is:

~~~text
Delta ~= 5.616 + 0.957 * service_time
~~~

Use:

~~~text
next_start = max(
    previous_start + T_normal,
    now + server_retry_delay,
    now + local_error_backoff
)
~~~

For this capture T_normal is approximately 10 s from the healthy-cycle bootstrap.

429 should increase or preserve spacing, never shorten it indirectly because a failure completed quickly. Only one layer should own retries.

### 5. Recovery hysteresis

~~~text
B / Blocked --success--> E / Recovering
E / Recovering --stable confirmation--> H / Healthy
E / Recovering --failure--> B / Blocked
~~~

One successful observation is not enough.

### 6. Transport choice

HTTP/2 is the preferred baseline because it provides multiplexed independent request streams, stream-level error isolation, GOAWAY semantics, and explicit safe-retry cases for unprocessed requests.

Reference: https://www.rfc-editor.org/rfc/rfc9113.html

HTTP/1.1 remains a correctness-preserving fallback. The application recovery state must not depend on H2-only connection state.

HTTP/3 is an optional acceleration path. QUIC connection migration can preserve a connection across client path/address changes, but this does not solve 429 or state ambiguity.

References:
- https://www.rfc-editor.org/rfc/rfc9114.html
- https://www.rfc-editor.org/rfc/rfc9000.html

WebSocket can remain useful for realtime notification, but loss of the socket should mean realtime observation degraded, not canonical conversation lost and not permission to replay work.

### Stateless transport precedent

MCP 2026-07-28 is a useful design precedent, not a proposal that ChatGPT conversation recovery should use MCP. That revision removed protocol-level sessions/handshakes and moved toward self-contained per-request HTTP exchanges, while application state can be carried explicitly.

References:
- https://blog.modelcontextprotocol.io/posts/2026-07-28/
- https://ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28

## Monte Carlo path comparison

GitHub Actions runs 5,000 trials per path/model with common random numbers.

Paths:

- P0 completion_per_context: ~6 s completion-coupled cycles, independent local contexts, full snapshots.
- P1 anchored_singleflight_full: one shared loop, >=10 s start-to-start, full snapshots, two-round confirmation.
- P2 observe_then_snapshot: one shared loop, >=10 s start-to-start, conceptual 4 KiB state probe, two-round confirmation, then one 4.684 MiB snapshot.

The 4 KiB probe size is a simulation assumption. The 4.684 MiB snapshot size comes from the public rounded capture.

### Naive first-success recovery

Under the biopsy-derived adverse history model:

~~~text
posterior-predictive immediate rebound after first A ~= 94.5%
~~~

This is a stress result, not a production probability.

### Request-count pressure stress model

| Path | Stable recovery | Mean requests | Mean payload |
|---|---:|---:|---:|
| P0 completion/context | 20.36% | 38.66 | 28.96 MiB |
| P1 anchor+single-flight | 68.18% | 11.29 | 13.49 MiB |
| P2 observe->snapshot | 68.18% | 11.29 | 4.62 MiB |

Cheap observation does not receive an artificial rate-limit advantage here: every request has equal hypothetical pressure cost. Its benefit is lower materialization cost.

### Byte/work-weighted pressure stress model

| Path | Stable recovery | p95 recovery | Mean payload |
|---|---:|---:|---:|
| P0 completion/context | 21.0% | 537.3 s | 29.07 MiB |
| P1 anchor+single-flight | 68.98% | 370 s | 13.26 MiB |
| P2 observe->snapshot | 100% | 70 s | 4.59 MiB |

This is intentionally hypothetical. It says that if pressure scales materially with expensive snapshot work, observe-before-materialize can dominate. It does not identify the production limiter.

### Latent wall-clock recovery model

| Path | Recovery | Mean payload | p95 detection delay |
|---|---:|---:|---:|
| P0 completion/context | 100% | 22.80 MiB | 11.69 s |
| P1 anchor+single-flight | 100% | 9.15 MiB | 19.54 s |
| P2 observe->snapshot | 100% | 4.60 MiB | 19.54 s |

The redesign pays detection delay for lower request/snapshot cost.

### Adverse attempt-driven model

| Path | Recovery by 1200 s | Mean requests | Mean payload |
|---|---:|---:|---:|
| P0 completion/context | 58.32% | 146.66 | 180.78 MiB |
| P1 anchor+single-flight | 38.22% | 47.03 | 32.82 MiB |
| P2 observe->snapshot | 38.22% | 47.03 | 4.76 MiB |

This deliberately hurts conservative recovery. It prevents a universal-dominance claim and makes the proposal a robust/minimax tradeoff.

### Optional H3 path-churn sensitivity

Assumption-only ranges: path-change interval 30..600 s, H2/TCP reconnect penalty 0.5..3.0 s, QUIC migration survival 50%..95%, migration validation 0.1..0.5 s.

For a 60 s recovery window:

~~~text
P(any path change) ~= 40.2%
H2 mean added delay ~= 1.10 s
H3 mean added delay ~= 0.44 s
H3/H2 mean delay ratio ~= 0.40
~~~

This is only a QUIC migration sensitivity demonstration. The architecture must remain correct if H3 provides zero benefit.

## Recommended path

~~~text
local triggers
    -> single-flight recovery lease
    -> cheap state/version observation
    -> bounded start-anchored retry if blocked
    -> E / Recovering on first success
    -> stable confirmation
    -> full snapshot once
    -> atomic reconcile
    -> optional realtime reattach
~~~

Transport preference:

~~~text
HTTP/2      preferred baseline
HTTP/1.1    correctness-preserving fallback
HTTP/3      optional path-survival acceleration
WebSocket   optional realtime notification only
~~~

## Reproduce

~~~bash
python3 scripts/simulate_transport_recovery_paths.py
~~~

## Limitations

The simulation does not identify the production rate-limit function, current cross-tab coordination, production HTTP version, internal snapshot validators, or WebSocket's internal role.

The proposal is a falsifiable recovery architecture tested under several causal models, not a reconstruction of OpenAI internals.