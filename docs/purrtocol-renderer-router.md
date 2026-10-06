# Purrtocol Renderer Habitat Router / 生息地ルータ

Status: **constraint router — no hidden degradation**

Renderer Arena answers which strategies are currently non-dominated. Habitat Router answers a
different question:

> Given this environment's hard resource and expression requirements, which Pareto renderers can actually live here?

The router consumes an Arena ledger plus explicit constraints:

```text
max_asset_bytes
min_lineage_expression_coverage
require_pareto_frontier
```

It returns the **set** of feasible renderers. It does not invent a total score or silently choose
one renderer when several satisfy the request.

## Three reference habitats

With the current measured renderer ecology:

```text
Baseline  18,500 B   coverage 0.000
Lean      18,644 B   coverage 0.625
Full      18,904 B   coverage 1.000
```

the same world can expose different feasible sets:

- ultra-tight habitat: `max=18,500`, `min_coverage=0.0` -> Baseline only,
- constrained expressive habitat: `max=18,700`, `min_coverage=0.5` -> Lean only,
- full-expression habitat: `max=19,000`, `min_coverage=1.0` -> Full only.

A request such as `max=18,500` and `min_coverage=1.0` has no valid inhabitant. The correct output
is:

```text
NO_FEASIBLE_RENDERER
```

not an undeclared downgrade.

## Why this matters

Renderer diversity becomes useful only when deployment can exploit it. A single universal
renderer would force every environment to pay the same representation cost. Habitat routing
lets constrained devices, richer clients, and future network conditions occupy different
points on the same verified Pareto ecology.

This connects Purrtocol WORLD to the broader finite-resource rule:

> Do not keep or execute capability that the current habitat cannot justify.

## World laws

```text
No silent requirement relaxation.
No feasible renderer is a valid result.
Feasible set != hidden winner.
Arena gates remain binding.
Human UNKNOWN is not a routing score.
Resource constraint != permission to break semantics.
```

The router does not yet use runtime, network latency, energy, or human-response dimensions.
Those may enter only after their measurement contracts are strong enough to survive their own
counterexamples.
