# Purrtocol Graphic Evolution

Status: **C1.2 projection bridge / render-plan only**

## Why this exists

Purrtocol graphics should not evolve by drawing a funny cat first and inventing a backstory afterward.

The intended direction is:

```text
C1 ecology history
  -> phenotype descriptor
  -> graphic manifest
  -> rig / motion / material / camera / lighting
  -> rendered artifact
  -> actual human observation
  -> later selection research
```

The history comes first. The appearance is a projection of that history.

## Existing First Light is the semantic ancestor

The current 3D contract remains authoritative for recovery semantics. First Light is intentionally tiny and is not final character art. The graphic-evolution bridge reuses its required semantic nodes and animations rather than inventing an incompatible second mascot pipeline.

The manifest reads `data/purrtocol_3d_contract.json` and records the measured First Light baseline from that contract. Those measurements remain observations of the implemented First Light asset; they are not automatically budgets or claims about future renders.

## The midnight-commercial oracle

One presentation regime is named:

`serious-midnight-commercial`

Its governing rule is:

> Play the production completely straight. The subject is allowed to be absurd; the filmmaking does not wink at the audience.

This regime is a **projection candidate**, not an empirical claim that it is always funnier, clearer, or more memorable. Human reaction remains `UNKNOWN` until observed.

The desired contrast is intentionally two-axis:

- technical production quality can rise;
- absurdity can emerge from the organism and its history.

`technical quality != humor`

A smoother rig, cleaner light, richer material, or more cinematic camera is not itself evidence of better comedy or better communication.

## Manifest structure

Each selected C1 organism receives a deterministic profile containing:

- organism/species/parent/generation provenance;
- niche and survival/extinction state;
- the C1 phenotype descriptor;
- a First-Light-compatible rig intent;
- semantic animation and node contracts;
- motion grammar;
- camera grammar;
- lighting grammar;
- material grammar;
- presentation regime;
- explicit `human_reaction: UNKNOWN`;
- an explicit no-auto-promotion gate.

The bridge may also select extinction exemplars when final survivors are sparse. Those profiles are memorial projections and remain marked as non-survivors.

## Candidate presentation regimes

### serious-midnight-commercial

High technical fidelity, high deadpan seriousness, deliberately sincere broadcast grammar. Suitable when simulated novelty/projection traits cross the current heuristic threshold.

### deadpan-public-information-film

A public-information-film grammar for organisms from the human-facing niche that did not enter the commercial regime.

### clinical-recovery-demo

Neutral instrumentation-forward rendering for recovery semantics.

### museum-extinction-memorial

A historical projection for failed lineages. Extinction is not silently rewritten as survival because an image looks good.

## Graphic dimensions worth researching

The WORLD can later explore, measure, or constrain:

- silhouette recognizability;
- rig reuse and deformation quality;
- motion readability;
- semantic state readability without color alone;
- procedural variation;
- asset bytes and memory footprint;
- draw calls / triangle count / texture footprint;
- frame-time on modest hardware;
- camera rhythm;
- loop seamlessness;
- material richness;
- expression bandwidth;
- loading latency;
- comprehension speed;
- human surprise;
- human replay value.

The last three require real observation; they must not be hallucinated by the generator.

## Smooth 3D path

The First Light asset proved the semantic/runtime path with six named animations. The next graphics frontier is not simply “more polygons”. A useful staged path is:

```text
First Light semantic rig
  -> ecology-derived manifest
  -> reusable expressive rig
  -> procedural body/silhouette parameters
  -> smoother locomotion and secondary motion
  -> serious camera/light grammar
  -> measured runtime budgets
  -> observed human response
```

Secondary motion candidates include ears, tail, goggles, carried packet/snapshot props, and later fur-like or soft-body cues when the runtime budget supports them. They should remain semantically subordinate to recovery-state readability.

## Evidence and promotion boundary

A render plan is not an asset.
A render is not evidence.
A funny image is not a recovery result.
A high-quality animation is not proof of comprehension.
A generated variant is not automatically canon.

Promotion still requires an implemented asset, runtime validation, provenance, and an explicit promotion event under the 3D contract.

## Meta-meta production rule

Graphic-evolution changes should prefer atomic multi-file Git commits where practical. The repository's CI uses checkout extensively, and one-file-at-a-time commits can increase the measurement footprint of the very traffic observatory studying repository propagation.

The production system should therefore optimize both the artifact and the observation cost of producing it.
