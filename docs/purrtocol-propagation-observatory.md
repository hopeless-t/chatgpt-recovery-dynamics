# Purrtocol Propagation Observatory

## Purpose

Purrtocol propagation is not equivalent to stars, forks, page views, or any single GitHub metric.

The observatory studies how Recovery Dynamics ideas move through software ecosystems while preserving the boundary between observed evidence and speculative lineage.

The core question is:

> If the Purrtocol name disappears, how many generations later does the recovery DNA remain?

## Evidence boundary

GitHub Traffic data is owner-visible operational telemetry. Exact traffic snapshots SHOULD remain local/private by default and MUST NOT be published merely because a derived analysis is useful.

The repository may publish schemas, methods, synthetic examples, and aggregate classifications without publishing a private traffic snapshot.

Labels:

- `Observed`: directly measured public or owner-visible data.
- `Derived`: arithmetic or deterministic transformation of observed data.
- `Hypothesis`: causal explanation not yet demonstrated.
- `Unknown`: unresolved attribution.

`Clone != human adopter`.

`Unique cloner != verified unique person`.

`Propagation != popularity`.

## Propagation stages

A candidate propagation path is:

`discovery -> full clone -> local run -> semantic adoption -> independent implementation -> variant -> cultural mutation`

Each transition requires stronger evidence than the previous one. A clone can establish possession of repository state, but it cannot establish comprehension, execution, adoption, or descent.

## Species classification

External observations may be classified as:

1. **Direct descendant** — explicit repository, code, attribution, or lineage link.
2. **Semantic descendant** — distinctive Recovery Survival Contract ideas persist while names or code have changed.
3. **Convergent species** — independently evolved similar recovery behavior with no demonstrated lineage.
4. **False positive** — superficial vocabulary overlap without shared mechanism.
5. **UNKNOWN** — insufficient evidence.

No automated detector may promote `UNKNOWN` to descendant without evidence.

## Traffic-shape signals

The companion analyzer intentionally emits signals rather than causal verdicts.

Useful dimensions include:

- clones per unique cloner;
- unique-cloner to unique-visitor ratio;
- clone to page-view ratio;
- temporal concentration;
- visible forks, stars, PRs, and public references;
- public lineage observations.

A clone-heavy / view-light shape can be consistent with direct Git access, CI, agents, scanners, mirrors, or other automation. It does **not** identify which cause is responsible.

### Self-generated CI is a first-class confounder

This repository contains many GitHub Actions jobs that perform `actions/checkout`. A high clone count therefore cannot be interpreted as external propagation until the observatory estimates a plausible self-generated CI baseline.

The attribution ladder is:

`raw clone traffic -> subtract/estimate self-CI envelope -> unresolved clone residual -> public lineage search -> descendant evidence`

The self-CI envelope is itself uncertain. The observatory MUST keep lower/upper bounds when GitHub does not expose enough information to attribute individual clone events.

A residual clone wave is still not a human count or descendant count.

## Anti-Goodhart rules

Never optimize the world for raw:

- clones;
- stars;
- forks;
- page views;
- cat count;
- commits;
- generated variants.

A successful propagation event is one where useful recovery behavior survives transmission without evidence corruption.

## WORLD integration

The observatory can project validated propagation events into Purrtocol WORLD as ecology events.

Examples:

- a verified direct descendant becomes an introduced species;
- a convergent implementation becomes an independently evolved wild species;
- a large unattributed clone wave becomes a migration anomaly, not a population count;
- a semantic descendant preserving recovery invariants becomes a cultural transmission event.

Projection may be entertaining, but `Visualization != Evidence`.

## Next experiments

1. Persist private traffic snapshots outside the public repository.
2. Derive privacy-preserving shape metrics.
3. Estimate a self-generated CI clone envelope from workflow runs and checkout-bearing jobs.
4. Compare the residual traffic shape with visible web traffic.
5. Search public code for distinctive invariant combinations rather than mascot names alone.
6. Compare direct descendants against convergent species.
7. Estimate how many transformations Recovery DNA can survive before attribution disappears.
