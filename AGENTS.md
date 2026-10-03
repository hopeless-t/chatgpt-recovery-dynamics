# AGENTS.md

This repository is both a recovery-systems research project and an intentionally expanding Purrtocol communication universe.

Use this file as a map, not as a substitute for reading the task-relevant source.

## Core invariants

Never weaken these to make a change easier:

- **Recover. Don't amplify.**
- **Visualization != Evidence.**
- **UNKNOWN != retry permission.**
- **Concept != implemented artifact.**
- **Attempt != Operation.**
- **Re-observation != re-execution.**

Do not infer OpenAI's internal root cause, topology, production capacity, exact rate-limit scope, or transport implementation from the public trace.

Do not load-test production OpenAI services, deliberately trigger 429s, bypass rate limits, or publish authenticated HAR data.

## Read only what the task needs

For recovery evidence or claims:
- `docs/evidence-ledger.md`
- `docs/methodology.md`
- `docs/deep-validation.md`

For recovery architecture:
- `docs/recovery-design.md`
- `docs/429-survival-kit/index.md` for standards-aware 429/backpressure client behavior
- `docs/transport-recovery-redesign.md`
- `docs/server-friendly-congestion-control.md`

For Purrtocol canon:
- `docs/purrtocol-design-bible.md`

For 3D work:
- read the nearest `docs/purrtocol-3d/AGENTS.md`

For variants/forks:
- read the nearest `docs/purrtocol-variant-foundry/AGENTS.md`
- `PURRTOCOL_VARIANTS.md`

For repository-wide improvement work:
- `IMPROVEMENT_LOOP.md`
- `docs/repository-observatory/state.json`
- `data/improvement_events.jsonl`

For machine discovery:
- `docs/llms.txt`
- `docs/index.md`
- `docs/purrtocol.json`

## Validation

Prefer the smallest relevant check, then the full invariant stack before promotion.

Useful commands:

```bash
python scripts/analyze_public_data.py
python scripts/validate_purrtocol_3d.py
python scripts/validate_purrtocol_variants.py
python scripts/validate_pakenya_events.py
python scripts/audit_repository_state.py
```

GitHub Actions is the promotion gate for public analysis, Purrtocol lineage, 3D, and repository observatory checks.

A failing check is a specimen. Diagnose it before changing the check.

## Change discipline

- Keep historical raw evidence immutable.
- Add new interpretations prospectively.
- Keep post-checkpoint Purrtocol growth out of frozen primary/observer-inclusive fits.
- Prefer small reversible changes.
- Preserve provenance for generated assets and external sources.
- Keep large derived outputs reproducible or digest-bound when practical.
- Avoid duplicating long instructions here; link to the authoritative document instead.

## Purrtocol

We welcome weirdness.

We do not welcome provenance ambiguity.

A Purrtocol derivative may mutate visually, narratively, culturally, or technically, but its manifest must say what it inherited and what it changed.

## Repository improvement loop

The default loop is:

```text
observe -> biopsy -> competing explanations -> smallest reversible change
        -> verify -> promote -> re-observe
```

Repository-local implementation does not require per-change owner approval, but evidence promotion remains fail-closed.

If the observatory turns red, do not paint it green.
