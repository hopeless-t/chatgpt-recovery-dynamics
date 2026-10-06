# Purrtocol C1 Ecology

## Status

`Simulation`, not empirical evidence.

C1 turns the C0 Civilization bootstrap into a bounded evolutionary ecology. The purpose is not to manufacture a predetermined funny mascot. The purpose is to let recovery constraints, projection pressure, resource limits, mutation, migration, and lineage produce inspectable outcomes that can later be projected into graphics and Civilization News.

## Core pipeline

```text
genotype
  -> ecology traits
  -> niche interaction
  -> recovery gate
  -> projection gate
  -> resource gate
  -> selection
  -> mutation / migration
  -> lineage
  -> phenotype descriptor
```

The phenotype descriptor is downstream of simulated history. It is deliberately not a rendered asset yet.

## World laws

1. **Recovery validity comes first.** A highly entertaining organism cannot survive by projection score if it amplifies recovery failure.
2. **Projection is a real selection pressure.** A technically valid organism can still fail to reproduce if it cannot project itself clearly enough for its niche.
3. **Resources are bounded.** Compute, memory, retry pressure, observation, and energy all affect viability.
4. **Lineage is explicit.** Every non-root organism has a parent and a bounded mutation record.
5. **Migration is possible but rare.** A lineage may cross niches and face different pressures.
6. **Generated organism != implemented Purrtocol.** C1 outputs simulation rows and projection descriptors only.
7. **Simulation != Evidence.** Ecology results do not establish claims about real systems, users, adoption, or biological evolution.
8. **NO FINAL BOSS.** No species or civilization is terminal. Stable states are inputs to the next experiment.

## Niches

The initial ecology exposes five deliberately different environments:

- `429-desert` — high failure ambiguity and strong pressure against blind retry amplification.
- `distributed-wetlands` — observation and shared state are comparatively valuable.
- `mobile-dungeon` — intermittent failure pressure rewards cautious re-observation.
- `agent-space` — high ambiguity plus strong observation pressure; `UNKNOWN` must not silently become success.
- `human-square` — lower technical shock but the strongest projection pressure.

These are simulation regimes, not claims that real environments have these exact parameters.

## Genotype, traits, phenotype

C1 keeps three layers separate.

### Genotype

The existing Purrtocol genome supplies symbolic genes such as medium, silhouette, habitat, state cues, temperament, narrative job, and mutation class.

Children inherit the parent genome and mutate one or two genes per birth. This gives lineage continuity instead of independently redrawing every child from a fresh random genome.

### Ecology traits

Each organism also carries bounded continuous traits:

- caution;
- sharing;
- compression;
- novelty;
- efficiency;
- energy.

Traits mutate locally around the parent.

### Phenotype projection

After the organism interacts with its niche, C1 derives a projection descriptor from both genotype and history:

- visual medium;
- silhouette;
- state cue;
- observation prop;
- motion grammar.

This is the bridge to future Graphic Evolution.

The intended future chain is:

```text
ecology history
  -> phenotype descriptor
  -> rig / motion / material / camera grammar
  -> rendered 2D or 3D Pakeya
  -> human reaction observation
  -> later selection research
```

Human reaction must not be hard-coded as the answer. A funny image can become an observation, not an oracle that automatically rewrites evidence.

## Extinction reasons

Every failed organism receives one primary machine-readable reason:

- `recovery-invalid`
- `projection-failed`
- `resource-negative`

The priority is intentional: projection never masks a broken recovery gate.

## Observer effect

Propagation research introduced an important meta-meta problem:

```text
measure propagation
  -> CI validates the measurement system
  -> CI checks out the repository
  -> instrumentation may alter clone telemetry
```

So the observer can affect the observed surface. C1 records this as a modeled boundary rather than pretending the measurement footprint is external ecology.

A future Propagation Observatory should model:

```text
observed activity = external activity + self-instrumentation + unresolved activity
```

without claiming those components are identifiable until evidence supports the split.

## Graphic Evolution direction

The graphical research lane should optimize neither raw polygon count nor raw humor.

Candidate dimensions include:

- recognizability at tiny file sizes;
- motion readability;
- silhouette stability;
- procedural variation;
- rig reuse;
- expressive state cues;
- rendering cost;
- memory and bandwidth footprint;
- replay value;
- comprehension speed;
- surprise without evidence corruption.

A deliberately serious, smooth 3D production can coexist with an absurd organism. Technical quality and comic effect are separate axes.

## Next phases

- **C1.1:** species persistence, diversity pressure, and explicit niche competition.
- **C1.2:** ledger-grounded phenotype manifests suitable for 3D/2D render pipelines.
- **C2 Economics:** exchange, specialization, commons, market, scheduler, and hybrid regimes.
- **C3 Culture:** memes, teaching, norms, cultural inheritance, and faster-than-genetic adaptation.
- **C4 Institutions:** policies, auditors, governance, and counterfactual policy worlds.
- **C5 Civilization News:** deterministic, ledger-grounded projection of events with traceable claims.
