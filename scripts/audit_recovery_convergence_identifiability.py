#!/usr/bin/env python3
"""REC-FP-001: audit whether the current capture can identify recovery contraction.

The fixed-point correspondence proposes measuring contraction after B -> E
reentry. This script first asks a stricter question:

    does the sanitized capture contain enough consecutive post-reentry
    Accessible observations to estimate any contraction ratio at all?

It does not generate production traffic and it does not infer backend state.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SESSION_GAP_S = 60.0


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["t_rel_s"] = float(row["t_rel_s"])
        row["stream_latency_ms"] = float(row["stream_latency_ms"])
        row["snapshot_latency_ms"] = float(row["snapshot_latency_ms"])
    return rows


def split_epochs(rows: list[dict]) -> list[list[dict]]:
    epochs: list[list[dict]] = []
    start = 0
    for index in range(len(rows) - 1):
        if rows[index + 1]["t_rel_s"] - rows[index]["t_rel_s"] > SESSION_GAP_S:
            epochs.append(rows[start:index + 1])
            start = index + 1
    epochs.append(rows[start:])
    return epochs


def audit(rows: list[dict]) -> dict:
    reentries = []
    contraction_pairs = []
    stable_reentries = 0
    rebound_next = 0
    post_reentry_run_lengths = []

    for epoch_index, epoch in enumerate(split_epochs(rows), start=1):
        for index in range(1, len(epoch)):
            prev = epoch[index - 1]
            cur = epoch[index]
            if prev["state"] != "blocked" or cur["state"] != "accessible":
                continue

            run = 1
            cursor = index + 1
            while cursor < len(epoch) and epoch[cursor]["state"] == "accessible":
                run += 1
                cursor += 1

            next_state = epoch[index + 1]["state"] if index + 1 < len(epoch) else None
            if next_state == "blocked":
                rebound_next += 1
            if run >= 2:
                stable_reentries += 1

            post_reentry_run_lengths.append(run)
            reentries.append(
                {
                    "epoch": epoch_index,
                    "t_rel_s": cur["t_rel_s"],
                    "accessible_run_length_from_reentry": run,
                    "next_state": next_state,
                    "service_s": max(
                        cur["stream_latency_ms"],
                        cur["snapshot_latency_ms"],
                    ) / 1000.0,
                }
            )

            # A contraction ratio requires at least two consecutive accessible
            # post-reentry observations. Count every adjacent A/A pair inside
            # the reentry run as one potentially observable contraction step.
            for pair_index in range(index, index + run - 1):
                contraction_pairs.append(
                    {
                        "epoch": epoch_index,
                        "t0_rel_s": epoch[pair_index]["t_rel_s"],
                        "t1_rel_s": epoch[pair_index + 1]["t_rel_s"],
                    }
                )

    reentry_n = len(reentries)
    max_run = max(post_reentry_run_lengths) if post_reentry_run_lengths else 0

    if contraction_pairs:
        contraction_status = "CONTRACTION_OBSERVABLE"
    else:
        contraction_status = "CONTRACTION_NOT_IDENTIFIABLE_FROM_CURRENT_CAPTURE"

    return {
        "schema": "recovery-convergence-identifiability/v1",
        "experiment_id": "REC-FP-001",
        "classification": "within_capture_identifiability_audit",
        "input": {
            "dataset": "data/paired_observations.csv",
            "session_gap_s": SESSION_GAP_S,
            "production_traffic_generated": False,
        },
        "reentry": {
            "b_to_e_events": reentry_n,
            "e_to_b_next": rebound_next,
            "e_to_h_observed": stable_reentries,
            "max_post_reentry_accessible_run_length": max_run,
            "post_reentry_run_lengths": post_reentry_run_lengths,
        },
        "contraction_identifiability": {
            "adjacent_post_reentry_accessible_pairs": len(contraction_pairs),
            "empirical_kappa_samples_available": len(contraction_pairs),
            "status": contraction_status,
            "reason": (
                "Estimating kappa_n = r_(n+1)/r_n requires at least two "
                "consecutive post-reentry Accessible observations. None exist "
                "in this capture."
                if not contraction_pairs
                else "At least one consecutive post-reentry Accessible pair exists."
            ),
        },
        "candidate_model_status": {
            "M_A_categorical_H_E_B": "SUPPORTED_WITHIN_CAPTURE",
            "M_B_semi_markov_recovery": "NOT_TESTED_BY_THIS_AUDIT",
            "M_C_observable_contraction": (
                "UNIDENTIFIABLE_FROM_CURRENT_CAPTURE"
                if not contraction_pairs
                else "TESTABLE"
            ),
            "M_D_rebound_hysteresis": (
                "SUPPORTED_WITHIN_CAPTURE"
                if reentry_n and rebound_next == reentry_n
                else "PARTIAL_OR_NOT_ESTABLISHED"
            ),
            "M_E_no_fixed_point_structure": "NOT_REJECTED",
        },
        "claim_ceiling": {
            "allowed": [
                "RECOVERY_CONVERGENCE_IDENTIFIABILITY_AUDITED",
                "CURRENT_CAPTURE_LACKS_POST_REENTRY_CONTRACTION_PAIRS",
                "WITHIN_CAPTURE_REBOUND_HYSTERESIS_OBSERVED",
            ],
            "forbidden": [
                "OPENAI_BACKEND_FIXED_POINT_IDENTIFIED",
                "CHATGPT_INTERNAL_ATTRACTOR_IDENTIFIED",
                "FIXED_POINT_DYNAMICS_DISPROVEN_GLOBALLY",
                "PRODUCTION_ROOT_CAUSE_IDENTIFIED",
            ],
        },
        "reentries": reentries,
        "contraction_pairs": contraction_pairs,
        "next_evidence": (
            "An independent capture with at least one B->E->H or longer "
            "post-reentry Accessible run is required before fitting a "
            "contraction ratio or convergence depth."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/paired_observations.csv")
    parser.add_argument("--output")
    args = parser.parse_args()

    result = audit(load_rows(Path(args.csv)))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
