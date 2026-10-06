# Purrtocol Recovery Policy Lab / 復旧政策実験場

Status: **bounded modeled policy comparison — no final winner**

Connection Amplification showed that recovery work can push a system across a shared-capacity cliff. The Policy Lab asks a second question:

> Which explicit intervention classes restore the capacity gate, and which apparently useful interventions remain insufficient on their own?

It deliberately does **not** assign one scalar intervention cost. Reducing retries, reducing fanout, reducing failure probability, shortening connection hold time, and adding capacity are operationally different actions. Comparing their real cost would require evidence this model does not have.

## Synthetic baseline

The first lab reuses the bounded `small-local-hero` scenario:

```text
baseline request rate = 40 req/s
shared capacity       = 100 concurrent connections
retry depth           = 4
fanout                 = 4 connections / attempt
failure probability   = 0.7
retry multiplier       = 1.5
hold time              = 0.5 s
payload                = 1000 B
local success          = 0.99
```

This baseline reaches about `442.0505` expected concurrent connections and fails the capacity gate.

## Intervention classes

The initial synthetic interventions are deliberately interpretable rather than provider-specific:

- `stop-repeated-checks`: set retry multiplier to 0.
- `fanout-cap-only`: reduce fanout from 4 to 1.
- `reduce-failure-branch`: lower modeled failure probability from 0.7 to 0.1.
- `shorten-hold-time`: lower connection hold time from 0.5 s to 0.1 s.
- `retry-depth-zero`: cap the modeled retry tree at depth 0.
- `capacity-expansion`: increase shared capacity from 100 to 500.

These names describe **model levers**, not a claim that they exactly reproduce the OpenAI 2026-09-29 mitigations.

Expected qualitative result:

```text
stop-repeated-checks     -> safe
fanout-cap-only           -> still unsafe (~110.5 > 100)
reduce-failure-branch     -> safe
shorten-hold-time         -> safe
retry-depth-zero          -> safe
capacity-expansion        -> safe
```

The useful counterexample is `fanout-cap-only`: a substantial local improvement can still miss the global safety boundary.

## Why no winner

A capacity-safe policy is not automatically the cheapest, fastest, fairest, or easiest intervention. The lab therefore returns a **safe set** and an **unsafe set**, not a champion.

Promotion to policy ranking would require a separate measurement contract for intervention cost, risk, service quality, and side effects.

## Evidence boundary

- OpenAI incident existence and cross-product impact: public official observation.
- Detailed incident mechanism: reported public postmortem description tracked separately.
- All values, intervention patches, and outputs in this lab: modeled/synthetic.

## World laws

```text
Capacity gate before local optimization.
Safe set != final winner.
One mitigation may be insufficient.
Different intervention types do not share an invented cost unit.
Modeled policy != provider topology.
Recover. Don't amplify.
```
