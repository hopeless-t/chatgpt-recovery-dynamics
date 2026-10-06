# Adopt the Recovery Semantics

You do **not** need to fork the entire research repository to use the recovery ideas.

This guide extracts the smallest reusable design.

## Minimal state

Track two identities:

```text
operation_id = stable identity of the semantic action
attempt_id   = identity of one concrete execution attempt
```

A retry keeps `operation_id` stable and creates a new `attempt_id`.

Also track enough durable state to answer:

- did the operation definitely complete?
- did it definitely fail before the side effect?
- is the outcome unknown?
- is replay allowed for this operation class?
- when is the earliest legal next attempt?
- how much recovery confidence has accumulated?

## Minimal replay classes

A useful starting split is:

```text
ReplaySafe
AtMostOnce
ExternallyDeduplicated
```

### ReplaySafe

The operation can be repeated without changing meaning or duplicating a harmful side effect.

### AtMostOnce

If the result is ambiguous, do not blindly repeat it. Re-observe durable state or escalate.

### ExternallyDeduplicated

Replay is permitted only because a stable idempotency/deduplication key is enforced by the receiving system.

## Minimal decision order

```text
1. classify the outcome
2. inspect durable state when outcome is UNKNOWN
3. classify replay safety
4. obey server retry floors such as Retry-After
5. enforce a local retry budget
6. use single-flight recovery per semantic operation
7. create a new attempt_id only when retry is authorized
8. do not declare Healthy on the first success after a Blocked period
```

## Observe before materialize

Prefer the cheapest query that can answer the recovery question.

For example:

```text
HEAD/status lookup/checkpoint read
        before
full transcript fetch/large object rebuild/re-execution
```

This separates recovery **knowledge** from recovery **work**.

## Single-flight

When many callers notice the same degraded operation, elect one recovery owner or share one in-flight recovery future.

Do not allow every observer to wake the same cold capability, refetch the same heavy state, or replay the same operation independently.

## Recovery confidence

Use at least three conceptual states:

```text
B = Blocked
E = Recovering
H = Healthy
```

Recommended transition discipline:

```text
B + first success -> E
E + renewed failure -> B
E + stable confirmations -> H
```

The exact confirmation count and timing are system-specific. The repository's fixture values are test parameters, not universal provider guidance.

## Pseudocode

```text
recover(operation):
    state = observe(operation.operation_id)

    if state.completed:
        return COMPLETED

    if state.outcome == UNKNOWN and operation.replay_class == AtMostOnce:
        return REOBSERVE_OR_ESCALATE

    floor = max(server_retry_floor, local_pacing_floor)

    if retry_budget_exhausted(operation):
        return INCOMPLETE

    await floor

    if another_recovery_is_in_flight(operation.operation_id):
        return JOIN_EXISTING_RECOVERY

    attempt_id = new_attempt_id()
    return execute(operation.operation_id, attempt_id)
```

## What not to copy blindly

Do not copy this repository's observed timing values into production as universal constants.

Do not infer a provider's internal queue, capacity, rate-limit scope, or root cause from the public trace.

Do not treat Purrtocol visualizations as empirical evidence.

## Conformance target

If you want a small normative target for your implementation, use [Recovery Survival Contract v0.1](RECOVERY_SURVIVAL_CONTRACT_V0_1.md).

If you want to compare behavior with the repository's local reference implementation, run [QUICKSTART.md](QUICKSTART.md).
