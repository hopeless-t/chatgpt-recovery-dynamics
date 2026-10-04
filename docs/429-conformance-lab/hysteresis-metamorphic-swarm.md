# Recovery Hysteresis Metamorphic Kitten Swarm

> Status: FIRST REPRODUCIBLE BASELINE OBSERVED

NET-429-HYS-001 froze an eight-case executable H/E/B recovery baseline.

NET-429-HYS-002 asks a harder question:

> does the state machine preserve the **relations** behind the design when the
> policy thresholds vary?

The deterministic grid is predeclared as:

```text
confirmation_successes_required ∈ {2, 3, 4}
minimum_recovering_duration_s   ∈ {0, 2, 5, 10}

12 policies × 7 relations = 84 relation checks
```

For every policy the swarm checks:

1. first post-Blocked success enters E;
2. a 429 while E returns to B;
3. exact count+duration boundary promotes to H once;
4. stricter confirmation count cannot promote earlier;
5. stricter duration cannot promote earlier;
6. translating all event times preserves state semantics;
7. later success while already H does not reset failure history again.

The experiment imports the executable Gate and Policy types from NET-429-HYS-001
but derives the expected metamorphic relations independently.

Safety:

- no network access;
- no production traffic;
- no operation replay authority;
- tested thresholds are lab parameters, not provider recommendations.

This page intentionally does **not** claim a pass before the first CI
observation.


## First observed result

The first CI observation passed 84/84 checks. The first run exposed an
observability defect: the swarm report itself was not persisted in the workflow
artifact. The gate result remained green, but a compact reference should be
bound to a reproducible artifact.

The upload surface was repaired without changing any relation or threshold.
The clean reproducible run produced:

```text
first observed workflow      37210948381
reproducible artifact run    37211126462
artifact                     11306097502
policy count                 12
relation checks              84
passed                       84
failed                       0
generated-input SHA-256      b224188bd7a46fcf6f6a49869e2305bdb1cf3e0a4555db36e81a95fde710c913
```

All seven relation families passed for all twelve policies.

Frozen compact receipt:

- `data/http_429_recovery_hysteresis_metamorphic_reference.json`

This strengthens the repository-level hysteresis contract. It does not establish
production thresholds or a provider recovery mechanism.
