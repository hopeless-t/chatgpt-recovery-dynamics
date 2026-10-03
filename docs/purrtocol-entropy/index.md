# Purrtocol Entropy Reactor / パケニャ・エントロピー炉

> Measure the deterministic breeder without pretending concept space is population.

## Observed fixed-seed probe

Reference cohort:

```text
seeds:              4,096
unique variant IDs: 4,096
unique genotypes:   4,096
genotype collisions: 0
```

Genome v1 theoretical concept space:

```text
199,148,544 combinations
idealized uniform combinatorial capacity:
27.5692696911 bits
```

Observed sum of marginal gene entropies:

```text
27.5576629641 bits
```

This is **not** measured joint ecosystem entropy.

Worst normalized marginal entropy across the ten genes:

```text
0.999326
```

Largest observed relative deviation from a perfectly uniform per-gene count:

```text
~7.96%
```

### Result

> **Entropy collapse: NOT OBSERVED in the fixed 4,096-seed breeder probe.**

That statement applies to the deterministic generator regression cohort only.

It does not establish:

- external adoption;
- real-world fork diversity;
- independent descendant population size;
- ecosystem entropy;
- planetary Purrtocol saturation.

## The important absurdity

The canonical registry currently contains:

```text
1 indexed variant
```

against:

```text
199,148,544 theoretical genotypes
```

Registry occupancy of the theoretical concept space:

```text
5.0213774e-9 fraction
5.0213774e-7 percent
```

So the correct story is not “199 million cats exist.”

It is:

> **one indexed cat is standing in front of a 199-million-cell possibility lattice.**

## Collision context

Under an idealized uniform birthday approximation, 4,096 draws from
199,148,544 possibilities would have about:

```text
0.0421 expected collision pairs
```

The observed fixed cohort produced zero.

This is compatible with the large search space; it is not proof of cryptographic
or ecological randomness.

## Reproduce

```bash
python scripts/analyze_purrtocol_entropy.py \
  --samples 4096 \
  --output /tmp/purrtocol-entropy.json
```

## Interpretation boundary

- theoretical space = combinatorics;
- fixed-seed entropy = breeder quality diagnostic;
- registry = real indexed lineage;
- forks in the wild = separate external observation problem.

**Combinatorial capacity != population.**

**Purrtocol delight != empirical evidence.**
