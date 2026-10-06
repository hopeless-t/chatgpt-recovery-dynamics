# Purrtocol Expressed Second Light

Status: **experimental implemented visualization — non-canonical**

This lane closes the first full loop from simulated ecology into an actual 3D descendant:

```text
C1 Ecology
  -> Graphic Evolution
  -> Expression Genome
  -> Expressed Second Light GLB
```

The stable Second Light generator remains unchanged. `scripts/render_purrtocol_expression.py`
starts from that deterministic baseline and applies one breeding-eligible expression genome.

## What can now be expressed

The v0 renderer maps bounded genome fields into actual GLB structure and animation data:

- body and head roundness -> node scale,
- niche-derived ear asymmetry -> left/right ear scale and pose,
- tail arc -> tail pose and length,
- surface roughness bias -> material roughness,
- breath amplitude -> body/head translation tracks,
- step amplitude -> provisional movement tracks,
- timing scale -> animation input clocks,
- tail secondary motion -> tail rotation tracks.

This is deliberately a small phenotype surface. More parameters are not automatically
better: each added degree of freedom must remain deterministic, bounded, semantically
compatible, and inspectable.

## Fail-closed breeding rule

Only genomes satisfying all of these conditions may produce a living rendered descendant:

```text
survives == true
breeding_eligible == true
implementation_target == purrtocol-second-light-generator/v0
canonical == false
human_reaction == UNKNOWN
```

Extinct genomes are rejected by the renderer. Museum visualization is a separate future
lane so memorial specimens cannot silently re-enter the breeding population.

## Reproducibility

For the same expression genome, CI requires byte-identical GLB and receipt output.
CI also renders two distinct genomes and requires different GLBs. A variant must therefore
be both reproducible within lineage and distinguishable across lineage.

The first expressed litter is uploaded as a GitHub Actions artifact.

## Evidence boundary

The renderer writes lineage and expression metadata into `asset.extras`, but none of it is
empirical evidence about humans:

```text
Simulation != Evidence
Visualization != Evidence
Generated variant != Canon
UNKNOWN != SUCCESS
Technical quality != humor
Extinct != breeding eligible
```

A technically distinct cat is not automatically a good cat. Human comprehension, humor,
replay value, and propagation remain `UNKNOWN` until separately observed.

## Meta-meta lesson

The important transition is not "make the mascot prettier." It is:

> ecological history can now leave a deterministic, auditable physical trace in a 3D organism.

That makes future renderer competition possible: multiple renderers can receive the same
Expression Genome and compete on size, semantic fidelity, runtime cost, visual legibility,
and eventually observed human response without rewriting upstream history.
