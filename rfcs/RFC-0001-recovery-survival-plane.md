# RFC-0001: Conversation Recovery Survival Plane

- Status: Draft
- Audience: client, transport, recovery, reliability engineers
- Scope: conceptual architecture; not a reconstruction of OpenAI internals

## Abstract

This RFC specifies a transport-agnostic recovery plane for restoring readable conversation state without coupling canonical truth to one network connection.

## Invariants

~~~text
transport failure != canonical conversation loss
transport attempt != logical recovery
re-observation != re-execution
first success != stable recovery
UNKNOWN != retry permission
~~~

## Logical identity

A recovery implementation should preserve stable application identity across transport attempts.

Conceptually:

~~~text
conversation_id
conversation_version
recovery_id
operation_id      # when logical work exists
attempt_id
~~~

Transport retry changes attempt_id, not the logical recovery identity.

## Recovery flow

~~~text
local triggers
 -> single-flight owner
 -> cheap state/version observation
 -> start-anchored retry if blocked
 -> Recovering / E on first success
 -> stable confirmation
 -> one snapshot or delta materialization
 -> atomic reconcile
 -> optional realtime reattach
~~~

## Transport profile

~~~text
HTTP/2      preferred baseline
HTTP/1.1    correctness-preserving fallback
HTTP/3      optional path-survival acceleration
WebSocket   optional realtime observation/notification
~~~

No transport session is canonical conversation truth.

## Retry scheduling

~~~text
next_start = max(
    previous_start + normal_period,
    server_retry_delay,
    local_backoff_with_jitter
)
~~~

Fast failure must not create a faster start-to-start retry cycle.

## Recovery confirmation

The first readable observation enters E / Recovering. A later independent observation or stability window is required before transition to H / Healthy.

## Security / safety

- Do not bypass rate limits.
- Honor server-directed backpressure.
- Do not blindly replay mutating work after ambiguous disconnect.
- Prefer re-observation of durable state.

## Open questions

- Best stable-confirmation window.
- Whether delta synchronization is available or useful.
- Fairness scope for recovery traffic.
- Adaptive concurrency policy.
- Replication across independent clients/captures.
