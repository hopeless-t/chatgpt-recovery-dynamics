# Critic Router / Source-Proximate Preflight

The first Meta Improvement Loop observation found:

```text
median observation -> first change: 488.0 s
median last change -> verification: 41.5 s
median verification -> promotion: 32.5 s
```

So the first tuning target is **diagnosis/localization**, not weaker verification.

The Critic Router maps changed paths to the cheapest relevant preflight checks.

## Examples

3D artifact:

```bash
python scripts/preflight_router.py \
  --path docs/assets/purrtocol/purrtocol.glb
```

429 recovery:

```bash
python scripts/preflight_router.py \
  --path scripts/http_429_survival.py \
  --run
```

A branch diff:

```bash
python scripts/preflight_router.py \
  --diff-base origin/main \
  --run
```

## Important semantics

Preflight is intentionally **not** a merge gate replacement.

```text
source-proximate preflight
        ↓
cheap early failure
        ↓
smaller biopsy radius
        ↓
full CI promotion gate still required
```

The Repository Observatory is always included because apparently unrelated
changes can still create cross-surface drift.

## Why this is a loop-level tuning

RIL-001 required two changes because the first repaired binary then exposed a
stale hash contract.

That failure was valuable, but the meta signal says cheaper checks closer to the
changed source can reduce the cost of discovering the next layer.

The goal is not “zero failures.”

The goal is:

> **find informative failures earlier, closer to the source, without making the final gate weaker.**
