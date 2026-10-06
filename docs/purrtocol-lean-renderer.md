# Purrtocol Lean Expression Renderer

Status: **experimental implemented renderer strategy — non-canonical**

The Lean Expression Renderer is the first real alternative strategy in Renderer Arena.
It reads the same `purrtocol-expression-genome/v0` input as the full Expressed Second Light
renderer, but deliberately materializes only part of that genome.

## Declared expression budget

Lean v0 realizes five of eight current physical expression axes:

```text
body_roundness
head_roundness
ear_asymmetry
tail_arc
roughness_bias
```

It deliberately omits:

```text
breath_amplitude
step_amplitude
timing_scale
```

Therefore:

```text
lineage_expression_coverage = 5 / 8 = 0.625
```

This is not described as "almost full" or hidden behind a quality score. Partial expression is
part of the public receipt and Renderer Arena input.

## What Lean keeps

Lean preserves:

- all required semantic nodes,
- all six Recovery Dynamics animation clips,
- zero textures,
- deterministic output,
- fail-closed rejection of extinct / non-breeding genomes,
- static-to-animation continuity for body scale, ear pose, and tail pose,
- a physical fingerprint with lineage metadata removed,
- minimum in-asset binding to `expression_id` and `expression_signature`.

Richer source provenance remains in the receipt instead of being duplicated into the GLB.

## Why this renderer exists

The full renderer is not assumed to be optimal merely because it expresses more axes. Lean asks:

> How much lineage can survive when representation cost is deliberately constrained?

This gives Renderer Arena a real trade-off rather than a synthetic comparison:

```text
Second Light baseline  -> minimum expression / minimum representation cost
Lean renderer          -> partial expression / intermediate cost
Full renderer          -> full current expression / higher cost
```

If all three survive the Pareto frontier, that is not a failure to choose a winner. It means the
world currently contains three viable rendering niches.

## World laws

```text
Partial expression must be declared.
Omitted behavior != failed behavior.
Smaller != automatically better.
More expression != automatically better.
UNKNOWN human response stays UNKNOWN.
Simulation != Evidence.
Visualization != Evidence.
Generated variant != Canon.
```
