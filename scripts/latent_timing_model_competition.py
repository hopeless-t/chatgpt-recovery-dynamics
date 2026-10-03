#!/usr/bin/env python3
"""Compete residual-timing models without naming a physical mechanism.

Candidates:
- IID Gaussian residuals;
- observed A/B-conditioned Gaussian residuals;
- AR(1) continuous one-step memory;
- two-state Gaussian HMM latent regime.

The script uses the existing sanitized paired-observation trace only.
No production traffic is generated.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

from deep_validate_trace import (
    fit_linear,
    load_pairs_csv,
    split_epochs,
    transitions_from_epochs,
)

EPS = 1e-12


def logsumexp(values: list[float]) -> float:
    m = max(values)
    return m + math.log(sum(math.exp(v - m) for v in values))


def gaussian_logpdf(x: float, mean: float, var: float) -> float:
    var = max(var, 1e-9)
    return -0.5 * (math.log(2.0 * math.pi * var) + (x - mean) ** 2 / var)


def residuals(model: dict[str, float], rows: list[dict[str, Any]]) -> list[float]:
    return [
        row["gap_s"] - (model["intercept"] + model["slope"] * row["service_s"])
        for row in rows
    ]


def group_residuals_by_epoch(
    transitions: list[dict[str, Any]],
    values: list[float],
) -> list[list[float]]:
    out: dict[int, list[float]] = {}
    for row, value in zip(transitions, values):
        out.setdefault(row["epoch"], []).append(value)
    return [out[k] for k in sorted(out)]


def transition_states(epochs: list[list[dict[str, Any]]]) -> list[str]:
    states: list[str] = []
    for epoch in epochs:
        for cur in epoch[:-1]:
            states.append("A" if cur["state"] == "accessible" else "B")
    return states


def fit_iid(sequences: list[list[float]]) -> dict[str, Any]:
    values = [x for seq in sequences for x in seq]
    mean = statistics.fmean(values)
    var = statistics.fmean((x - mean) ** 2 for x in values)
    var = max(var, 1e-9)
    ll = sum(gaussian_logpdf(x, mean, var) for x in values)
    return {"mean": mean, "var": var, "log_likelihood": ll, "dynamic_params": 2}


def iid_loglik(sequences: list[list[float]], model: dict[str, Any]) -> float:
    return sum(
        gaussian_logpdf(x, model["mean"], model["var"])
        for seq in sequences
        for x in seq
    )


def fit_state_conditioned(
    values: list[float],
    states: list[str],
) -> dict[str, Any]:
    params = {}
    ll = 0.0
    for state in ("A", "B"):
        xs = [x for x, s in zip(values, states) if s == state]
        mean = statistics.fmean(xs)
        var = max(statistics.fmean((x - mean) ** 2 for x in xs), 1e-9)
        params[state] = {"mean": mean, "var": var, "n": len(xs)}
        ll += sum(gaussian_logpdf(x, mean, var) for x in xs)
    return {"states": params, "log_likelihood": ll, "dynamic_params": 4}


def state_conditioned_loglik(
    values: list[float],
    states: list[str],
    model: dict[str, Any],
) -> float:
    return sum(
        gaussian_logpdf(
            x,
            model["states"][state]["mean"],
            model["states"][state]["var"],
        )
        for x, state in zip(values, states)
    )


def fit_ar1(sequences: list[list[float]]) -> dict[str, Any]:
    xs = []
    ys = []
    for seq in sequences:
        for prev, cur in zip(seq, seq[1:]):
            xs.append(prev)
            ys.append(cur)

    xbar = statistics.fmean(xs)
    ybar = statistics.fmean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    phi = (
        sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
        if denom > EPS
        else 0.0
    )
    phi = max(-0.98, min(0.98, phi))
    intercept = ybar - phi * xbar
    innovations = [y - (intercept + phi * x) for x, y in zip(xs, ys)]
    var = max(statistics.fmean(e * e for e in innovations), 1e-9)

    ll = ar1_loglik(
        sequences,
        {"intercept": intercept, "phi": phi, "var": var},
    )
    return {
        "intercept": intercept,
        "phi": phi,
        "var": var,
        "log_likelihood": ll,
        "dynamic_params": 3,
    }


def ar1_loglik(sequences: list[list[float]], model: dict[str, Any]) -> float:
    c = model["intercept"]
    phi = model["phi"]
    var = model["var"]
    stationary_mean = c / (1.0 - phi)
    stationary_var = var / max(1.0 - phi * phi, 1e-6)

    ll = 0.0
    for seq in sequences:
        if not seq:
            continue
        ll += gaussian_logpdf(seq[0], stationary_mean, stationary_var)
        for prev, cur in zip(seq, seq[1:]):
            ll += gaussian_logpdf(cur, c + phi * prev, var)
    return ll


def quantile(values: list[float], p: float) -> float:
    xs = sorted(values)
    pos = p * (len(xs) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1.0 - w) + xs[hi] * w


def hmm_forward_loglik(
    sequence: list[float],
    params: dict[str, Any],
) -> float:
    pi = params["pi"]
    a = params["transition"]
    means = params["means"]
    vars_ = params["vars"]

    alpha = [
        math.log(max(pi[j], EPS)) + gaussian_logpdf(sequence[0], means[j], vars_[j])
        for j in range(2)
    ]
    for x in sequence[1:]:
        nxt = []
        for j in range(2):
            nxt.append(
                gaussian_logpdf(x, means[j], vars_[j])
                + logsumexp([
                    alpha[i] + math.log(max(a[i][j], EPS))
                    for i in range(2)
                ])
            )
        alpha = nxt
    return logsumexp(alpha)


def hmm_loglik(sequences: list[list[float]], params: dict[str, Any]) -> float:
    return sum(hmm_forward_loglik(seq, params) for seq in sequences if seq)


def e_step(
    sequence: list[float],
    params: dict[str, Any],
) -> tuple[float, list[list[float]], list[list[list[float]]]]:
    pi = params["pi"]
    a = params["transition"]
    means = params["means"]
    vars_ = params["vars"]
    n = len(sequence)

    emit = [
        [gaussian_logpdf(x, means[j], vars_[j]) for j in range(2)]
        for x in sequence
    ]
    alpha = [[0.0, 0.0] for _ in range(n)]
    beta = [[0.0, 0.0] for _ in range(n)]

    for j in range(2):
        alpha[0][j] = math.log(max(pi[j], EPS)) + emit[0][j]

    for t in range(1, n):
        for j in range(2):
            alpha[t][j] = emit[t][j] + logsumexp([
                alpha[t - 1][i] + math.log(max(a[i][j], EPS))
                for i in range(2)
            ])

    ll = logsumexp(alpha[-1])

    for t in range(n - 2, -1, -1):
        for i in range(2):
            beta[t][i] = logsumexp([
                math.log(max(a[i][j], EPS))
                + emit[t + 1][j]
                + beta[t + 1][j]
                for j in range(2)
            ])

    gamma = [[0.0, 0.0] for _ in range(n)]
    for t in range(n):
        norm = logsumexp([alpha[t][j] + beta[t][j] for j in range(2)])
        for j in range(2):
            gamma[t][j] = math.exp(alpha[t][j] + beta[t][j] - norm)

    xi: list[list[list[float]]] = []
    for t in range(n - 1):
        raw = [
            [
                alpha[t][i]
                + math.log(max(a[i][j], EPS))
                + emit[t + 1][j]
                + beta[t + 1][j]
                for j in range(2)
            ]
            for i in range(2)
        ]
        norm = logsumexp([raw[i][j] for i in range(2) for j in range(2)])
        xi.append([
            [math.exp(raw[i][j] - norm) for j in range(2)]
            for i in range(2)
        ])

    return ll, gamma, xi


def fit_hmm2(
    sequences: list[list[float]],
    *,
    max_iter: int = 300,
    tol: float = 1e-9,
) -> dict[str, Any]:
    values = [x for seq in sequences for x in seq]
    global_var = max(statistics.pvariance(values), 1e-6)
    var_floor = max(global_var * 0.02, 1e-6)

    starts = []
    for qlo, qhi in ((0.2, 0.8), (0.3, 0.7), (0.1, 0.9)):
        for persistence in (0.60, 0.80, 0.95):
            starts.append({
                "pi": [0.5, 0.5],
                "transition": [
                    [persistence, 1.0 - persistence],
                    [1.0 - persistence, persistence],
                ],
                "means": [quantile(values, qlo), quantile(values, qhi)],
                "vars": [global_var, global_var],
            })

    best = None

    for initial in starts:
        params = json.loads(json.dumps(initial))
        last_ll = float("-inf")

        for iteration in range(max_iter):
            seq_stats = [e_step(seq, params) for seq in sequences if seq]
            ll = sum(item[0] for item in seq_stats)

            pi_num = [0.0, 0.0]
            trans_num = [[0.0, 0.0], [0.0, 0.0]]
            trans_den = [0.0, 0.0]
            weight = [0.0, 0.0]
            weighted_sum = [0.0, 0.0]

            for seq, (_, gamma, xi) in zip(
                [seq for seq in sequences if seq],
                seq_stats,
            ):
                for j in range(2):
                    pi_num[j] += gamma[0][j]
                for t, x in enumerate(seq):
                    for j in range(2):
                        weight[j] += gamma[t][j]
                        weighted_sum[j] += gamma[t][j] * x
                for t in range(len(seq) - 1):
                    for i in range(2):
                        trans_den[i] += gamma[t][i]
                        for j in range(2):
                            trans_num[i][j] += xi[t][i][j]

            new_means = [
                weighted_sum[j] / max(weight[j], EPS)
                for j in range(2)
            ]
            new_vars = [0.0, 0.0]
            for seq, (_, gamma, _) in zip(
                [seq for seq in sequences if seq],
                seq_stats,
            ):
                for t, x in enumerate(seq):
                    for j in range(2):
                        new_vars[j] += gamma[t][j] * (x - new_means[j]) ** 2
            new_vars = [
                max(new_vars[j] / max(weight[j], EPS), var_floor)
                for j in range(2)
            ]

            nseq = len(seq_stats)
            new_pi = [max(pi_num[j] / nseq, 1e-4) for j in range(2)]
            s = sum(new_pi)
            new_pi = [x / s for x in new_pi]

            new_a = []
            for i in range(2):
                row = [
                    max(trans_num[i][j] / max(trans_den[i], EPS), 1e-4)
                    for j in range(2)
                ]
                rs = sum(row)
                new_a.append([x / rs for x in row])

            params = {
                "pi": new_pi,
                "transition": new_a,
                "means": new_means,
                "vars": new_vars,
            }

            if abs(ll - last_ll) < tol:
                break
            last_ll = ll

        final_ll = hmm_loglik(sequences, params)
        candidate = {
            **params,
            "log_likelihood": final_ll,
            "dynamic_params": 7,
            "iterations": iteration + 1,
            "variance_floor": var_floor,
        }
        if best is None or candidate["log_likelihood"] > best["log_likelihood"]:
            best = candidate

    assert best is not None

    # Canonicalize labels by increasing emission mean for readable output.
    if best["means"][0] > best["means"][1]:
        best["pi"] = [best["pi"][1], best["pi"][0]]
        best["means"] = [best["means"][1], best["means"][0]]
        best["vars"] = [best["vars"][1], best["vars"][0]]
        a = best["transition"]
        best["transition"] = [[a[1][1], a[1][0]], [a[0][1], a[0][0]]]

    return best


def bic(log_likelihood: float, n: int, dynamic_params: int) -> float:
    # +2 common cycle-law parameters. Including them changes absolute BIC only,
    # not the ordering among residual candidates.
    k = dynamic_params + 2
    return k * math.log(n) - 2.0 * log_likelihood


def model_table(
    transitions: list[dict[str, Any]],
    epochs: list[list[dict[str, Any]]],
    cycle_model: dict[str, Any],
) -> dict[str, Any]:
    vals = residuals(cycle_model, transitions)
    seqs = group_residuals_by_epoch(transitions, vals)
    states = transition_states(epochs)
    n = len(vals)

    iid = fit_iid(seqs)
    observed_state = fit_state_conditioned(vals, states)
    ar1 = fit_ar1(seqs)
    hmm = fit_hmm2(seqs)

    models = {
        "iid_gaussian": iid,
        "observed_ab_conditioned": observed_state,
        "ar1": ar1,
        "hmm2_latent_gaussian": hmm,
    }
    for model in models.values():
        model["bic"] = bic(
            model["log_likelihood"],
            n,
            model["dynamic_params"],
        )
        model["mean_nll"] = -model["log_likelihood"] / n

    ranking = sorted(
        (
            {"model": name, "bic": row["bic"], "mean_nll": row["mean_nll"]}
            for name, row in models.items()
        ),
        key=lambda row: row["bic"],
    )
    return {
        "n": n,
        "cycle_law": {
            "intercept_s": cycle_model["intercept"],
            "service_coefficient": cycle_model["slope"],
        },
        "models": models,
        "bic_ranking": ranking,
    }


def cross_epoch(
    epochs: list[list[dict[str, Any]]],
    transitions: list[dict[str, Any]],
) -> dict[str, Any]:
    by_epoch = {
        epoch_i: [r for r in transitions if r["epoch"] == epoch_i]
        for epoch_i in (1, 2)
    }
    states_by_epoch = {
        epoch_i: transition_states([epochs[epoch_i - 1]])
        for epoch_i in (1, 2)
    }

    out = {}
    for train_i, test_i in ((1, 2), (2, 1)):
        train_rows = by_epoch[train_i]
        test_rows = by_epoch[test_i]
        cycle = fit_linear(train_rows)
        train_vals = residuals(cycle, train_rows)
        test_vals = residuals(cycle, test_rows)
        train_seqs = [train_vals]
        test_seqs = [test_vals]

        iid = fit_iid(train_seqs)
        ar1 = fit_ar1(train_seqs)
        hmm = fit_hmm2(train_seqs)
        observed_state = fit_state_conditioned(
            train_vals,
            states_by_epoch[train_i],
        )

        scores = {
            "iid_gaussian": -iid_loglik(test_seqs, iid) / len(test_vals),
            "observed_ab_conditioned": -state_conditioned_loglik(
                test_vals,
                states_by_epoch[test_i],
                observed_state,
            ) / len(test_vals),
            "ar1": -ar1_loglik(test_seqs, ar1) / len(test_vals),
            "hmm2_latent_gaussian": -hmm_loglik(test_seqs, hmm) / len(test_vals),
        }
        out[f"train_epoch{train_i}_test_epoch{test_i}"] = {
            "n_train": len(train_vals),
            "n_test": len(test_vals),
            "cycle_law_fit": {
                "intercept_s": cycle["intercept"],
                "service_coefficient": cycle["slope"],
            },
            "test_mean_nll": scores,
            "ranking": sorted(scores, key=scores.get),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="data/paired_observations.csv")
    ap.add_argument("--output")
    args = ap.parse_args()

    pairs = load_pairs_csv(args.pairs)
    epochs = split_epochs(pairs)
    transitions = transitions_from_epochs(epochs)
    cycle = fit_linear(transitions)

    within = model_table(transitions, epochs, cycle)
    cross = cross_epoch(epochs, transitions)

    result = {
        "schema": "latent-timing-model-competition/v1",
        "evidence_class": "within_capture_model_competition",
        "within_capture": within,
        "cross_epoch_prediction": cross,
        "interpretation_rules": [
            "Lower BIC is descriptive model preference within this capture, not mechanism identification.",
            "Lower cross-epoch mean NLL is stronger evidence of portable predictive structure within this capture.",
            "A latent HMM state, if supported, must not be named as a scheduler/timer/backend state without independent evidence.",
            "AR(1) support means one-step predictive memory is useful; it does not identify its physical source.",
            "Observed A/B-conditioned Gaussian is a control for state-regime confounding, not a causal model.",
        ],
        "external_validity": "NOT_ESTABLISHED: only two active epochs from one capture are available.",
    }

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
