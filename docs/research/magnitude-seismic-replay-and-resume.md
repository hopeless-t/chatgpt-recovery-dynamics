# Magnitude / Seismic lessons for recovery dynamics

## Core transfer

Magnitude's architecture separates semantic state, submission, completion, and accepted state, while its agent/runtime design explicitly distinguishes replay-safe from at-most-once operations. That is directly relevant to recovery from 429s, interrupted streams, transport loss, partial tool completion, and context reconstruction.

## 1. Recovery needs typed transition states

Do not represent a workflow as only `started` / `done`.

Use a state machine closer to:

```text
Proposed
Checked
Planned
Bound
Authorized
Submitted
Completed
Observed
Accepted
```

Important distinctions:

- `Authorized` does not mean a side effect happened.
- `Submitted` does not mean it completed.
- `Completed` does not mean the result was observed.
- `Observed` does not mean it was accepted into canonical state.

Recovery should resume from the last evidenced transition, not from conversational guesswork.

## 2. Every side-effecting operation needs a replay class

Suggested vocabulary:

```text
ReplaySafe
AtMostOnce
ExternallyDeduplicated(key)
ReadOnly
```

Examples:

```text
read repository        -> ReplaySafe
create branch          -> ExternallyDeduplicated(branch-name)
post comment            -> AtMostOnce or deduplicated by request id
query status            -> ReplaySafe
send payment            -> AtMostOnce + explicit confirmation boundary
```

The recovery engine should refuse blind replay when the class is unknown.

## 3. Canonical event log over transcript reconstruction

A transcript is useful evidence but a weak recovery substrate. Maintain compact canonical events such as:

```text
operation.planned
operation.authorized
operation.submitted
operation.completed
operation.observed
operation.accepted
operation.failed
```

Each event should carry:

- stable operation id
- semantic digest
- replay class
- authority boundary
- external correlation/deduplication id if available
- evidence payload/digest
- predecessor state

Conversation text can then be reconstructed as a projection rather than serving as the sole execution ledger.

## 4. Budget exhaustion is an incomplete result

429s, token exhaustion, context pressure, wall-clock stops, or memory limits should produce a typed `Incomplete` state when work remains valid and resumable.

Do not collapse:

```text
budget stop -> failure
budget stop -> infeasible
budget stop -> restart everything
```

Instead preserve:

```text
incumbent result
pending obligations
last accepted event
unresolved evidence
remaining candidate set
resume cursor
```

## 5. Preserve pending coverage under compaction

Compaction may discard verbose historical detail only if it retains enough summary state to recover obligations.

A safe compaction record should preserve:

- unfinished operations;
- authority requirements still pending;
- at-most-once submissions whose completion is unknown;
- accepted outputs still referenced by downstream work;
- proof/evidence gaps;
- dependency edges;
- replay keys.

If detailed work is evicted, recomputation is acceptable. Losing knowledge that an obligation exists is not.

## 6. Separate execution identity from conversational identity

A resumed conversation, new model instance, or different agent should be able to continue the same operation graph without inventing a new semantic operation.

```text
semantic operation id != chat turn id
semantic operation id != model session id
semantic operation id != transport connection id
```

This makes 429 recovery and cross-agent handoff much cleaner.

## 7. Failure biopsy dimensions

For each failed or interrupted run, classify the failure separately:

```text
semantic_invalid
unauthorized
capability_missing
resource_exhausted
transport_interrupted
submission_unknown
execution_failed
observation_failed
acceptance_failed
projection_failed
```

This prevents all recovery incidents from being treated as the same "conversation stopped" problem.

## 8. Proposed fault-injection matrix

For one bounded side-effecting workflow, inject interruption after every state transition:

1. before authorization;
2. after authorization, before submission;
3. after submission, before response;
4. after remote completion, before local observation;
5. after observation, before acceptance;
6. after acceptance, before user-facing projection.

Verify that recovery produces no duplicate irreversible side effects and no lost accepted result.

## Working hypothesis

> Robust recovery is primarily a semantic/event-state problem, not a retry problem.

Retries become safe only after the system knows what operation was intended, which transition was evidenced, and whether that transition can be repeated.
