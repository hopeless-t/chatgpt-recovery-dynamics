# Purrtocol Genome Nursery / パケニャ培養槽

> Deterministically generate a **concept manifest** from a seed.

## Important boundary

The genome currently spans **199,148,544 theoretical genotype combinations**.

That number is a combinatorial concept space.

It is **not** an implemented-variant count, population estimate, adoption metric, or evidence of external forks.

The canonical registry can still contain one implemented root while the concept space is enormous.

## Reproduce locally

```bash
python scripts/breed_purrtocol.py \
  --seed pakenya-cambrian-001 \
  --origin-repository https://github.com/YOU/YOUR-FORK \
  --submitted-by your-handle
```

Same seed + same genome version gives the same:

- `variant_id`;
- name;
- gene selections;
- mutation list.

Origin/submission metadata remains supplied by the caller.

## Selection rule

For each gene:

```text
H = SHA256(seed + ":" + gene_name)
index = first_64_bits_big_endian(H) mod option_count
```

Variant identity:

```text
PKV-SEED- + first 12 uppercase hex chars of SHA256(seed)
```

## Current genes

- medium
- silhouette
- habitat
- blocked cue
- recovering cue
- healthy cue
- observation prop
- temperament
- narrative job
- mutation class

Canonical genome: [purrtocol-genome.json](../purrtocol-genome.json)

## Lifecycle

```text
seed
  ↓
generated concept
  ↓
fork chooses to implement
  ↓
real artifact + provenance
  ↓
optional upstream lineage PR
```

Nursery output defaults to:

```text
status = concept
evidence_status = concept
```

Generation does not silently promote itself.

**Generated != implemented.**
