# Strata v0.1.39 cross-pollination for ChatGPT Recovery Dynamics — 2026-10-05

## Recovery analogy worth testing

Strata does not treat missing fast capacity as binary failure. It selects slower compatible tiers/backends, controls concurrency, and preserves a bounded hot working set. Recovery systems can use the same shape.

## Candidate recovery tiers

```text
HOT   current turn / minimal resume state
WARM  recent checkpoints + tool/result summaries
COLD  full conversation/event history
REMOTE re-fetchable artifacts or external state
```

Budget by serialized bytes/tokens and recovery value, not by message count.

## Strata-derived hypotheses

- A small exact resume set may outperform replaying the whole history after interruption/429.
- Recovery admission should consider resident-state and retry pressure; more concurrent retries can reduce total recovery throughput.
- Interactive turn processing and bulk reconstruction/replay are different phases and may need different policies.
- Degraded lanes should be explicit: smaller context, slower model/route, delayed noncritical work, or read-only recovery can be preferable to total failure.
- Cheap reconstruction/draft workers may propose resume state, but exact checkpoint/evidence verification should decide acceptance.

## Measurements

Track recovery bytes/tokens, replay cost, time-to-first-useful-response, duplicate work, divergence, stale-state use, retry amplification and verified recovery outcome.

## Boundary

A fallback that resumes progress must not widen authority or silently treat missing evidence as recovered state.
