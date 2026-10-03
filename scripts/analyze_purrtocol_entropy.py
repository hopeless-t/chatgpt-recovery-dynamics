#!/usr/bin/env python3
"""Measure deterministic Purrtocol breeder diversity over a fixed seed cohort.

This measures the breeder implementation, not the real-world Purrtocol ecosystem.

Important distinctions:
- theoretical genotype space != implemented variant population;
- marginal gene entropy != joint ecosystem entropy;
- fixed-seed diversity is a regression/quality diagnostic, not adoption evidence.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from breed_purrtocol import breed

ROOT = Path(__file__).resolve().parents[1]
GENOME_PATH = ROOT / "data" / "purrtocol_genome.json"
REGISTRY_PATH = ROOT / "data" / "purrtocol_variants.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def shannon_bits(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    out = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        p = count / total
        out -= p * math.log2(p)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=4096)
    parser.add_argument("--seed-prefix", default="entropy-probe-")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.samples < 1:
        raise SystemExit("--samples must be >= 1")

    genome = json.loads(GENOME_PATH.read_text(encoding="utf-8"))
    registry = read_jsonl(REGISTRY_PATH)
    genes = genome["genes"]
    gene_order = list(genes)

    theoretical_combinations = math.prod(len(options) for options in genes.values())
    idealized_max_bits = math.log2(theoretical_combinations)

    per_gene = {gene: Counter() for gene in gene_order}
    genotype_counts: Counter[tuple[str, ...]] = Counter()
    variant_ids: set[str] = set()

    for i in range(args.samples):
        seed = f"{args.seed_prefix}{i:06d}"
        variant = breed(
            seed,
            origin_repository="https://github.com/hopeless-t/chatgpt-recovery-dynamics",
            submitted_by="entropy-reactor",
        )
        variant_ids.add(variant["variant_id"])
        genotype = tuple(variant["genome"][gene] for gene in gene_order)
        genotype_counts[genotype] += 1
        for gene, value in variant["genome"].items():
            per_gene[gene][value] += 1

    gene_reports = {}
    sum_marginal_entropy_bits = 0.0

    for gene in gene_order:
        counts = per_gene[gene]
        option_count = len(genes[gene])
        entropy = shannon_bits(counts)
        max_entropy = math.log2(option_count)
        sum_marginal_entropy_bits += entropy
        expected = args.samples / option_count
        max_abs_relative_deviation = max(
            abs(counts.get(option, 0) - expected) / expected
            for option in genes[gene]
        )
        gene_reports[gene] = {
            "option_count": option_count,
            "counts": {option: counts.get(option, 0) for option in genes[gene]},
            "entropy_bits": entropy,
            "max_entropy_bits": max_entropy,
            "normalized_entropy": entropy / max_entropy if max_entropy else 1.0,
            "max_abs_relative_deviation_from_uniform": max_abs_relative_deviation,
            "all_options_observed": all(counts.get(option, 0) > 0 for option in genes[gene]),
        }

    unique_genotypes = len(genotype_counts)
    genotype_collisions = args.samples - unique_genotypes
    collision_pairs = sum(
        count * (count - 1) // 2
        for count in genotype_counts.values()
    )
    idealized_expected_collision_pairs = (
        args.samples * (args.samples - 1)
        / (2.0 * theoretical_combinations)
    )

    registered_variants = len(registry)
    occupancy_fraction = registered_variants / theoretical_combinations
    occupancy_percent = occupancy_fraction * 100.0

    result = {
        "schema": "purrtocol-entropy-report/v1",
        "classification": "deterministic_breeder_quality_diagnostic",
        "seed_cohort": {
            "prefix": args.seed_prefix,
            "samples": args.samples,
        },
        "theoretical_space": {
            "genotype_combinations": theoretical_combinations,
            "idealized_uniform_max_entropy_bits": idealized_max_bits,
            "gene_count": len(gene_order),
        },
        "registered_lineage": {
            "registry_variants": registered_variants,
            "occupancy_fraction_of_theoretical_space": occupancy_fraction,
            "occupancy_percent_of_theoretical_space": occupancy_percent,
            "note": "Registry count is real indexed lineage; theoretical space is not population.",
        },
        "fixed_seed_breeder_probe": {
            "unique_variant_ids": len(variant_ids),
            "unique_genotypes": unique_genotypes,
            "genotype_collisions": genotype_collisions,
            "collision_pairs": collision_pairs,
            "idealized_uniform_expected_collision_pairs": idealized_expected_collision_pairs,
            "sum_of_marginal_gene_entropies_bits": sum_marginal_entropy_bits,
            "note": "Sum of marginal entropies is not measured joint ecosystem entropy.",
        },
        "genes": gene_reports,
        "interpretation_rules": [
            "199,148,544 theoretical genotypes do not mean 199,148,544 implemented cats.",
            "This fixed-seed cohort measures deterministic breeder diversity, not external adoption.",
            "Per-gene Shannon entropy is a marginal implementation diagnostic.",
            "A collision is not automatically a bug; sustained collapse or missing options would be a regression signal.",
            "The registry remains the authority for real indexed variants.",
        ],
    }

    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
