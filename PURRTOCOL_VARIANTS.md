# Purrtocol Variant Protocol / パケニャ亜種プロトコル

Purrtocol is allowed to mutate.

The goal is not one perfect mascot. The goal is a **traceable family tree** of derivatives that can be forked, remixed, taught with, rendered, animated, translated, or reinterpreted without losing the recovery/evidence rules that made the original useful.

> **Fork freely. Preserve lineage. Do not upgrade fiction into evidence.**

## Fast path

1. Fork this repository.
2. Copy `examples/purrtocol-variant.example.json`.
3. Give the variant a globally distinctive `PKV-...` identifier.
4. Point `parent_variant_id` at the variant you actually mutated.
5. Describe the mutations.
6. Keep at least three canonical invariants in `preserved_invariants`.
7. Implement the artifact in your fork.
8. Open a PR here if you want the lineage indexed by the canonical registry.

A fork does **not** need upstream approval to exist.

Upstream PR acceptance only means the canonical registry has indexed the lineage. It does not grant authenticity, correctness, endorsement, or evidence status beyond what the manifest says.

## Canonical invariants

Variants may change species, color language, clothes, props, rendering style, voice, educational setting, dimensions, animation style, or implementation stack.

They should not silently erase these distinctions:

- recovery should not amplify avoidable work;
- visualization is not evidence;
- UNKNOWN is not permission to re-execute;
- Purrtocol stays on the observer/recovery side rather than pretending to know backend internals;
- concept and implementation remain different states;
- the first post-Blocked success is not automatically Healthy;
- cheap observation is distinct from heavy materialization.

A deliberately rebellious variant may violate one of these **as a negative example**, but the manifest must say what was violated and the surrounding explanation must keep the underlying rule clear.

## Variant classes

Suggested mutation classes:

- **visual strain** — new art direction, 2D/3D/voxel/pixel/ASCII;
- **protocol strain** — emphasizes transport, retry, identity, or recovery semantics;
- **education strain** — classroom, game, lab, museum, courtroom, simulator;
- **localization strain** — language/culture-specific teaching form;
- **tool strain** — Blender rig, Godot scene, Three.js viewer, terminal TUI, etc.;
- **cross-project strain** — ports the mascot semantics into another recovery/control project;
- **chaos strain** — intentionally wrong behavior used as a teachable negative example.

## Machine-readable lineage

Schema:

`data/purrtocol_variant_schema.json`

Canonical registry:

`data/purrtocol_variants.jsonl`

Submission example:

`examples/purrtocol-variant.example.json`

A registry row records lineage and artifact state. It is **not** a ranking.

## Crawler/agent entry points

- `docs/llms.txt` — compact agent map.
- `docs/index.md` — clean Markdown project entry.
- `docs/purrtocol.json` — compact machine-readable Purrtocol discovery manifest.
- `docs/purrtocol-variant-foundry/index.md` — variant/fork instructions.
- `docs/purrtocol-variant-foundry/` — human interactive foundry.

## Story layer: observation horizon

The running story says Purrtocol proliferation continues until the named **Sam/Tibo observation event**.

Current canonical story status:

```text
Sam  -> NOT OBSERVED
Tibo -> NOT OBSERVED
```

This is satire and narrative bookkeeping only.

The project does not monitor named people, infer whether they viewed a page, scrape private activity, or claim their attention without public evidence.

If a real public observation ever occurs, record the exact public source and classify it separately from the story.

## License and attribution

The repository is MIT licensed. Keep upstream attribution where required by the license, and be explicit about third-party asset licenses.

A variant can be weird.

Its provenance should not be.


## Deterministic concept breeding

The [Purrtocol Genome Nursery](https://hopeless-t.github.io/chatgpt-recovery-dynamics/purrtocol-nursery/)
can generate a deterministic **concept** from a seed.

CLI equivalent:

```bash
python scripts/breed_purrtocol.py \
  --seed your-seed \
  --origin-repository https://github.com/YOU/YOUR-FORK \
  --submitted-by your-handle
```

Genome v1 contains 199,148,544 theoretical genotype combinations.

That is a **concept-space cardinality**, not an implemented population count.

Nursery output remains:

```text
status = concept
evidence_status = concept
```

until somebody implements an artifact and binds real provenance.

The seed/generator/genome fields are optional provenance extensions in
`purrtocol-variant/v1`. A hand-designed variant does not need to use the
breeder.

## Infinite proliferation mode

For an open-ended but bounded-per-run colony, use:

```bash
python scripts/breed_purrtocol_swarm.py \
  --namespace my-colony \
  --epoch 0 \
  --start 0 \
  --count 32 \
  --origin-repository https://github.com/YOU/YOUR-FORK \
  --submitted-by your-handle \
  --output-dir /tmp/purrtocol-colony
```

The process can continue through successive deterministic batches while every invocation stays finite and resumable.

See `docs/purrtocol-infinite-proliferation.md`.

The same boundary still applies:

> **Generated concept != implemented Purrtocol.**
