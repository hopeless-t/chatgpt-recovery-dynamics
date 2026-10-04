# NET-429-HYS-001 — Recovery Hysteresis Gate

> Status: FIRST EXECUTABLE OBSERVATION PENDING

The repository has long carried the design rule:

```text
Blocked
  -> first successful observation
  -> Recovering / E
  -> stable confirmation
  -> Healthy / H
```

This experiment turns that rule into an executable state machine without
changing the frozen HTTP 429 scheduler/conformance baselines.

## Separation of responsibility

```text
HTTP 429 Survival Plane scheduler
  answers: when / whether an attempt may happen

Recovery Hysteresis Gate
  answers: how much recovery confidence may be declared
```

The gate does **not** authorize retries or operation replay.

## Motivation

Within the existing sanitized capture:

```text
B -> E -> B : 8 observed
B -> E -> H : 0 observed
```

That supports one narrow rule within this capture:

> one successful observation after Blocked is not sufficient evidence of
> stable recovery.

It does not establish a universal rebound probability or a provider-specific
recovery threshold.

## Parameterized lab policy

The implementation accepts:

- `confirmation_successes_required >= 2`
- `minimum_recovering_duration_s >= 0`

The deterministic first lab fixture uses:

```text
confirmation_successes_required = 2
minimum_recovering_duration_s   = 5
```

Those are **test-fixture values**, not production recommendations.

## Required invariants

1. B + first 2xx -> E, never H.
2. B -> E does not reset accumulated failure history.
3. E + 429 -> B.
4. E -> H requires both configured confirmation count and configured
   recovering duration.
5. Failure history is reset only on E -> H.
6. UNKNOWN operation outcomes remain governed by the existing re-observation
   rule.

## Initial scenario matrix

Eight deterministic cases cover:

- first success remains Recovering;
- immediate rebound;
- count met before stability window;
- count + stability window promotion;
- extra confirmations;
- established Healthy success;
- Healthy -> throttled;
- promotion followed by re-block.

No network requests are made by this experiment.

The first CI run is observation-before-freeze. This document intentionally does
not claim that the executable baseline passes until CI observes it.
