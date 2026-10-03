# AGENTS.md — Purrtocol Variant Foundry

This directory governs fork/variant lineage work.

## Start here

Read:

- `../../../PURRTOCOL_VARIANTS.md`
- `../../purrtocol-variant.schema.json`
- `../../../examples/purrtocol-variant.example.json`
- `../../../data/purrtocol_variants.jsonl`

## Genome Nursery

A deterministic concept can be generated with:

```bash
python scripts/breed_purrtocol.py --seed your-seed
```

The result is still a **concept**. Do not add it to the canonical registry as an
implemented/external variant until a real artifact and provenance exist.

## Variant rules

- A fork does not need upstream permission to exist.
- Upstream indexing records provenance; it is not endorsement or ranking.
- Use a distinctive `PKV-...` identifier.
- Point `parent_variant_id` at the variant actually mutated.
- Describe mutations explicitly.
- Preserve at least three canonical invariants.
- Document third-party asset licenses.
- Keep story, concept, implementation, and observed repository history distinct.

## Validation

Run:

```bash
python scripts/validate_purrtocol_variants.py
python scripts/audit_repository_state.py
```

Do not hand-edit the canonical registry to imply an external descendant exists when no corresponding artifact/provenance exists.

## Weirdness policy

Strange cats are welcome.

Lineage ambiguity is not.
