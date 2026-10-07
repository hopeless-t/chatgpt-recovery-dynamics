# Purrtocol Genesis Microcosm

> 生命が生まれる前から、歴史は始まっている。

This layer starts before the first Purrtocol exists. It adds a bounded pre-life substrate, explicit resource circulation, environment-conditioned founder expression, and traceable micro-fluctuation amplification.

## Imported structural ideas from Market Microcosm

The design intentionally reuses four ideas already explored in `hopeless-t/market-microcosm-lab`:

1. **Closed internal circulation.** Internal transfers conserve stock; external sources and sinks are declared.
2. **Usage is not the only allocator.** The common pool is split across usage, a survival floor, and an ecosystem diversity fund.
3. **Viability precedes optimization.** A locally efficient allocation is not considered good if it destroys the ecosystem.
4. **Randomness is declared and bounded.** Noise perturbs state; it does not directly choose outcomes.

The current Genesis allocation is intentionally simple:

```text
commons
  -> 50% usage
  -> 30% survival floor
  -> 20% ecosystem diversity fund
```

This is a synthetic game/research mechanism, not a claim that real ecosystems or economies should use those exact weights.

## Before Purrtocol

The world begins with three resource fields:

- `energy`
- `signal`
- `shelter`

Each period has explicit external inflow and explicit abiotic loss. When the substrate crosses the bounded emergence threshold, four founders materialize by moving existing environmental stock into organism reserves. No resource is created by the birth event.

## Same traits, different expression

Every Purrtocol uses the same trait vocabulary:

```text
caution
sharing
compression
novelty
```

The vocabulary is invariant. Initial expression is plastic and depends on the world that exists before life emerges.

Reference sanity checks currently yield:

- high hazard -> `caution`
- high connectivity -> `sharing`
- sparse + volatile resources -> `compression`
- heterogeneous resources -> `novelty`

This means the game can start with the same species grammar while producing different founding Purrtocols from different planets/habitats.

## Fluctuation contract

Replayability needs variation without opaque dice deciding history.

The simulator therefore uses counter-based deterministic micro-randomness with separate namespaces for:

- environmental noise;
- founder-expression jitter;
- mutation.

The environment noise for a given seed/period/channel does not change merely because one branch produced more children.

Outcomes such as niche dominance, extinction, institutions, or later revolution are never direct random draws. They must arise through state transitions.

## Reference twin experiment

Two worlds are run with:

- the same macro environment;
- the same seed (`467`);
- the same exogenous noise schedule;
- the same trait vocabulary;
- the same simulation rules.

The only intervention is `+0.005` signal inflow in one early period. Baseline signal inflow is `1.9`, so the intervention is about **0.263%** of one period's normal signal flow.

After 80 periods the current reference fixture separates into:

```text
baseline twin   caution 9 / sharing 8
perturbed twin  caution 7 / sharing 10
```

The ecosystem-fund target differs across **39 allocation periods**.

The interpretation is deliberately narrow: this proves path-dependent divergence inside this synthetic model. It is not a proof of mathematical chaos and not evidence about real biology, markets, or politics.

## Same macro world, many histories

Using the same macro environment with seeds `410..421`, the current reference suite produces **11 distinct final signatures** across 12 worlds and both `caution`- and `sharing`-dominant outcomes.

The intended chain is:

```text
micro fluctuation
  -> resource/reserve difference
  -> threshold crossing
  -> survival/reproduction difference
  -> commons allocation difference
  -> niche composition difference
  -> future allocation difference
  -> larger historical divergence
```

This is the replayability mechanism.

## Bridge into Civilization

Genesis is upstream of the existing layers:

```text
PRE_LIFE substrate
  -> LIFE_EMERGED
  -> founder expression
  -> ecological/resource history
  -> C1 evolutionary ecology
  -> economic / institutional circulation
  -> C2 knowledge institutions
  -> civilization history
```

A future game build should not spawn a generic mascot and then assign a biome. The biome should help produce the first Purrtocol phenotype, and that founding history should remain visible in descendants, culture, policy, graphics, and museum records.

## World laws

- Internal transfers must conserve stock.
- External sources and sinks must be explicit.
- Usage allocation is not the only allocation.
- Survival floors may protect long-run diversity at short-run efficiency cost.
- Same trait vocabulary != same expression.
- Same macro conditions != identical history.
- Same seed + same rules = replayable world.
- Tiny fluctuation may change history, but outcome RNG is forbidden.
- Path-dependent divergence != proof of real-world chaos.
- Simulation != Evidence.
- NO FINAL CIVILIZATION.
