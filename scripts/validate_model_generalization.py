#!/usr/bin/env python3
"""Generalization checks for timing memory and history-aware recovery state.

This script asks two adversarial questions:

1. Is the AR-like timing memory merely omitted A/B state or epoch structure?
2. Does the H/E/B transition model generalize across the two active epochs
   better than a first-order A/B model?

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

SESSION_GAP_S = 60.0


def load_rows(path):
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        for key in (
            "t_rel_s",
            "stream_latency_ms",
            "snapshot_latency_ms",
        ):
            row[key] = float(row[key])

    return rows


def split_epochs(rows):
    epochs = []
    start = 0

    for i in range(len(rows) - 1):
        if (
            rows[i + 1]["t_rel_s"]
            - rows[i]["t_rel_s"]
            > SESSION_GAP_S
        ):
            epochs.append(rows[start : i + 1])
            start = i + 1

    epochs.append(rows[start:])
    return epochs


def solve_linear(a, b):
    n = len(b)
    m = [[*a[i], b[i]] for i in range(n)]

    for col in range(n):
        pivot = max(
            range(col, n),
            key=lambda r: abs(m[r][col]),
        )
        m[col], m[pivot] = m[pivot], m[col]

        value = m[col][col]
        if abs(value) < 1e-12:
            value = 1e-12 if value >= 0 else -1e-12

        for j in range(col, n + 1):
            m[col][j] /= value

        for row in range(n):
            if row == col:
                continue

            factor = m[row][col]

            for j in range(col, n + 1):
                m[row][j] -= factor * m[col][j]

    return [row[n] for row in m]


def ols(rows, features):
    x = [
        [1.0] + [row[f] for f in features]
        for row in rows
    ]
    y = [row["gap_s"] for row in rows]

    k = len(x[0])
    xtx = [[0.0] * k for _ in range(k)]
    xty = [0.0] * k

    for row, target in zip(x, y):
        for i in range(k):
            xty[i] += row[i] * target

            for j in range(k):
                xtx[i][j] += row[i] * row[j]

    beta = solve_linear(xtx, xty)

    residuals = [
        target
        - sum(
            row[j] * beta[j]
            for j in range(k)
        )
        for row, target in zip(x, y)
    ]

    sse = sum(r * r for r in residuals)

    bic = (
        len(rows) * math.log(sse / len(rows))
        + k * math.log(len(rows))
    )

    return {
        "features": features,
        "beta": beta,
        "residuals": residuals,
        "sse": sse,
        "bic": bic,
    }


def residual_ar1(rows, residuals):
    numerator = 0.0
    denominator = 0.0

    for epoch in (1, 2):
        rr = [
            residuals[i]
            for i, row in enumerate(rows)
            if row["epoch"] == epoch
        ]

        for i in range(1, len(rr)):
            numerator += rr[i] * rr[i - 1]
            denominator += rr[i - 1] ** 2

    phi = numerator / denominator

    sse = 0.0

    for epoch in (1, 2):
        rr = [
            residuals[i]
            for i, row in enumerate(rows)
            if row["epoch"] == epoch
        ]

        sse += rr[0] ** 2

        for i in range(1, len(rr)):
            sse += (
                rr[i]
                - phi * rr[i - 1]
            ) ** 2

    return {
        "phi": phi,
        "sse": sse,
    }


def same_state_phi(rows, residuals, blocked):
    numerator = 0.0
    denominator = 0.0
    pairs = 0

    for epoch in (1, 2):
        indices = [
            i
            for i, row in enumerate(rows)
            if row["epoch"] == epoch
        ]

        for j in range(1, len(indices)):
            cur = indices[j]
            prev = indices[j - 1]

            same = (
                rows[cur]["blocked"] == blocked
                and rows[prev]["blocked"] == blocked
            )

            if not same:
                continue

            numerator += residuals[cur] * residuals[prev]
            denominator += residuals[prev] ** 2
            pairs += 1

    return {
        "phi": numerator / denominator,
        "pairs": pairs,
    }


def build_timing_rows(epochs):
    rows = []

    for epoch_i, epoch in enumerate(epochs, start=1):
        for i in range(len(epoch) - 1):
            cur = epoch[i]
            prev = epoch[i - 1] if i > 0 else None

            rows.append(
                {
                    "epoch": epoch_i,
                    "service_s": max(
                        cur["stream_latency_ms"],
                        cur["snapshot_latency_ms"],
                    ) / 1000.0,
                    "gap_s": (
                        epoch[i + 1]["t_rel_s"]
                        - cur["t_rel_s"]
                    ),
                    "blocked": int(
                        cur["state"] == "blocked"
                    ),
                    "reentry": int(
                        cur["state"] == "accessible"
                        and prev is not None
                        and prev["state"] == "blocked"
                    ),
                }
            )

    return rows


def label_epoch(epoch):
    labels = []

    for i, row in enumerate(epoch):
        if row["state"] == "blocked":
            labels.append("B")
        elif (
            i > 0
            and epoch[i - 1]["state"] == "blocked"
        ):
            labels.append("E")
        else:
            labels.append("H")

    return labels


def transition_counts(labels, mode):
    if mode == "AB":
        mapped = [
            "B" if x == "B" else "A"
            for x in labels
        ]
        states = ("A", "B")
    else:
        mapped = labels
        states = ("H", "E", "B")

    counts = {
        f"{a}->{b}": 0
        for a in states
        for b in states
    }

    for a, b in zip(mapped, mapped[1:]):
        counts[f"{a}->{b}"] += 1

    return counts


def posterior_means(train_counts, mode):
    if mode == "AB":
        a_to_b = train_counts["A->B"]
        a_to_a = train_counts["A->A"]
        b_to_a = train_counts["B->A"]
        b_to_b = train_counts["B->B"]

        return {
            "p_AB": (
                a_to_b + 0.5
            ) / (
                a_to_b + a_to_a + 1.0
            ),
            "p_BA": (
                b_to_a + 0.5
            ) / (
                b_to_a + b_to_b + 1.0
            ),
        }

    h_to_b = train_counts["H->B"]
    h_to_h = train_counts["H->H"]
    b_to_e = train_counts["B->E"]
    b_to_b = train_counts["B->B"]
    e_to_b = train_counts["E->B"]
    e_to_h = train_counts["E->H"]

    return {
        "p_HB": (
            h_to_b + 0.5
        ) / (
            h_to_b + h_to_h + 1.0
        ),
        "p_BE": (
            b_to_e + 0.5
        ) / (
            b_to_e + b_to_b + 1.0
        ),
        "p_EB": (
            e_to_b + 0.5
        ) / (
            e_to_b + e_to_h + 1.0
        ),
    }


def predictive_logloss(test_labels, model, mode):
    if mode == "AB":
        labels = [
            "B" if x == "B" else "A"
            for x in test_labels
        ]
    else:
        labels = test_labels

    loglik = 0.0

    for a, b in zip(labels, labels[1:]):
        if mode == "AB":
            if a == "A":
                p = (
                    model["p_AB"]
                    if b == "B"
                    else 1.0 - model["p_AB"]
                )
            else:
                p = (
                    model["p_BA"]
                    if b == "A"
                    else 1.0 - model["p_BA"]
                )
        else:
            if a == "H":
                p = (
                    model["p_HB"]
                    if b == "B"
                    else 1.0 - model["p_HB"]
                )
            elif a == "B":
                p = (
                    model["p_BE"]
                    if b == "E"
                    else 1.0 - model["p_BE"]
                )
            else:
                p = (
                    model["p_EB"]
                    if b == "B"
                    else 1.0 - model["p_EB"]
                )

        loglik += math.log(max(p, 1e-12))

    return -loglik / (len(labels) - 1)


def cross_epoch_transition_prediction(epochs):
    labels = [label_epoch(epoch) for epoch in epochs]
    output = []

    for train_i, test_i in ((0, 1), (1, 0)):
        train = labels[train_i]
        test = labels[test_i]

        ab_counts = transition_counts(train, "AB")
        heb_counts = transition_counts(train, "HEB")

        ab_model = posterior_means(
            ab_counts,
            "AB",
        )
        heb_model = posterior_means(
            heb_counts,
            "HEB",
        )

        output.append(
            {
                "train_epoch": train_i + 1,
                "test_epoch": test_i + 1,
                "AB_logloss": predictive_logloss(
                    test,
                    ab_model,
                    "AB",
                ),
                "HEB_logloss": predictive_logloss(
                    test,
                    heb_model,
                    "HEB",
                ),
                "AB_model": ab_model,
                "HEB_model": heb_model,
            }
        )

    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="data/paired_observations.csv",
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    epochs = split_epochs(load_rows(args.csv))
    rows = build_timing_rows(epochs)

    base = ols(rows, ["service_s"])
    controlled = ols(
        rows,
        [
            "service_s",
            "blocked",
            "epoch",
        ],
    )
    controlled_reentry = ols(
        rows,
        [
            "service_s",
            "blocked",
            "reentry",
            "epoch",
        ],
    )

    ar_base = residual_ar1(
        rows,
        base["residuals"],
    )
    ar_controlled = residual_ar1(
        rows,
        controlled["residuals"],
    )
    ar_controlled_reentry = residual_ar1(
        rows,
        controlled_reentry["residuals"],
    )

    def with_ar_bic(model, ar):
        k = 1 + len(model["features"])
        n = len(rows)

        return {
            "features": model["features"],
            "base_bic": model["bic"],
            "base_sse": model["sse"],
            "ar1_phi": ar["phi"],
            "ar1_sse": ar["sse"],
            "ar1_bic": (
                n * math.log(ar["sse"] / n)
                + (k + 1) * math.log(n)
            ),
        }

    result = {
        "timing_memory_after_controls": [
            with_ar_bic(base, ar_base),
            with_ar_bic(
                controlled,
                ar_controlled,
            ),
            with_ar_bic(
                controlled_reentry,
                ar_controlled_reentry,
            ),
        ],
        "same_state_memory_from_base_residuals": {
            "accessible": same_state_phi(
                rows,
                base["residuals"],
                0,
            ),
            "blocked": same_state_phi(
                rows,
                base["residuals"],
                1,
            ),
        },
        "cross_epoch_transition_prediction": (
            cross_epoch_transition_prediction(epochs)
        ),
        "guardrails": [
            "State/epoch controls are observational covariates, not causal interventions.",
            "Same-state residual memory reduces the chance that AR structure is only an A/B-switching artifact.",
            "There are only two active epochs, so cross-epoch prediction is replication within one capture, not population validation.",
        ],
    }

    text = json.dumps(
        result,
        indent=2,
        sort_keys=True,
    ) + "\n"

    if args.output:
        Path(args.output).write_text(
            text,
            encoding="utf-8",
        )
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
