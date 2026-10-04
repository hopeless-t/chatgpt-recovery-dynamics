# Scheduler × Hysteresis Composed Metamorphic Kitten Swarm

> Status: FIRST OBSERVATION PENDING

NET-429-COMP-001 established one deterministic scheduler × recovery-confidence
composition baseline.

NET-429-COMP-002 expands that into a generated relation surface.

Predeclared policy axes:

```text
confirmation_successes_required ∈ {2, 3}
minimum_recovering_duration_s   ∈ {0, 5}
base_minimum_period_s           ∈ {0.5, 2}
recovery_probe_period_s         ∈ {1, 5}

16 policies × 8 relations = 128 relation checks
```

Relations:

1. first success preserves the composed conservative floor;
2. a 429 decision is independent of prior H/E/B confidence after classification to B;
3. confidence pacing cannot make retry earlier than the bare scheduler;
4. a stronger Retry-After remains authoritative;
5. STOP_BUDGET is orthogonal to confidence;
6. UNKNOWN non-idempotent -> REOBSERVE is orthogonal to confidence;
7. pacing relaxes to base cadence only after Healthy promotion;
8. a stricter recovery-probe period cannot make the next observation earlier.

Safety:

- no network access;
- no production traffic;
- no operation replay authority.

The generated grid tests repository control semantics only. It does not establish
provider thresholds, provider internals, or production recommendations.

The first CI result is intentionally not predeclared.
