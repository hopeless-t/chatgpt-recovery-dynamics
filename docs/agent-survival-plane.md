# Agent Survival Plane: automation irony and degraded-mode handoff

Status: research proposal  
Date: 2026-10-05  
Source trigger: https://type.jp/et/feature/31834/

## Motivation

As AI agents automate more normal-path work, humans may perform less of that work directly while remaining responsible for the hardest abnormal cases. This is a software-agent form of the classic automation irony: the operator is needed most when the automated system is least trustworthy, but may have the least fresh operational context at that moment.

For recovery-oriented systems this suggests a new plane:

```text
Agent Survival Plane
```

Its job is not to make the agent smarter. Its job is to preserve enough evidence, state, and handoff context that work can be safely observed, resumed, degraded, or escalated after agent failure.

## Analogy with Transport Survival

Transport survival already separates logical operation identity from physical attempts:

```text
operation != attempt
transport failure != execution failure
re-observation != re-execution
```

The analogous agent boundaries are:

```text
work objective != agent session
agent failure != task failure
handoff != re-generation
recovery != blind re-execution
```

## Proposed survival state

A durable agent-facing recovery record should minimally include:

- stable operation / task identity;
- last known committed state;
- pending side effects;
- evidence already collected;
- unresolved uncertainty;
- assumptions made by the failed agent;
- verifier results;
- rollback / compensation options;
- next safe observation action;
- explicit STOP / ESCALATE conditions.

## Failure modes

### 1. Context evaporation

An agent disappears and the replacement receives only the original prompt.

Risk: repeated work, repeated side effects, lost uncertainty, and contradictory conclusions.

### 2. False clean restart

A new agent treats an ambiguous prior attempt as if nothing happened.

Risk: duplicate mutation.

### 3. Human cold handoff

A human is asked to resolve the rare hardest failure while receiving a large raw transcript instead of a compressed operational state.

Risk: cognitive overload precisely at the point of highest consequence.

## Recovery law

```text
agent loss
  -> observe durable state
  -> recover evidence ledger
  -> classify execution certainty
  -> resume only from a proven safe boundary
  -> otherwise STOP / ESCALATE
```

`UNKNOWN != permission to regenerate or rerun`.

## Human handoff capsule

A degraded-mode handoff should optimize for situational reconstruction:

```text
objective
current committed state
last safe checkpoint
what changed
what is uncertain
what may already have executed
highest-risk unresolved item
next safe observation
```

This is different from a conversational summary. It is a recovery artifact.

## Candidate simulation

Extend the existing recovery simulations with agent/session failure injection:

1. normal agent performs N steps;
2. inject failure before, during, or after an ambiguous side effect;
3. start a replacement agent with either raw transcript, minimal prompt, or Survival Plane record;
4. measure duplicate execution, recovery latency, lost uncertainty, and human handoff size.

## Hypothesis

A durable Agent Survival Plane should reduce recovery amplification in the same way that observe-first transport recovery reduces request amplification: preserve identity, observe state, and refuse to turn ambiguity into duplicate action.
