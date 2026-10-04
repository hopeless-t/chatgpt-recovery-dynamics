# Scheduler × Recovery Hysteresis Composition

> Status: FIRST BASELINE OBSERVED

NET-429-COMP-001 composes two control planes that remain separately owned:

```text
Scheduler
  -> retry authorization
  -> Retry-After / start-to-start timing floors
  -> bounded budget

Recovery Hysteresis
  -> B / E / H confidence
  -> failure-history reset only on stable E -> H

Composition
  -> may add a conservative pacing floor while B/E
  -> may not create replay authority
  -> may not override STOP_BUDGET
  -> may not override REOBSERVE
  -> may not shorten a scheduler floor
```

The first deterministic lab predeclares eight checks:

1. first success enters E and preserves a slow recovery-observation floor;
2. E + 429 returns B without shortening the start anchor;
3. confidence pacing is monotone-conservative relative to the bare scheduler;
4. a stronger Retry-After remains authoritative;
5. confidence cannot override STOP_BUDGET;
6. confidence cannot override UNKNOWN non-idempotent -> REOBSERVE;
7. failure history clears only on E -> H;
8. pacing relaxation occurs only after H, not on the first success.

Fixture policy:

```text
confirmation successes    2
recovering duration       5 s
base minimum period       1 s
recovery probe period     5 s
```

These are deterministic test values, not production recommendations.

Safety:

- no network access;
- no production traffic;
- no operation replay authority.

The source intentionally does not claim a pass before CI observes the first run.


## First observed result

Source:

```text
workflow   37211808310
job        111464340871
head       97a0cc3eaca479ddf072733bc5283a604f28848e
artifact   11306778418
```

Observed:

```text
scenarios                         8
passed                            8
failed                            0
scheduler owns retry authority    true
hysteresis owns confidence        true
confidence can create replay      false
confidence can shorten floor      false
network access                    false
production traffic                false
```

The first composition baseline therefore supports a narrow repository claim:

> recovery confidence may make pacing more conservative while B/E, but it does
> not own replay authorization, budget stops, or server timing floors.

Frozen compact receipt:

- `data/http_429_recovery_composition_reference.json`

Fixture periods remain test values only.
