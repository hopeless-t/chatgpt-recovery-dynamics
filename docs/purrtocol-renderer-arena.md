# Purrtocol Renderer Arena / レンダラ競技場

Status: **engineering-observation harness — no automatic winner**

Renderer Arena separates **survival gates** from **optimization**.

A tiny, fast, or flashy renderer does not earn survival if it breaks recovery semantics,
provenance, extinction handling, determinism, or evidence boundaries. Only entrants that pass
those gates are compared on a Pareto frontier.

## Why there is no total score

A scalar score encourages Goodhart failure. For example, minimizing bytes alone rewards an
empty or semantically broken asset. Maximizing visible motion alone rewards noisy animation.
Maximizing human attention before observation invents evidence.

Arena v0 therefore uses hard gates first, then only two stable engineering objectives:

```text
asset_bytes                   -> minimize
lineage_expression_coverage   -> maximize
```

Semantic contract coverage must already be `1.0` to enter the frontier.

The first measured comparison is intentionally simple:

- `second-light-baseline/v0`: smaller stable control, zero lineage-expression coverage,
- `expressed-second-light/v0`: slightly larger, but physically expresses an Expression Genome.

Neither dominates the other: the baseline occupies a compactness niche, while the expressed
renderer occupies a lineage-expression niche.

## Runtime is diagnostic in v0

Hosted CI timing varies with runner generation, region, cache state, load, and platform noise.
Runtime samples may be recorded, but Arena v0 refuses to treat them as a stable Pareto objective.
A later bounded benchmark harness can promote runtime only after its measurement contract is
strong enough.

## Human response is outside automated fitness

These remain excluded from automated renderer selection until observed:

```text
human_reaction
humor
comprehension
replay_value
```

`UNKNOWN` is not converted to zero, neutral, or average. It stays unknown.

## Anti-Goodhart counterexamples

CI injects a synthetic one-byte `tiny-liar` renderer. It loses before optimization because it
breaks semantic, extinction, and provenance gates. CI also injects a valid but bloated renderer
with the same lineage-expression coverage as the expressed renderer; the smaller expressed
renderer Pareto-dominates it.

These are test-only counterexamples, not observed external species.

## Arena laws

```text
Hard gates before optimization.
Invalid cannot win by being small.
No single scalar score.
Pareto frontier != final champion.
Human UNKNOWN != zero.
Runtime sample != stable benchmark.
Metadata difference != Physical difference.
No automatic canonical promotion.
```

## Next evolution

Arena v0 makes renderer competition possible without inventing a winner. Future real renderer
strategies can occupy different niches, for example:

- ultra-light semantic renderer,
- richer motion renderer,
- mobile-budget renderer,
- projection-first renderer,
- accessibility / high-legibility renderer.

A new axis should enter optimization only after it has a bounded measurement contract and a
counterexample showing how that metric can be gamed.
