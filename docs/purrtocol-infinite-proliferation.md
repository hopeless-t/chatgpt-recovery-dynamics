# Purrtocol Infinite Proliferation Project

Purrtocol may proliferate without pretending that generated concepts are implemented artifacts.

The project slogan is playful; the mechanism is strict:

> **Unbounded process. Bounded run. Traceable lineage.**

## Why this exists

The existing Purrtocol Genome Nursery can map deterministic seeds into a large finite genotype space.

The next problem is operational: how can people, agents, forks, classrooms, tools, and other projects keep generating derivatives without:

- inflating the canonical registry with unimplemented concepts;
- confusing concepts with evidence;
- losing parentage/provenance;
- creating one giant non-resumable generation job;
- turning proliferation itself into retry/amplification waste?

The answer is a resumable swarm breeder.

## Run a colony

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

Every invocation is finite. The default batch is 32 and the hard per-run cap is 4096.

The generated `_swarm_index.json` records `next_start`, so the next bounded run can continue:

```bash
python scripts/breed_purrtocol_swarm.py \
  --namespace my-colony \
  --epoch 0 \
  --start 32 \
  --count 32 \
  --origin-repository https://github.com/YOU/YOUR-FORK \
  --submitted-by your-handle \
  --output-dir /tmp/purrtocol-colony \
  --resume
```

## Chain mode

By default every generated concept points to the requested parent, normally `PKV-CANONICAL`.

Use `--chain-parent` to create a lineage walk:

```text
PKV-CANONICAL
    ↓
concept 0
    ↓
concept 1
    ↓
concept 2
    ↓
...
```

This makes the mutation history itself part of the derivative structure.

## What “infinite” means here

The phrase does **not** mean that a computer can materialize infinitely many files.

Three different spaces must remain separate:

1. **Seed stream** — can be extended without a predeclared terminal ordinal.
2. **Genome state space** — finite for a fixed genome schema; repeated genotypes are eventually possible.
3. **Implemented population** — only artifacts humans or agents actually build and bind to provenance.

The current genome's published theoretical genotype cardinality remains a property of the genome schema, not a claim about the implemented population.

The swarm therefore models an open-ended **generation process**, not an infinite stored set.

## Epochs

`epoch` lets a colony open a new deterministic generation era without rewriting history.

Example:

```text
namespace = public-lab
epoch 0   = first exploration
epoch 1   = after a new tool/rendering stack arrives
epoch 2   = after a localization campaign
```

Old output remains reproducible from its original namespace/epoch/ordinal tuple.

## Resume semantics

`--resume` reuses an existing concept file only when its complete canonical JSON is byte-identical to the result that would be generated now.

A mismatched file fails closed.

This intentionally mirrors the recovery project itself:

```text
interrupted proliferation
        ↓
observe existing artifact
        ↓
identical -> reuse
mismatch   -> stop
        ↓
never blindly overwrite provenance
```

## Promotion boundary

Swarm output always starts as:

```text
status = concept
evidence_status = concept
```

Generation does not mean:

- implemented;
- upstream indexed;
- endorsed;
- empirically validated;
- observed in production.

To promote one concept into an implemented Purrtocol derivative:

1. choose the concept;
2. build the artifact;
3. bind real repository/commit/asset provenance;
4. validate the applicable invariant checks;
5. optionally submit the lineage upstream.

See `PURRTOCOL_VARIANTS.md`.

## The proliferation law

The project should maximize **diversity of understandable recovery explanations**, not raw file count.

A healthy colony therefore prefers:

- different media;
- different species/silhouettes;
- different educational roles;
- different languages and cultures;
- different recovery concepts;
- different implementation stacks;

while preserving the canonical recovery invariants unless a variant is explicitly marked as a negative example.

## Anti-Goodhart rule

Do not optimize:

- number of generated manifests;
- number of cats;
- number of commits;
- number of forks;
- number of registry rows.

Optimize whether a derivative makes a recovery invariant easier to understand, test, teach, or reuse.

## Relationship to Recovery Dynamics

The proliferation process deliberately reuses the parent project's core rule:

> **Recover. Don't amplify.**

Even cat generation should not become an amplification bug.

That means bounded batches, deterministic identities, resumable observation, explicit provenance, and no automatic promotion of ambiguous state.
