#!/usr/bin/env python3
"""Small-sample model competition for Accessible -> Blocked transitions.

The models are deliberately simple and auditable. Continuous variables are only
used through preregistered/coarse partitions that have an independent rationale
from the already-established timing model.

Scoring:
- exact Beta-Bernoulli marginal likelihood with Jeffreys prior;
- leave-one-out posterior predictive log loss;
- leave-one-out Brier score.

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

SESSION_GAP_S = 60.0


def load_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    numeric = {
        "t_rel_s",
        "stream_latency_ms",
        "snapshot_latency_ms",
    }
    for row in rows:
        for key in numeric:
            row[key] = float(row[key])
    return rows


def build_examples(rows):
    epoch = 1
    accessible_run = 0
    out = []

    for i in range(len(rows) - 1):
        cur = rows[i]
        nxt = rows[i + 1]

        if i > 0 and cur["t_rel_s"] - rows[i - 1]["t_rel_s"] > SESSION_GAP_S:
            epoch += 1
            accessible_run = 0

        if cur["state"] == "accessible":
            accessible_run += 1
        else:
            accessible_run = 0

        gap_next = nxt["t_rel_s"] - cur["t_rel_s"]
        if gap_next > SESSION_GAP_S or cur["state"] != "accessible":
            continue

        prev = None
        if i > 0 and cur["t_rel_s"] - rows[i - 1]["t_rel_s"] <= SESSION_GAP_S:
            prev = rows[i - 1]

        prev_gap = (
            cur["t_rel_s"] - prev["t_rel_s"]
            if prev is not None
            else None
        )
        service_s = max(
            cur["stream_latency_ms"],
            cur["snapshot_latency_ms"],
        ) / 1000.0

        out.append(
            {
                "y": int(nxt["state"] == "blocked"),
                "epoch": epoch,
                "reentry": int(
                    prev is not None and prev["state"] == "blocked"
                ),
                # 8 s is the midpoint between the previously established
                # ~6 s blocked and ~10 s accessible cadence regimes.
                "previous_gap_lt_8s": (
                    None if prev_gap is None else int(prev_gap < 8.0)
                ),
                # 5 s is a coarse comparator around the observed accessible
                # snapshot/service scale. It is not a tuned threshold.
                "service_lt_5s": int(service_s < 5.0),
                "accessible_run_le_2": int(accessible_run <= 2),
            }
        )

    return out


def log_beta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def score_model(name, examples, key):
    rows = [r for r in examples if r[key] is not None]
    groups = defaultdict(lambda: {"success": 0, "failure": 0})

    for row in rows:
        g = str(row[key])
        if row["y"]:
            groups[g]["success"] += 1
        else:
            groups[g]["failure"] += 1

    log_ml = 0.0
    for g in groups.values():
        log_ml += (
            log_beta(g["success"] + 0.5, g["failure"] + 0.5)
            - log_beta(0.5, 0.5)
        )

    loo_log = 0.0
    loo_brier = 0.0

    for i, row in enumerate(rows):
        g = str(row[key])
        success = 0
        failure = 0
        for j, other in enumerate(rows):
            if i == j or str(other[key]) != g:
                continue
            if other["y"]:
                success += 1
            else:
                failure += 1

        p = (success + 0.5) / (success + failure + 1.0)
        if row["y"]:
            loo_log += math.log(p)
        else:
            loo_log += math.log(1.0 - p)
        loo_brier += (row["y"] - p) ** 2

    return {
        "name": name,
        "n": len(rows),
        "groups": dict(groups),
        "log_marginal_likelihood": log_ml,
        "loo_logloss": -loo_log / len(rows),
        "loo_brier": loo_brier / len(rows),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="data/paired_observations.csv",
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    examples = build_examples(load_rows(Path(args.csv)))

    # Constant model is represented by one literal stratum.
    for row in examples:
        row["constant"] = "all"

    specs = [
        ("M0_constant", "constant"),
        ("M1_epoch", "epoch"),
        ("M2_reentry_history", "reentry"),
        ("M3_previous_gap_lt8s", "previous_gap_lt_8s"),
        ("M4_service_lt5s", "service_lt_5s"),
        ("M5_accessible_run_le2", "accessible_run_le_2"),
    ]

    results = [score_model(name, examples, key) for name, key in specs]
    base = next(
        r["log_marginal_likelihood"]
        for r in results
        if r["name"] == "M0_constant"
    )

    for result in results:
        result["log_bayes_factor_vs_constant"] = (
            result["log_marginal_likelihood"] - base
        )

    results.sort(key=lambda r: r["loo_logloss"])

    output = {
        "scoring": {
            "prior": "Jeffreys Beta(1/2,1/2) per Bernoulli stratum",
            "primary": "leave-one-out posterior predictive log loss",
            "secondary": [
                "leave-one-out Brier score",
                "exact integrated marginal likelihood",
            ],
        },
        "models": results,
        "guardrail": (
            "This is small-sample model competition over one capture. "
            "The reentry-history result is a strong within-capture predictor, "
            "not a population-level production law."
        ),
    }

    text = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
