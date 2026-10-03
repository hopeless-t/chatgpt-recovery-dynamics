# Meta Improvement Loop Dashboard

The repository now runs two nested control loops.

```text
INNER / RIL
observe -> biopsy -> change -> verify -> promote -> re-observe

OUTER / MIL
measure loop telemetry -> locate friction -> bounded tuning
-> verify immutable guardrails -> remeasure
```

## Frozen first checkpoint

Four completed RIL cycles:

```text
median total cycle                    631.5 s
median observation -> first change   488.0 s
median last change -> verification    41.5 s
median verification -> promotion      32.5 s
verified-before-promotion ratio         1.0
```

The first triggered signals were:

- `diagnosis_dominates`
- `rework_signal`

## First tuning

**Critic Router v1**

Changed paths are mapped to cheap source-proximate diagnostics before full CI.

This tuning is not yet declared successful.

Promotion criterion for the tuning itself:

- at least 3 post-tuning RIL cycles;
- post-tuning observation -> first-change median below 488 s;
- verified-before-promotion remains 1.0;
- no critical guardrail weakened;
- observer footprint remains under soft warnings.

## Recursion boundary

Automatic controller depth is fixed at two.

The Meta Improvement Loop observes its own footprint instead of automatically spawning a third controller.

**No scalar overall improvement score exists.**
