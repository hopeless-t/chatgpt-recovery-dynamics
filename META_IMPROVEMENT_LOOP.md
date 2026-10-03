# Meta Improvement Loop / 自己改善ループを自己改善する回路

The repository now has two nested control loops.

```text
             ┌────────────────────────────────────────────┐
             │         META LOOP / Loop Tuner            │
             │                                            │
             │ measure inner-loop telemetry               │
             │      ↓                                     │
             │ locate dominant friction                   │
             │      ↓                                     │
             │ propose bounded tuning                     │
             │      ↓                                     │
             │ verify immutable guardrails                │
             │      ↓                                     │
             │ adopt tuning and remeasure                 │
             └─────────────────┬──────────────────────────┘
                               │ tunes
                               v
┌─────────────────────────────────────────────────────────────┐
│ INNER LOOP / Repository Improvement Loop                   │
│ observe → biopsy → change → verify → promote → re-observe │
└─────────────────────────────────────────────────────────────┘
```

## Why this exists

A fast improvement loop can still improve the wrong thing.

Examples:

- deleting CI makes cycle time shorter;
- removing observations makes failure counts fall;
- producing more commits makes throughput look higher;
- generating more Purrtocol concepts makes “cat count” explode without adding real descendants.

Those are classic Goodhart traps.

The meta loop therefore does **not** optimize one scalar score.

## Telemetry

For every completed RIL cycle it measures separately:

- total cycle duration;
- observation → first change;
- last change → verification;
- verification → promotion;
- number of observations;
- number of changes;
- failed observations;
- re-observation after a change;
- whether verification preceded promotion.

Repository observer footprint is measured separately.

## Immutable guardrails

The outer loop cannot tune away:

- evidence boundaries;
- verification-before-promotion;
- historical evidence immutability;
- fail-closed critical invariants;
- UNKNOWN/action-authority separation;
- concept/implementation separation.

## Tuning surfaces

Allowed tuning includes:

- better critic localization;
- better task/context routing;
- cheaper intermediate validation;
- parallel independent checks;
- change-sensitive deep verification **only if the full promotion gate remains intact**;
- smaller reversible artifacts;
- lower observer duplication;
- better frontier scheduling.

## First question

The first meta-loop run intentionally freezes no conclusion.

It asks:

> **Across the recorded RIL cycles, which stage currently dominates wall-clock friction?**

Only after observing the report should the repository choose its first loop-level tuning.

## Anti-Goodhart law

> **Do not make the dashboard happier by making the system less observable.**

No “overall improvement score” is permitted.

Speed is telemetry.

Evidence quality remains a constraint.

## Reproduce

```bash
python scripts/analyze_improvement_loop.py \
  --output /tmp/meta-loop.json
```

The canonical policy is:

`data/meta_improvement_loop_policy.json`
