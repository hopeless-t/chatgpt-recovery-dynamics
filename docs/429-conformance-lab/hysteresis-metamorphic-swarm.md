# Recovery Hysteresis Metamorphic Kitten Swarm

> Status: FIRST OBSERVATION PENDING

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
