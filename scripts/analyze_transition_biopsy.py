#!/usr/bin/env python3
"""A->B transition biopsy and small-sample model competition.

Uses only the published paired observation CSV. The primary question is:
what distinguishes an Accessible observation that remains Accessible from one
whose next observation returns to Blocked?

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


SESSION_GAP_S = 60.0


def load_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    numeric = {
        "t_rel_s",
        "pair_skew_ms",
        "stream_latency_ms",
        "snapshot_latency_ms",
        "snapshot_payload_kib_rounded_4",
    }
    for row in rows:
        for key in numeric:
            row[key] = float(row[key])
    return rows


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(
        p * (1 - p) / n + z * z / (4 * n * n)
    ) / d
    return [center - half, center + half]


def comb(n, k):
    return math.comb(n, k)


def fisher_reentry_one_sided():
    # Observed table:
    # reentry:     8 -> B, 0 -> A
    # non-reentry: 2 -> B, 38 -> A
    # Conditional on 10 total A->B events, probability that >=8 land in the
    # eight reentry rows is exactly the probability all eight reentry rows do.
    return comb(10, 8) * comb(38, 0) / comb(48, 8)


def transition_biopsy(rows):
    out = []
    epoch = 1
    epoch_start = rows[0]["t_rel_s"]
    accessible_run = 0

    for i in range(len(rows) - 1):
        cur = rows[i]
        nxt = rows[i + 1]

        if i > 0 and cur["t_rel_s"] - rows[i - 1]["t_rel_s"] > SESSION_GAP_S:
            epoch += 1
            epoch_start = cur["t_rel_s"]
            accessible_run = 0

        if cur["state"] == "accessible":
            accessible_run += 1
        else:
            accessible_run = 0

        next_gap = nxt["t_rel_s"] - cur["t_rel_s"]
        if next_gap > SESSION_GAP_S or cur["state"] != "accessible":
            continue

        prev = None
        if i > 0 and cur["t_rel_s"] - rows[i - 1]["t_rel_s"] <= SESSION_GAP_S:
            prev = rows[i - 1]

        out.append(
            {
                "epoch": epoch,
                "t_rel_s": cur["t_rel_s"],
                "next_blocked": int(nxt["state"] == "blocked"),
                "reentry_from_blocked": int(
                    prev is not None and prev["state"] == "blocked"
                ),
                "accessible_run_length": accessible_run,
                "service_s": max(
                    cur["stream_latency_ms"],
                    cur["snapshot_latency_ms"],
                ) / 1000.0,
                "stream_s": cur["stream_latency_ms"] / 1000.0,
                "snapshot_s": cur["snapshot_latency_ms"] / 1000.0,
                "pair_skew_ms": cur["pair_skew_ms"],
                "snapshot_payload_kib": cur[
                    "snapshot_payload_kib_rounded_4"
                ],
                "previous_gap_s": (
                    cur["t_rel_s"] - prev["t_rel_s"]
                    if prev is not None
                    else None
                ),
                "time_in_epoch_s": cur["t_rel_s"] - epoch_start,
            }
        )

    return out


def mean(xs):
    return sum(xs) / len(xs)


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n % 2:
        return xs[n // 2]
    return (xs[n // 2 - 1] + xs[n // 2]) / 2


def describe(rows, key):
    xs = [r[key] for r in rows if r[key] is not None]
    xs = sorted(xs)
    return {
        "n": len(xs),
        "mean": mean(xs),
        "median": median(xs),
        "min": xs[0],
        "max": xs[-1],
    }


def markov_counts(rows):
    epochs = []
    start = 0
    for i in range(len(rows) - 1):
        if rows[i + 1]["t_rel_s"] - rows[i]["t_rel_s"] > SESSION_GAP_S:
            epochs.append(rows[start : i + 1])
            start = i + 1
    epochs.append(rows[start:])

    two = {k: 0 for k in ("A->A", "A->B", "B->A", "B->B")}
    hist = {
        k: 0
        for k in (
            "H->H",
            "H->B",
            "E->B",
            "E->H",
            "B->B",
            "B->E",
        )
    }

    for epoch in epochs:
        labeled = []
        for i, row in enumerate(epoch):
            if row["state"] == "blocked":
                labeled.append("B")
            else:
                prev = epoch[i - 1] if i > 0 else None
                labeled.append(
                    "E"
                    if prev is not None and prev["state"] == "blocked"
                    else "H"
                )

        for i in range(len(epoch) - 1):
            a = "A" if epoch[i]["state"] == "accessible" else "B"
            b = "A" if epoch[i + 1]["state"] == "accessible" else "B"
            two[f"{a}->{b}"] += 1

            x, y = labeled[i], labeled[i + 1]
            key = f"{x}->{y}"
            if key in hist:
                hist[key] += 1

    return two, hist


def binomial_ll(success, failure):
    n = success + failure
    if n == 0:
        return 0.0
    p = success / n
    ll = 0.0
    if success:
        ll += success * math.log(p)
    if failure:
        ll += failure * math.log(1 - p)
    return ll


def markov_competition(rows):
    two, hist = markov_counts(rows)

    ll2 = (
        binomial_ll(two["A->B"], two["A->A"])
        + binomial_ll(two["B->A"], two["B->B"])
    )
    n = sum(two.values())
    k2 = 2

    # History-aware Accessible model:
    # H = Accessible not immediately preceded by B
    # E = one-cycle Accessible excursion immediately preceded by B
    # B transition probability remains first-order.
    llh = (
        binomial_ll(hist["H->B"], hist["H->H"])
        + binomial_ll(hist["E->B"], hist["E->H"])
        + binomial_ll(hist["B->E"], hist["B->B"])
    )
    kh = 3

    return {
        "two_state_first_order": {
            "counts": two,
            "log_likelihood": ll2,
            "parameters": k2,
            "aic": 2 * k2 - 2 * ll2,
            "bic": k2 * math.log(n) - 2 * ll2,
        },
        "history_aware_three_label": {
            "definition": (
                "H=stable/ordinary Accessible, "
                "E=Accessible immediately after Blocked, B=Blocked"
            ),
            "counts": hist,
            "log_likelihood": llh,
            "parameters": kh,
            "aic": 2 * kh - 2 * llh,
            "bic": kh * math.log(n) - 2 * llh,
        },
        "delta_aic_history_minus_two_state": (
            (2 * kh - 2 * llh) - (2 * k2 - 2 * ll2)
        ),
        "delta_bic_history_minus_two_state": (
            (kh * math.log(n) - 2 * llh)
            - (k2 * math.log(n) - 2 * ll2)
        ),
    }


def summarize(rows, biopsy):
    to_b = [r for r in biopsy if r["next_blocked"]]
    stay = [r for r in biopsy if not r["next_blocked"]]
    reentry = [r for r in biopsy if r["reentry_from_blocked"]]
    non = [r for r in biopsy if not r["reentry_from_blocked"]]

    re_b = sum(r["next_blocked"] for r in reentry)
    non_b = sum(r["next_blocked"] for r in non)

    return {
        "accessible_origin_transitions": len(biopsy),
        "a_to_b": len(to_b),
        "a_to_a": len(stay),
        "reentry_contingency": {
            "reentry_n": len(reentry),
            "reentry_to_blocked": re_b,
            "non_reentry_n": len(non),
            "non_reentry_to_blocked": non_b,
            "p_next_blocked_reentry": re_b / len(reentry),
            "p_next_blocked_non_reentry": non_b / len(non),
            "wilson_95_reentry": wilson(re_b, len(reentry)),
            "wilson_95_non_reentry": wilson(non_b, len(non)),
            "fisher_exact_one_sided": fisher_reentry_one_sided(),
        },
        "biopsy_descriptives": {
            key: {
                "stay_accessible": describe(stay, key),
                "transition_to_blocked": describe(to_b, key),
            }
            for key in (
                "service_s",
                "stream_s",
                "snapshot_s",
                "pair_skew_ms",
                "previous_gap_s",
                "accessible_run_length",
                "time_in_epoch_s",
            )
        },
        "model_competition": markov_competition(rows),
        "interpretation_guardrail": (
            "Reentry history is highly predictive in this capture, but only "
            "eight reentry observations exist. This is evidence for recovery "
            "hysteresis, not a population-level transition law."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="data/paired_observations.csv",
    )
    parser.add_argument("--output")
    parser.add_argument("--biopsy-output")
    args = parser.parse_args()

    rows = load_rows(Path(args.csv))
    biopsy = transition_biopsy(rows)
    summary = summarize(rows, biopsy)

    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")

    if args.biopsy_output:
        Path(args.biopsy_output).write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in biopsy) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
