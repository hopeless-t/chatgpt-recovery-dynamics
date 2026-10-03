# Repository Improvement Loop

This repository now treats its own development process as a control problem.

> **Observe the repository. Improve the smallest useful layer. Verify. Re-observe.**

The loop exists to increase the rate of useful improvement without converting speed into epistemic sloppiness.

## North Star

> **Maximize useful, forkable, reproducible recovery knowledge and Purrtocol delight while keeping the evidence boundary stronger than the expansion rate.**

“Delight” is intentionally not converted into a fake scientific score.

## Loop

```text
repository state
      |
      v
observe
      |
      v
biopsy a concrete weakness
      |
      v
compete explanations
      |
      v
small reversible change
      |
      v
CI / evidence verification
      |
      +---- FAIL ----> new observation, not weaker standards
      |
      v
promote
      |
      v
re-observe
```

## Authority model

Repository-local implementation may proceed without per-change owner approval.

That does **not** mean:

- empirical claims may be upgraded without evidence;
- failed checks may be bypassed for convenience;
- historical raw evidence may be rewritten;
- story events may be reclassified as observed facts;
- unrelated repositories may be modified merely because they were inspected.

Cross-repository material is imported as design precedent unless a separate change explicitly modifies the source repository.

## Borrowed disciplines

### Finite RAM Lab

Use append-only canonical observations and rebuildable projections.

The improvement ledger lives in:

`data/improvement_events.jsonl`

Dashboards and summaries are projections.

Also preserve observer hygiene: the machinery used to measure repository health can itself create files, workflows, CI traffic, and maintenance load. That cost must remain visible.

### MVCA

Reuse:

```text
Attempt != Operation
Re-observation != Re-execution
UNKNOWN != action authority
```

For repository work:

- one improvement objective has one stable `cycle_id`;
- diagnostic attempts do not silently become new objectives;
- an ambiguous state causes more observation, not automatic promotion.

### Finite Tool Surface Lab

Prefer compact references and digests over permanently committing large redundant outputs.

## First recorded loop

`RIL-001` is the 3D First Light repair cycle.

The 3D validator first rejected a malformed GLB JSON chunk. A two-character binary corruption was biopsied and repaired. The next run rejected a stale contract hash. The metadata was rebound to the repaired artifact. All required checks then passed and PR #4 was promoted.

The important result is not that a bug existed.

The important result is that **the loop got stronger because the bug existed**.

## Machine surfaces

- `data/improvement_events.jsonl`
- `data/improvement_event_schema.json`
- `docs/repository-observatory/state.json`
- `scripts/audit_repository_state.py`
- `.github/workflows/repository-observatory.yml`

## Promotion rule

A repository-observatory failure is not an instruction to relax the observatory.

It is a new specimen.
