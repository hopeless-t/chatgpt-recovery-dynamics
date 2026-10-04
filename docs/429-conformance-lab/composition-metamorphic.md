# Scheduler × Recovery Confidence Metamorphic Kitten Swarm

> Status: FIRST OBSERVATION PENDING

`NET-429-COMP-002` extends the frozen eight-case scheduler/hysteresis composition
baseline into generated **relations**, not merely more point fixtures.

## Policy grid

```text
confirmation_successes_required ∈ {2, 3, 4}
minimum_recovering_duration_s   ∈ {0, 5}
base_minimum_period_s           ∈ {0.5, 1.0}
recovery_probe_period_s         ∈ {1, 5, 10}

36 composition policies
10 relations per policy
360 relation checks total
```

## Predeclared relations

1. Blocked confidence cannot make retry earlier than the bare scheduler.
2. Recovering confidence cannot make retry earlier than the bare scheduler.
3. A stronger `Retry-After` remains authoritative.
4. Confidence cannot override `STOP_BUDGET`.
5. Confidence cannot override ambiguous non-idempotent `REOBSERVE`.
6. Translating the whole scheduler clock preserves composition semantics.
7. A stronger recovery-probe floor cannot make retry earlier.
8. A stronger base scheduler floor cannot make retry earlier.
9. Recovery pacing relaxes only when the confidence gate actually reaches H.
10. A stricter confidence threshold cannot relax pacing earlier.

## Authority boundary

The test deliberately keeps ownership asymmetric:

```text
scheduler   -> retry authorization, timing floors, budget, identity
hysteresis  -> B / E / H confidence
composition -> may add conservative pacing only
```

Confidence must never mint replay authority.

## Safety / evidence boundary

- deterministic state/control-plane experiment only;
- no network access;
- no production traffic;
- no provider thresholds are inferred;
- tested timing values are fixtures, not recommendations;
- existing frozen COMP-001, HYS-001, HYS-002 and 429 runtime baselines are not rewritten.

The first CI run is observation-before-freeze. This document intentionally does
not claim `360/360` before CI observes the generated relation surface.
