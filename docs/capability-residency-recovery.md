# Capability Residency and Recovery Amplification

Date: 2026-10-05
Status: cross-pollination research note

## Trigger

Source discussion: https://gigazine.net/news/20261005-deepseek-harness/

If agent/harness capabilities may enter HOT/WARM/COLD/OFF states, then recovery logic gains a new failure mode: a user-visible operation can arrive while a required capability is cold or waking.

That creates a retry-amplification question directly aligned with this repository.

## State sketch

```text
OFF -> COLD -> WARM -> HOT
              ^       |
              |       v
           demotion / failure
```

A task requiring a non-HOT capability should not cause every observer/client to independently trigger a wake or replay.

## Failure pattern

Naive behavior:

```text
request arrives
  -> capability cold
  -> timeout / fast failure
  -> multiple clients retry
  -> each retry triggers wake/reconstruction work
  -> provider pressure rises
  -> more timeouts / fast failures
```

This is structurally similar to completion-coupled retry amplification.

## Recovery principle

Apply the existing project principle:

> Retry less. Observe more.

For cold capability activation:

```text
1. establish one wake owner (single-flight)
2. assign stable operation_id and wake_id
3. expose cheap wake/status observation
4. do not rematerialize full state just to ask whether wake is progressing
5. on ambiguous outcome, re-observe before replaying
6. respect server/provider-directed spacing
7. bound waiters and shed duplicate work
```

## Candidate state machine

```text
COLD
  --wake requested--> WAKING
WAKING
  --health pass--> HOT
WAKING
  --recoverable fail--> COLD
WAKING
  --uncertain side effect--> OBSERVE_ONLY
OBSERVE_ONLY
  --committed receipt--> HOT/COMPLETED
OBSERVE_ONLY
  --still uncertain--> STOP/ESCALATE
```

A single successful response immediately after wake should be treated as provisional recovery until stability criteria are met, mirroring the repository's existing Recovering state logic.

## Metrics

- duplicate wake requests per logical wake;
- total wake amplification;
- bytes transferred during health probing;
- wake p50/p95/p99 latency;
- waiter count and queue depth;
- cold-start failure rate;
- provisional-success rebound rate;
- unnecessary full-state materializations;
- provider-side rejected work;
- operation replay count.

## Simulation candidate

Extend the local server-friendly simulation with a capability wake service:

```text
foreground useful load
+ normal recovery load
+ cold-capability wake load
+ duplicate wake amplification
```

Compare:

1. every retry triggers wake;
2. Retry-After/jitter only;
3. single-flight wake;
4. single-flight + cheap observe-first + bounded waiters.

The purpose is not to model any specific OpenAI internal architecture. It is to test a generic recovery invariant for lifecycle-managed systems.

## Cross-repo hooks

- `mvca`: stable operation identity and re-observation semantics.
- `harness-component-economics`: cost of cold starts vs residency.
- `finite-ram-lab`: why capabilities may be demoted under constrained memory.
- `next-generation-github`: optional collaboration providers.

## Non-claim

This is a generic systems extension inspired by lifecycle-aware harness design. It does not claim that observed ChatGPT 429 behavior was caused by cold capability activation.
