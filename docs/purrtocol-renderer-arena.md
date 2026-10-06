# Purrtocol Renderer Arena / レンダラ競技場

Status: **engineering-observation harness — no automatic winner**

Renderer Arena separates **survival gates** from **optimization**.

A tiny, fast, or flashy renderer does not earn survival if it breaks recovery semantics,
provenance, extinction handling, determinism, or evidence boundaries. Only entrants that pass
those gates are compared on a Pareto frontier.

## Why there is no total score

A scalar score encourages Goodhart failure. Minimizing bytes alone rewards an empty or
semantically broken asset. Maximizing motion alone rewards noise. Maximizing attention before
human observation invents evidence.

Arena v0 therefore uses hard gates first, then two bounded engineering objectives:

```text
asset_bytes                   -> minimize
lineage_expression_coverage   -> maximize
```

Semantic contract coverage must already be `1.0` to enter the frontier.

## First real renderer ecology

The initial arena had a stable Second Light control and one full expression renderer. The first
renderer-diversification step adds a third real implementation:

- `second-light-baseline/v0` — stable control, zero lineage-expression coverage,
- `lean-expressed-second-light/v0` — deliberately realizes 5/8 expression axes (`0.625`),
- `expressed-second-light/v0` — realizes all 8/8 current expression axes (`1.0`).

The expected ecology is not a podium. If representation cost rises monotonically with expression
coverage, all three can remain on the Pareto frontier as distinct niches.

A renderer may leave the frontier later when another implementation becomes no worse on both
cost and expression coverage and strictly better on at least one.

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
with the same lineage-expression coverage as the full renderer; the smaller full renderer
Pareto-dominates it.

These are test-only counterexamples, not observed external species.

## Arena laws

```text
Hard gates before optimization.
Invalid cannot win by being small.
No single scalar score.
Pareto frontier != final champion.
Partial expression must be declared.
Human UNKNOWN != zero.
Runtime sample != stable benchmark.
Metadata difference != Physical difference.
No automatic canonical promotion.
```

## Next evolution

Renderer Arena can now accept genuinely different strategies rather than only a baseline and a
single implementation. Future niches may include:

- ultra-light semantic renderer,
- richer secondary-motion renderer,
- mobile-budget renderer,
- projection-first renderer,
- accessibility / high-legibility renderer.

A new axis enters optimization only after it has a bounded measurement contract and a
counterexample showing how that metric can be gamed.
