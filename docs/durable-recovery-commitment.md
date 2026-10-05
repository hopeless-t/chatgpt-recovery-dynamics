# Durable recovery Commitment model

Status: research proposal; no production OpenAI claim

Source intake: https://note.com/npaka/n/n341b20a052c6

## Why it fits Recovery Dynamics

Recovery is naturally a long-lived objective that should survive UI sessions and process restarts, but it is dangerous to encode that persistence as "keep retrying until success."

The safer abstraction is a durable recovery Commitment whose default wake behavior is **observe first**.

```text
objective: obtain stable accessible state
state: BLOCKED | RECOVERING | HEALTHY
terminal_condition: stable confirmation
next_wakeup: bounded observation time
```

## Core law

```text
Recovery Commitment != Retry Loop
Wakeup != Request Permission
Transient Success != Stable Recovery
No Observation != Failure
Ambiguous Result != Redispatch Permission
```

## Candidate controller

```text
persist recovery state
  -> sleep
  -> wake on timer / external signal
  -> cheap observation
  -> reconcile current state
  -> only then decide whether any heavier fetch is justified
  -> persist evidence
  -> return to sleep or close on stable confirmation
```

This composes directly with the repository's `B -> E -> H` model and "Retry less. Observe more." principle.

## Simulation extension

Compare equal recovery semantics implemented as:

1. completion-coupled retry loop;
2. durable Commitment with periodic observation;
3. durable Commitment with event-driven observation when available plus bounded audit timer;
4. same as (3) with process death between every transition.

Measure:

- request amplification;
- payload bytes;
- time to stable H;
- false-H declarations;
- duplicate work after restart;
- state loss after process death;
- observation-to-materialization ratio.

## Strong acceptance criterion

A process restart should not erase recovery state, but persisted state must not itself cause extra network pressure.

> **Persist recovery meaning, not retry momentum.**