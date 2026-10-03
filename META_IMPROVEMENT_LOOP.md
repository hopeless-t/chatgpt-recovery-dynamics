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

## First observed checkpoint

The first Meta Improvement Loop run observed four completed RIL cycles:

```text
completed cycles                         4
median total cycle duration             631.5 s
median observation -> first change      488.0 s
median last change -> verification       41.5 s
median verification -> promotion         32.5 s
verified-before-promotion ratio           1.0
cycles with multiple changes              0.25
GitHub workflows                            11
observatory Python footprint            29,332 bytes
```

Two tuning signals fired:

```text
diagnosis_dominates
rework_signal
```

The important asymmetry is:

```text
488 s diagnosis/localization
vs
74 s median downstream verification+promotion
```

So the first tuning is **not** “make CI weaker/faster.”

It is:

> **make the first useful diagnosis arrive closer to the changed source.**

## First tuning — Critic Router v1

The repository now has:

- `data/preflight_routes.json`
- `scripts/preflight_router.py`
- `docs/repository-observatory/critic-router.md`

Changed paths are routed to the cheapest relevant local diagnostic before full CI.

Examples:

```text
GLB change
  -> validate_purrtocol_3d.py
  -> full 3D promotion gate still required

429 scheduler change
  -> validate_http_429_survival.py
  -> full 429 + observatory + public gates still required

meta-loop change
  -> analyze_improvement_loop.py
  -> full Meta Improvement Loop gate still required
```

Repository Observatory is always included.

### Evaluation gate

Critic Router v1 is **not yet declared successful** merely because it exists.

After at least three new RIL cycles, compare the post-tuning
observation-to-first-change median with the frozen baseline:

```text
baseline = 488.0 s
```

Success additionally requires:

- verification-before-promotion remains 1.0;
- no critical guardrail is weakened;
- observer footprint remains under soft design warnings.

One fast cycle is not evidence that the loop improved.

## Bounded recursion

Automatic control depth is fixed at two levels:

```text
1. Repository Improvement Loop
2. Meta Improvement Loop
```

The meta loop observes its own footprint instead of automatically creating a
third controller.

No automatic turtles all the way down.

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
