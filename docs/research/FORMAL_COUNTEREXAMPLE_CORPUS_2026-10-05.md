# Formal Counterexample Corpus for Recovery Dynamics (2026-10-05)

Source: https://zenn.dev/mizchi/articles/ai-coding-loop-formal

## Why this belongs here

Recovery failures are especially suitable for first-class counterexamples because the interesting object is not a prose description such as "429 happened". The useful object is the exact state/action/observation sequence that produced an unsafe or amplifying recovery path.

## Proposed Counterexample IR

```text
Counterexample {
  invariant
  initial_state
  operation_id
  attempt_sequence[]
  transport_events[]
  retry_decisions[]
  observed_responses[]
  expected_behavior
  actual_behavior
  environment_fingerprint
  evidence_refs[]
  reproducer_ref
}
```

Example invariant classes:

```text
UNKNOWN != retry permission
attempt != operation
transport failure != execution failure
re-observation != re-execution
rate-limit response must not create retry amplification
```

## Failure-to-regression pipeline

```text
HAR / runtime observation
  -> sanitize
  -> normalize event trace
  -> classify invariant violation
  -> Counterexample IR
  -> deterministic or bounded reproducer
  -> regression test
  -> replay on every recovery-policy revision
```

This converts a one-off incident into durable executable memory.

## Claim-scoped verification

A recovery policy should never emit only `PASS`. It should record what was explored.

```json
{
  "claim": "policy does not amplify retries for this trace family",
  "result": "PASS",
  "method": "trace replay / model check / Monte Carlo",
  "scope": {
    "retry_bound": 8,
    "clients": 4,
    "trace_family": "429-ambiguous-outcome"
  },
  "limitations": ["not an unbounded proof"]
}
```

## Candidate research lanes

### CE-001 — historical trace normalization

Convert sanitized historical failure traces into Counterexample IR.

### CE-002 — replay stability

Ensure repeated replay produces the same classified failure/success result under a frozen policy.

### CE-003 — retry-amplification mutation testing

Deliberately mutate backoff/retry rules and verify that the counterexample corpus kills unsafe variants.

### CE-004 — bounded state exploration

Generate combinations of ambiguous outcomes, disconnects, 429s, delayed completion, and re-observation to search for minimal counterexamples.

### CE-005 — evaluator regression

When the failure classifier/evaluator changes, compare old vs new decisions over the frozen corpus and record false accept/false reject deltas.

## Minimal success criterion

A policy revision is not accepted merely because current traces succeed. It must preserve all previously captured invariants and explain any changed verdict on the frozen counterexample corpus.

## Expected payoff

The repository gains a monotonic safety mechanism: each discovered recovery failure can shrink the future reachable failure region by becoming an executable regression guard instead of remaining only an incident narrative.
