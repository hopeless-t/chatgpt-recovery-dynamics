# AGENTS.md — 3D Purrtocol

This directory has a stricter local contract than the repository root.

## Canon

Read:

- `README.md`
- `../purrtocol-design-bible.md`
- `../../data/purrtocol_3d_contract.json`
- `FIRST_LIGHT.json`

## Required runtime semantics

The canonical GLB must preserve all required node names and animation names from `data/purrtocol_3d_contract.json`.

State meaning must remain legible:

- B / Blocked
- E / Recovering
- H / Healthy
- tiny observation packet
- heavier snapshot materialization

Color alone is not sufficient where a pose, silhouette, prop, or motion cue is practical.

## Validation

Run:

```bash
python scripts/validate_purrtocol_3d.py
python scripts/audit_repository_state.py
```

If the GLB changes, update measured byte/hash/runtime facts only after observing the new artifact.

Never change the expected hash first merely to make CI pass.

## Provenance

PKE-106 is the immutable concept origin.

PKE-033 is the implemented First Light lineage event.

Future visual refinements should create new implementation history rather than rewriting the concept origin.

## Evidence boundary

The 3D model is an implemented visualization.

It is not evidence for production topology, backend state, root cause, or service internals.
