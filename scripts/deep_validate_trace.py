#!/usr/bin/env python3
"""Deep validation of the published recovery trace.

This script performs sensitivity and posterior-predictive checks that do not
require any new production traffic:

- stream/snapshot pairing-window sensitivity;
- active-epoch gap sensitivity;
- timing-law residual dynamics and AR model competition;
- cross-epoch prediction of the cycle-time law;
- one-change-point detection vs first Blocked observation;
- permutation stress test for the change point;
- posterior-predictive check of the history-free A/B model;
- post-Blocked epoch morphology comparison;
- trace-preserving materialization accounting.

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from pathlib import Path

PAIR_WINDOWS_MS = [5, 10, 20, 50, 100, 250]
EPOCH_GAPS_S = [20, 30, 45, 60, 90, 120, 300, 600, 900]
DEFAULT_PAIR_WINDOW_S = 0.050
DEFAULT_EPOCH_GAP_S = 60.0


def load_events(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    rows.sort(key=lambda r: r["t_rel_s"])
    return rows


def load_pairs_csv(path):
    with Path(path).open("r", encoding="utf-8", newline="") as f:
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


def pair_events(events, window_s):
    streams = [e for e in events if e["event"] == "stream_status"]
    snaps = [
        e for e in events
        if e["event"] == "conversation_snapshot"
    ]

    used = set()
    pairs = []

    for stream in streams:
        best_i = None
        best_delta = None

        for i, snap in enumerate(snaps):
            if i in used:
                continue

            delta = abs(snap["t_rel_s"] - stream["t_rel_s"])

            if (
                delta <= window_s
                and (
                    best_delta is None
                    or delta < best_delta
                )
            ):
                best_i = i
                best_delta = delta

        if best_i is None:
            continue

        used.add(best_i)
        snap = snaps[best_i]

        if (
            stream["status"] == "200"
            and snap["status"] == "200"
        ):
            state = "accessible"
        elif (
            stream["status"] == "no_http_response"
            and snap["status"] == "429"
        ):
            state = "blocked"
        else:
            state = "mixed"

        pairs.append(
            {
                "t_rel_s": stream["t_rel_s"],
                "state": state,
                "pair_skew_ms": best_delta * 1000.0,
                "stream_latency_ms": stream["latency_ms"],
                "snapshot_latency_ms": snap["latency_ms"],
                "snapshot_payload_kib_rounded_4": (
                    snap.get("payload_kib_rounded_4")
                    or 0
                ),
            }
        )

    return pairs


def split_epochs(rows, gap_s=DEFAULT_EPOCH_GAP_S):
    epochs = []
    start = 0

    for i in range(len(rows) - 1):
        if (
            rows[i + 1]["t_rel_s"]
            - rows[i]["t_rel_s"]
            > gap_s
        ):
            epochs.append(rows[start : i + 1])
            start = i + 1

    epochs.append(rows[start:])
    return epochs


def transition_counts(rows, gap_s):
    counts = {
        "A->A": 0,
        "A->B": 0,
        "B->A": 0,
        "B->B": 0,
    }

    for cur, nxt in zip(rows, rows[1:]):
        gap = nxt["t_rel_s"] - cur["t_rel_s"]

        if gap > gap_s:
            continue

        a = "A" if cur["state"] == "accessible" else "B"
        b = "A" if nxt["state"] == "accessible" else "B"
        counts[f"{a}->{b}"] += 1

    a_out = counts["A->A"] + counts["A->B"]
    b_out = counts["B->A"] + counts["B->B"]

    return {
        **counts,
        "p_B_given_A": counts["A->B"] / a_out,
        "p_B_given_B": counts["B->B"] / b_out,
        "transitions": a_out + b_out,
    }


def transitions_from_epochs(epochs):
    out = []

    for epoch_i, epoch in enumerate(epochs, start=1):
        for i in range(len(epoch) - 1):
            cur = epoch[i]
            nxt = epoch[i + 1]

            service = max(
                cur["stream_latency_ms"],
                cur["snapshot_latency_ms"],
            ) / 1000.0

            gap = nxt["t_rel_s"] - cur["t_rel_s"]

            out.append(
                {
                    "epoch": epoch_i,
                    "index": i,
                    "service_s": service,
                    "gap_s": gap,
                    "wait_s": gap - service,
                }
            )

    return out


def fit_linear(rows):
    n = len(rows)
    sx = sum(r["service_s"] for r in rows)
    sy = sum(r["gap_s"] for r in rows)
    sxx = sum(
        r["service_s"] ** 2
        for r in rows
    )
    sxy = sum(
        r["service_s"] * r["gap_s"]
        for r in rows
    )

    denom = n * sxx - sx * sx
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n

    residuals = [
        r["gap_s"]
        - (
            intercept
            + slope * r["service_s"]
        )
        for r in rows
    ]

    sse = sum(x * x for x in residuals)
    sigma2 = sse / n

    return {
        "intercept": intercept,
        "slope": slope,
        "sse": sse,
        "sigma2": sigma2,
        "residuals": residuals,
    }


def solve_linear(a, b):
    n = len(b)
    m = [
        [*a[i], b[i]]
        for i in range(n)
    ]

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


def fit_ar_residuals(transitions, residuals, order):
    by_epoch = {}

    for row, residual in zip(transitions, residuals):
        by_epoch.setdefault(
            row["epoch"],
            [],
        ).append(residual)

    if order == 0:
        total_sse = sum(
            r * r
            for r in residuals
        )

        bic = (
            len(residuals)
            * math.log(total_sse / len(residuals))
            + 2 * math.log(len(residuals))
        )

        return {
            "order": 0,
            "phi": [],
            "total_sse": total_sse,
            "bic": bic,
        }

    x = []
    y = []

    for values in by_epoch.values():
        for i in range(order, len(values)):
            x.append(
                [
                    values[i - j - 1]
                    for j in range(order)
                ]
            )
            y.append(values[i])

    xtx = [
        [0.0] * order
        for _ in range(order)
    ]
    xty = [0.0] * order

    for row, target in zip(x, y):
        for i in range(order):
            xty[i] += row[i] * target

            for j in range(order):
                xtx[i][j] += row[i] * row[j]

    phi = solve_linear(xtx, xty)

    total_sse = 0.0

    for values in by_epoch.values():
        for i in range(min(order, len(values))):
            total_sse += values[i] ** 2

        for i in range(order, len(values)):
            pred = sum(
                phi[j] * values[i - j - 1]
                for j in range(order)
            )
            total_sse += (values[i] - pred) ** 2

    parameter_count = 2 + order

    bic = (
        len(residuals)
        * math.log(total_sse / len(residuals))
        + parameter_count
        * math.log(len(residuals))
    )

    return {
        "order": order,
        "phi": phi,
        "total_sse": total_sse,
        "bic": bic,
    }


def lag1_wait_phi(transitions):
    by_epoch = {}

    for row in transitions:
        by_epoch.setdefault(
            row["epoch"],
            [],
        ).append(row["wait_s"])

    mean_wait = statistics.fmean(
        row["wait_s"]
        for row in transitions
    )

    numerator = 0.0
    denominator = 0.0

    for values in by_epoch.values():
        centered = [
            v - mean_wait
            for v in values
        ]

        for i in range(1, len(centered)):
            numerator += (
                centered[i]
                * centered[i - 1]
            )
            denominator += centered[i - 1] ** 2

    return {
        "mean_wait_s": mean_wait,
        "ar1_phi": numerator / denominator,
    }


def evaluate_linear(model, rows):
    errors = [
        row["gap_s"]
        - (
            model["intercept"]
            + model["slope"] * row["service_s"]
        )
        for row in rows
    ]

    rmse = math.sqrt(
        statistics.fmean(
            e * e
            for e in errors
        )
    )

    loglik = sum(
        -0.5
        * (
            math.log(
                2.0
                * math.pi
                * model["sigma2"]
            )
            + e * e / model["sigma2"]
        )
        for e in errors
    )

    return {
        "n": len(rows),
        "rmse_s": rmse,
        "mean_error_s": statistics.fmean(errors),
        "logloss": -loglik / len(rows),
    }


def best_one_change_point(values, min_segment=5):
    mean_all = statistics.fmean(values)
    sse0 = sum(
        (x - mean_all) ** 2
        for x in values
    )

    best = None

    for cp in range(
        min_segment,
        len(values) - min_segment + 1,
    ):
        left = values[:cp]
        right = values[cp:]

        mean_left = statistics.fmean(left)
        mean_right = statistics.fmean(right)

        sse = (
            sum(
                (x - mean_left) ** 2
                for x in left
            )
            + sum(
                (x - mean_right) ** 2
                for x in right
            )
        )

        reduction = 1.0 - sse / sse0

        candidate = {
            "cp_index": cp,
            "sse": sse,
            "sse0": sse0,
            "sse_reduction_fraction": reduction,
            "mean_before_s": mean_left,
            "mean_after_s": mean_right,
        }

        if (
            best is None
            or candidate["sse"] < best["sse"]
        ):
            best = candidate

    return best


def change_point_permutation(
    values,
    first_blocked_index,
    trials,
    seed,
):
    observed = best_one_change_point(values)
    rng = random.Random(seed)

    ge_reduction = 0
    same_cp = 0
    both = 0

    for _ in range(trials):
        permuted = values[:]
        rng.shuffle(permuted)
        result = best_one_change_point(permuted)

        if (
            result["sse_reduction_fraction"]
            >= observed["sse_reduction_fraction"]
        ):
            ge_reduction += 1

        if result["cp_index"] == first_blocked_index:
            same_cp += 1

        if (
            result["cp_index"] == first_blocked_index
            and result["sse_reduction_fraction"]
            >= observed["sse_reduction_fraction"]
        ):
            both += 1

    # Add-one correction prevents zero Monte Carlo p-values.
    return {
        "observed": observed,
        "permutation_trials": trials,
        "p_max_reduction_ge_observed": (
            ge_reduction + 1
        ) / (trials + 1),
        "p_best_cp_equals_first_blocked": (
            same_cp + 1
        ) / (trials + 1),
        "p_both": (
            both + 1
        ) / (trials + 1),
    }


def posterior_predictive_all_reentry_blocked():
    # History-free A-origin transition probability with Jeffreys prior:
    # p_AB | data ~ Beta(10.5, 38.5).
    a = 10.5
    b = 38.5

    probability = 1.0

    for j in range(8):
        probability *= (
            a + j
        ) / (
            a + b + j
        )

    return {
        "model": "p_AB ~ Beta(10.5, 38.5)",
        "event": (
            "all eight Accessible observations immediately after Blocked "
            "are followed by Blocked"
        ),
        "probability": probability,
    }


def hypergeom_overlap_tail(
    total_positions,
    first_count,
    second_count,
    observed_overlap,
):
    denominator = math.comb(
        total_positions,
        second_count,
    )

    probability = 0.0

    for overlap in range(
        observed_overlap,
        min(first_count, second_count) + 1,
    ):
        remaining = second_count - overlap

        if remaining > total_positions - first_count:
            continue

        probability += (
            math.comb(first_count, overlap)
            * math.comb(
                total_positions - first_count,
                remaining,
            )
            / denominator
        )

    return probability


def epoch_morphology(epochs):
    sequences = []

    for epoch_i, epoch in enumerate(epochs, start=1):
        first_blocked = next(
            i
            for i, row in enumerate(epoch)
            if row["state"] == "blocked"
        )

        tail = epoch[first_blocked:]
        sequence = "".join(
            "A" if row["state"] == "accessible" else "B"
            for row in tail
        )

        a_positions = [
            i
            for i, char in enumerate(sequence)
            if char == "A"
        ]

        sequences.append(
            {
                "epoch": epoch_i,
                "length": len(sequence),
                "sequence": sequence,
                "a_positions": a_positions,
                "a_count": len(a_positions),
                "b_count": sequence.count("B"),
            }
        )

    first = sequences[0]
    second = sequences[1]

    exact_matches = sum(
        a == b
        for a, b in zip(
            first["sequence"],
            second["sequence"],
        )
    )

    overlap = len(
        set(first["a_positions"])
        & set(second["a_positions"])
    )

    return {
        "epochs": sequences,
        "exact_symbol_matches": exact_matches,
        "match_fraction": (
            exact_matches
            / min(
                first["length"],
                second["length"],
            )
        ),
        "a_position_overlap": overlap,
        "random_4_of_34_overlap_tail": hypergeom_overlap_tail(
            34,
            4,
            4,
            overlap,
        ),
        "guardrail": (
            "The two post-Blocked epochs are morphologically similar, "
            "but the A-position overlap test is only suggestive."
        ),
    }


def trace_replay(epochs, probe_kib=4.0):
    snapshot_kib = 4684.0

    total_actual_kib = 0.0
    total_probe_kib = 0.0
    total_materializations = 0
    details = []

    for epoch_i, epoch in enumerate(epochs, start=1):
        first_blocked = next(
            i
            for i, row in enumerate(epoch)
            if row["state"] == "blocked"
        )

        tail = epoch[first_blocked:]
        accessible = sum(
            row["state"] == "accessible"
            for row in tail
        )

        actual_kib = accessible * snapshot_kib

        consecutive_accessible = 0
        materializations = 0

        for row in tail:
            if row["state"] == "accessible":
                consecutive_accessible += 1
            else:
                consecutive_accessible = 0

            if consecutive_accessible >= 2:
                materializations += 1
                consecutive_accessible = 0

        probe_total = len(tail) * probe_kib
        counterfactual_kib = (
            probe_total
            + materializations * snapshot_kib
        )

        total_actual_kib += actual_kib
        total_probe_kib += counterfactual_kib
        total_materializations += materializations

        details.append(
            {
                "epoch": epoch_i,
                "observations_from_first_blocked": len(tail),
                "accessible_observations": accessible,
                "actual_success_snapshot_mib": actual_kib / 1024.0,
                "stable_2A_materializations": materializations,
                "probe_plus_materialization_mib": counterfactual_kib / 1024.0,
            }
        )

    return {
        "probe_kib_assumption": probe_kib,
        "details": details,
        "actual_success_snapshot_mib": total_actual_kib / 1024.0,
        "replay_payload_mib": total_probe_kib / 1024.0,
        "payload_reduction_fraction": (
            1.0
            - total_probe_kib / total_actual_kib
        ),
        "full_materializations": total_materializations,
        "guardrail": (
            "Trace-preserving accounting only. Suppressing real requests "
            "could change the server/client state trajectory."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--events",
        default="data/session_b_events.jsonl",
    )
    parser.add_argument(
        "--pairs",
        default="data/paired_observations.csv",
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=20000,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0x51C0FFEE,
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    events = load_events(args.events)
    public_pairs = load_pairs_csv(args.pairs)

    pairing_sensitivity = {}

    for window_ms in PAIR_WINDOWS_MS:
        pairs = pair_events(
            events,
            window_ms / 1000.0,
        )

        pairing_sensitivity[str(window_ms)] = {
            "total": len(pairs),
            "accessible": sum(
                p["state"] == "accessible"
                for p in pairs
            ),
            "blocked": sum(
                p["state"] == "blocked"
                for p in pairs
            ),
            "mixed": sum(
                p["state"] == "mixed"
                for p in pairs
            ),
            "max_pair_skew_ms": (
                max(
                    p["pair_skew_ms"]
                    for p in pairs
                )
                if pairs
                else None
            ),
        }

    epoch_gap_sensitivity = {
        str(gap): transition_counts(
            public_pairs,
            gap,
        )
        for gap in EPOCH_GAPS_S
    }

    epochs = split_epochs(public_pairs)
    transitions = transitions_from_epochs(epochs)

    linear = fit_linear(transitions)

    ar_models = [
        fit_ar_residuals(
            transitions,
            linear["residuals"],
            order,
        )
        for order in range(5)
    ]

    best_ar = min(
        ar_models,
        key=lambda row: row["bic"],
    )

    wait_dynamics = lag1_wait_phi(transitions)

    epoch_transitions = [
        [
            row
            for row in transitions
            if row["epoch"] == epoch_i
        ]
        for epoch_i in (1, 2)
    ]

    fit_epoch1 = fit_linear(epoch_transitions[0])
    fit_epoch2 = fit_linear(epoch_transitions[1])

    cross_epoch = {
        "fit_epoch1_test_epoch2": {
            "fit": {
                "intercept": fit_epoch1["intercept"],
                "slope": fit_epoch1["slope"],
                "sigma2": fit_epoch1["sigma2"],
            },
            "test": evaluate_linear(
                fit_epoch1,
                epoch_transitions[1],
            ),
        },
        "fit_epoch2_test_epoch1": {
            "fit": {
                "intercept": fit_epoch2["intercept"],
                "slope": fit_epoch2["slope"],
                "sigma2": fit_epoch2["sigma2"],
            },
            "test": evaluate_linear(
                fit_epoch2,
                epoch_transitions[0],
            ),
        },
    }

    change_points = []

    for epoch_i, epoch in enumerate(epochs, start=1):
        first_blocked = next(
            i
            for i, row in enumerate(epoch)
            if row["state"] == "blocked"
        )

        service = [
            max(
                row["stream_latency_ms"],
                row["snapshot_latency_ms"],
            ) / 1000.0
            for row in epoch
        ]

        result = change_point_permutation(
            service,
            first_blocked,
            args.permutations,
            args.seed + epoch_i,
        )

        result["epoch"] = epoch_i
        result["first_blocked_index"] = first_blocked
        result["change_point_matches_first_blocked"] = (
            result["observed"]["cp_index"]
            == first_blocked
        )

        change_points.append(result)

    result = {
        "pairing_window_sensitivity": pairing_sensitivity,
        "epoch_gap_sensitivity": epoch_gap_sensitivity,
        "timing_model": {
            "base_linear": {
                "intercept_s": linear["intercept"],
                "service_coefficient": linear["slope"],
                "sse": linear["sse"],
            },
            "ar_residual_competition": ar_models,
            "best_bic_model": best_ar,
            "wait_dynamics": wait_dynamics,
            "cross_epoch_prediction": cross_epoch,
        },
        "change_points": change_points,
        "posterior_predictive_history_free_markov": (
            posterior_predictive_all_reentry_blocked()
        ),
        "epoch_morphology": epoch_morphology(epochs),
        "trace_preserving_replay": trace_replay(epochs),
        "guardrails": [
            "Sensitivity checks do not identify OpenAI internals.",
            "AR residual structure is evidence of remaining temporal dependence, not proof of a particular scheduler implementation.",
            "Change-point tests use the same observed trace and should be replicated on independent captures.",
            "Trace replay holds the observed state sequence fixed and is accounting, not a causal production estimate.",
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
