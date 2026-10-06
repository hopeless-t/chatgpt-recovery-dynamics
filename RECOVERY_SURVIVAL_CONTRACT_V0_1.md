# Recovery Survival Contract v0.1

Status: **draft interoperability contract**

This document defines a deliberately small recovery surface that implementations can adopt without reproducing the full research repository.

Normative words `MUST`, `MUST NOT`, `SHOULD`, and `MAY` are used in their ordinary standards sense.

## 1. Scope

The contract applies when an operation can fail, time out, receive a rate-limit response, lose its transport, or finish with an ambiguous result.

It does not specify provider internals or universal retry timing constants.

## 2. Identity

An implementation MUST distinguish:

- `operation_id`: stable identity of the semantic operation;
- `attempt_id`: identity of one concrete execution attempt.

A retry of the same semantic operation MUST preserve `operation_id` and MUST use a new `attempt_id`.

An implementation MUST NOT infer a new semantic operation merely because a transport/session/attempt changed.

## 3. Outcome classification

At minimum, an attempt outcome MUST be classifiable as:

- known completed;
- known failed before the relevant side effect;
- unknown/ambiguous.

`UNKNOWN` MUST NOT itself authorize replay.

## 4. Replay safety

Before replay, an operation MUST have an explicit replay policy.

The minimum useful classes are:

- `ReplaySafe`;
- `AtMostOnce`;
- `ExternallyDeduplicated`.

For `AtMostOnce`, an ambiguous outcome MUST NOT be blindly replayed.

For `ExternallyDeduplicated`, replay MUST retain a stable external deduplication/idempotency identity appropriate to the receiving system.

## 5. Re-observation

When an outcome is ambiguous, an implementation SHOULD perform the cheapest sufficient durable-state observation before heavier recovery work.

Re-observation MUST be treated as distinct from re-execution.

A successful observation MAY terminate recovery without another execution attempt.

## 6. Retry floors

When a server supplies an authoritative retry floor such as `Retry-After`, a client MUST NOT schedule the next attempt earlier than that floor.

Local pacing MAY make the wait longer.

Local pacing MUST NOT shorten an authoritative server floor.

## 7. Retry budget

Recovery MUST have a finite local budget per semantic operation or recovery episode.

Budget exhaustion MUST terminate automatic retry authorization.

Budget exhaustion SHOULD be represented as incomplete/unresolved rather than silently converted into success.

## 8. Single-flight recovery

Concurrent observers of the same semantic operation SHOULD share or elect one recovery execution lane.

A client SHOULD avoid duplicate heavy observation, duplicate capability wake, or duplicate replay caused only by concurrent recovery observers.

## 9. Recovery confidence

An implementation MUST NOT equate the first post-failure success with stable health by default.

A compatible confidence model SHOULD distinguish at least:

```text
Blocked -> Recovering -> Healthy
```

A renewed failure during `Recovering` SHOULD return confidence to `Blocked`.

Promotion from `Recovering` to `Healthy` SHOULD require explicit confirmation policy.

## 10. Evidence boundary

A conformance result proves only behavior under the tested contract scenarios.

It MUST NOT be represented as proof of:

- a provider's internal architecture;
- provider-wide capacity;
- an internal root cause;
- universal retry thresholds;
- production safety beyond the exercised environment.

Visualization MUST NOT be promoted to empirical evidence.

## 11. Minimal conformance checklist

An implementation claiming compatibility with this draft SHOULD demonstrate all of the following:

- stable `operation_id` across retry attempts;
- fresh `attempt_id` per execution attempt;
- ambiguous non-idempotent outcome does not blindly replay;
- authoritative retry floor is never shortened;
- retry budget terminates repeated attempts;
- re-observation can resolve completion without re-execution;
- concurrent recovery does not create duplicate execution lanes for the same operation;
- first post-Blocked success enters a provisional recovery state rather than automatically declaring Healthy.

## 12. Compatibility phrase

A project MAY describe itself as:

> `Recovery Survival Contract v0.1 compatible`

only when its documented behavior satisfies the applicable MUST/MUST NOT requirements above.

Because v0.1 is a draft interoperability surface, implementations SHOULD also identify any deliberate deviations.

---

Project principle:

> **Recover. Don't amplify.**
