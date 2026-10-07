# Purrtocol Civilization — Shock Regimes

> The same policy can survive in one environment and fail in another.

This surface connects the bounded Recovery Safety Frontier to Purrtocol Civilization. It does **not** simulate real politics, real provider topology, or real remediation costs. It asks a narrower modeled question:

**When the environment changes, does the same finite policy vocabulary remain sufficient?**

## Frontier phases

Each environment receives one of four phase labels:

- `NO_INTERVENTION_REQUIRED` — the modeled baseline is already within capacity.
- `SINGLE_LEVER_SUFFICIENT` — at least one inclusion-minimal safe package has size 1.
- `COALITION_REQUIRED` — the baseline is unsafe and every inclusion-minimal safe package requires multiple levers.
- `FRONTIER_EMPTY_WITHIN_BOUND` — no safe package exists inside the explicitly enumerated package-size bound.

The last label is intentionally narrow. It does **not** mean that no remediation exists. It means only that the current finite lever vocabulary and package-size bound did not produce one.

## Phase-transition counterexample

The validation fixture keeps the policy vocabulary fixed and changes only the environment.

Base recovery policy:

- fanout connections per attempt: `4`
- failure probability: `0.7`
- retry multiplier: `1.5`
- connection hold: `0.5 s`
- retry depth: `4`

Available levers:

1. `fanout-cap`: fanout `4 -> 1`
2. `hold-time-cap`: hold time `0.5 -> 0.4`
3. `retry-depth-two`: retry depth `4 -> 2`
4. `retry-multiplier-cap`: retry multiplier `1.5 -> 1.0`

Only packages of size `<= 2` are considered.

### Calm habitat

- request rate: `10 rps`
- shared connection capacity: `100`
- modeled baseline: `110.512625` connections — unsafe
- each of the four singleton levers is individually safe
- phase: `SINGLE_LEVER_SUFFICIENT`

The civilization can survive without a coalition.

### Congested habitat

- request rate: `40 rps`
- shared connection capacity: `100`
- modeled baseline: `442.0505` connections — unsafe
- all four singleton levers are unsafe
- three inclusion-minimal safe coalitions remain:
  - `fanout-cap + hold-time-cap` -> `88.4101`
  - `fanout-cap + retry-depth-two` -> `63.05`
  - `fanout-cap + retry-multiplier-cap` -> `55.462`
- phase: `COALITION_REQUIRED`

A policy that could govern alone in the calm habitat can no longer govern alone under congestion.

### Severe habitat

- request rate: `80 rps`
- shared connection capacity: `80`
- modeled baseline: `884.101` connections — unsafe
- every singleton is unsafe
- every size-2 package is also unsafe
- best connection count among the three former coalitions is still `110.924`, above capacity `80`
- phase: `FRONTIER_EMPTY_WITHIN_BOUND`

The correct modeled conclusion is **not** “civilization is impossible.” It is:

> the current policy vocabulary is insufficient inside the current search bound.

The next response may require a new lever, a larger package, a capacity change, a workload change, or a different architecture.

## Institutional phase change

The deterministic fixture therefore produces:

```text
SINGLE_LEVER_SUFFICIENT
        ↓
COALITION_REQUIRED
        ↓
FRONTIER_EMPTY_WITHIN_BOUND
```

This is the first Purrtocol Civilization mechanism where the environment changes the *institutional structure* required for survival rather than merely changing a score.

## World laws

1. **Policy viability is environment-dependent.**
2. **A singleton can become coalition-only.**
3. **A bounded safety frontier can disappear under stronger shock.**
4. **Frontier empty within bound != global impossibility.**
5. **Safe package != universal winner.**
6. **Inclusion-minimal != cheapest.**
7. **Heterogeneous costs remain unscalarized.**
8. **Modeled regime != provider topology.**
9. **Recover. Don't amplify.**

## Evidence boundary

All values above come from the repository's finite connection-amplification model. They are deterministic modeled outputs used to exercise recovery reasoning. They are not empirical measurements of OpenAI, GitHub, Cloudflare, or any other production system.

The purpose is to make one failure mode visible:

> choosing a policy once and treating it as permanently optimal is itself a recovery bug.
