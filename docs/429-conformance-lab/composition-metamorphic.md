# Scheduler × Recovery Confidence Metamorphic Kitten Swarm

> Status: FIRST METAMORPHIC COMPOSITION BASELINE OBSERVED

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

## First observed result

Source:

```text
workflow run   37232843414
job            111525997438
head           1625b2ad2fef148b3e274be9cdb248329c1ed166
artifact       11314722454
```

Observed:

```text
policies                 36
relation families        10
relation checks          360
passed                   360
failed                   0
generated input SHA-256  2e8e834634feaa15a897214cdf720cbf79bd2852856a6f00a278f44cfc4d7365
```

Each relation family contributed exactly 36 checks.

The compact frozen receipt is:

- `data/http_429_recovery_composition_metamorphic_reference.json`

The full ~1 MB relation trace remains a CI artifact rather than becoming a
second canonical raw-data copy in the repository.

## Authority boundary

The test deliberately keeps ownership asymmetric:

```text
scheduler   -> retry authorization, timing floors, budget, identity
hysteresis  -> B / E / H confidence
composition -> may add conservative pacing only
```

Observed across the predeclared grid:

```text
scheduler owns retry authorization       true
hysteresis owns recovery confidence       true
confidence can create replay authority    false
confidence can shorten scheduler floor    false
```

## What 360/360 means

It supports this repository-level statement:

> Generated policy transformations preserved scheduler authority and
> conservative recovery-confidence pacing relations across the predeclared
> 36-policy / 360-relation grid.

It does **not** mean:

- every possible scheduler/confidence composition has been verified;
- these timing fixtures are production recommendations;
- any provider exposes the modeled B/E/H states;
- provider or production behavior has been established;
- a formal protocol certification has been performed.

## Safety / evidence boundary

- deterministic state/control-plane experiment only;
- no network access;
- no production traffic;
- no operation replay authority;
- no provider thresholds are inferred;
- existing frozen COMP-001, HYS-001, HYS-002 and 429 runtime baselines are not rewritten.
