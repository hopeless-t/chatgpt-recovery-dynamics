# ADR-0001: Evidence boundaries are first-class

- Status: Accepted
- Date: 2026-10-03

## Context

This repository combines sanitized trace observations, statistical models,
counterfactual accounting, local stress simulations, public-report archaeology,
and recovery design proposals.

Without an explicit boundary, a reader could mistake a compatible mechanism for
an observed production fact.

## Decision

Every important claim must be classifiable as one of:

1. directly observed;
2. recomputed / robustness-checked;
3. strong within-capture model evidence;
4. compatible but unproven causal hypothesis;
5. design proposal;
6. weak external historical evidence;
7. explicitly not established.

The canonical classification is maintained in docs/evidence-ledger.md.

Visualizations must carry the rule:

> **Visualization != Evidence.**

## Consequences

- More writing overhead.
- Less rhetorical freedom.
- Much lower risk of turning client-visible symptoms into claims about OpenAI internals.
- Model competition and falsification become easier because hypotheses are not silently upgraded into facts.
