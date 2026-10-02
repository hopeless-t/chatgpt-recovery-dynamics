#!/usr/bin/env python3
"""Robust Monte Carlo stress test for conversation recovery policies.

This is a design stress test, not an estimator of OpenAI's internal behavior.
It uses the sanitized paired-observation CSV plus deliberately different causal
models so a policy can be tested against model uncertainty.

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

SESSION_GAP_S = 60.0

COMPLETED_BLOCKED_RUN_DURATIONS_S = [
    17.995,
    38.995,
    47.996,
    43.019,
    11.821,
    45.995,
    42.014,
    43.005,
]

POLICIES = {
    "baseline": {
        "min_period": 0.0,
        "backoff_after": 10**9,
        "base_backoff": 0.0,
        "factor": 1.0,
        "cap": 0.0,
        "jitter": 0.0,
    },
    "anchor_10s": {
        "min_period": 10.0,
        "backoff_after": 10**9,
        "base_backoff": 0.0,
        "factor": 1.0,
        "cap": 0.0,
        "jitter": 0.0,
    },
    "moderate_backoff": {
        "min_period": 10.0,
        "backoff_after": 2,
        "base_backoff": 8.0,
        "factor": 1.5,
        "cap": 30.0,
        "jitter": 0.20,
    },
    "strong_backoff": {
        "min_period": 10.0,
        "backoff_after": 2,
        "base_backoff": 8.0,
        "factor": 2.0,
        "cap": 60.0,
        "jitter": 0.20,
    },
}


def quantile(values, q):
    xs = sorted(values)
    z = (len(xs) - 1) * q
    lo = math.floor(z)
    hi = math.ceil(z)
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (z - lo)


def describe(values):
    return {
        "mean": statistics.fmean(values),
        "p50": quantile(values, 0.50),
        "p90": quantile(values, 0.90),
        "p95": quantile(values, 0.95),
    }


def load_transitions(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        for key in (
            "t_rel_s",
            "stream_latency_ms",
            "snapshot_latency_ms",
        ):
            row[key] = float(row[key])

    transitions = []
    for cur, nxt in zip(rows, rows[1:]):
        gap = nxt["t_rel_s"] - cur["t_rel_s"]
        if gap > SESSION_GAP_S:
            continue

        service = max(
            cur["stream_latency_ms"],
            cur["snapshot_latency_ms"],
        ) / 1000.0

        transitions.append(
            {
                "state": cur["state"],
                "next": nxt["state"],
                "gap": gap,
                "service": service,
                "wait": gap - service,
            }
        )

    service = {"accessible": [], "blocked": []}
    waits = {"accessible": [], "blocked": []}

    for row in transitions:
        service[row["state"]].append(row["service"])
        waits[row["state"]].append(row["wait"])

    return transitions, service, waits


def gap_for(policy, state, blocked_run, service, wait, rng):
    gap = max(service + wait, policy["min_period"])

    if state == "blocked" and blocked_run >= policy["backoff_after"]:
        exp = blocked_run - policy["backoff_after"]
        delay = min(
            policy["cap"],
            policy["base_backoff"] * policy["factor"] ** exp,
        )
        delay *= 1.0 + policy["jitter"] * (2.0 * rng.random() - 1.0)
        gap = max(gap, service + delay)

    return gap


def beta_posterior(rng, successes, failures):
    # Jeffreys prior Beta(1/2, 1/2)
    return rng.betavariate(successes + 0.5, failures + 0.5)


def simulate_attempt_driven(policy, service, waits, seed):
    """Adverse model for backoff: recovery progresses per observation attempt.

    Spacing attempts cannot make the latent state clear sooner; it can only
    delay discovery. Transition probabilities are sampled from the observed
    active-epoch counts using Jeffreys beta posteriors.
    """

    rng = random.Random(seed)

    p_bb = beta_posterior(rng, 50, 8)
    p_ab = beta_posterior(rng, 10, 38)

    state = "blocked"
    t = 0.0
    attempts = 0
    blocked_attempts = 0
    blocked_run = 1
    accessible_run = 0

    while t < 1200.0 and attempts < 200:
        attempts += 1
        if state == "blocked":
            blocked_attempts += 1

        s = rng.choice(service[state])
        w = rng.choice(waits[state])
        gap = gap_for(policy, state, blocked_run, s, w, rng)

        if state == "blocked":
            next_state = "blocked" if rng.random() < p_bb else "accessible"
        else:
            next_state = "blocked" if rng.random() < p_ab else "accessible"

        if next_state == "accessible":
            accessible_run += 1
            blocked_run = 0
        else:
            accessible_run = 0
            blocked_run = blocked_run + 1 if state == "blocked" else 1

        t += gap
        state = next_state

        # Hysteresis: one accessible excursion is not enough.
        if accessible_run >= 2:
            return {
                "recovered": True,
                "time_s": t,
                "attempts": attempts,
                "blocked_attempts": blocked_attempts,
            }

    return {
        "recovered": False,
        "time_s": 1200.0,
        "attempts": attempts,
        "blocked_attempts": blocked_attempts,
    }


def simulate_latent_wallclock(policy, service, waits, seed):
    """Model where the blocked condition clears in wall-clock time.

    The latent duration is bootstrapped from completed blocked runs and then
    multiplicatively perturbed. Retry timing changes detection delay but does
    not change the underlying clear time.
    """

    rng = random.Random(seed)

    base_duration = rng.choice(COMPLETED_BLOCKED_RUN_DURATIONS_S)
    duration = base_duration * math.exp(0.30 * rng.normalvariate(0.0, 1.0))

    t = 0.0
    attempts = 0
    blocked_attempts = 0
    blocked_run = 1

    while t < 600.0 and attempts < 100:
        attempts += 1

        if t >= duration:
            return {
                "recovered": True,
                "time_s": t,
                "detection_delay_s": t - duration,
                "attempts": attempts,
                "blocked_attempts": blocked_attempts,
            }

        blocked_attempts += 1

        s = rng.choice(service["blocked"])
        w = rng.choice(waits["blocked"])
        t += gap_for(policy, "blocked", blocked_run, s, w, rng)
        blocked_run += 1

    return {
        "recovered": False,
        "time_s": 600.0,
        "detection_delay_s": max(0.0, 600.0 - duration),
        "attempts": attempts,
        "blocked_attempts": blocked_attempts,
    }


def logistic(x):
    if x > 40.0:
        return 1.0
    if x < -40.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def simulate_pressure_feedback(policy, service, waits, seed):
    """Hypothetical pressure-feedback stress model.

    Parameters are deliberately broad and are not fitted to OpenAI internals.
    The question is whether a policy remains useful if attempts consume a
    pressure budget that decays over wall-clock time.
    """

    param_rng = random.Random(seed)
    rng = random.Random(seed ^ 0x9E3779B9)

    tau = math.exp(
        math.log(15.0)
        + (math.log(120.0) - math.log(15.0)) * param_rng.random()
    )
    alpha = 0.05 + 0.30 * param_rng.random()
    theta = 0.70 + 0.60 * param_rng.random()
    steepness = 4.0 + 8.0 * param_rng.random()

    pressure = theta + 0.20 + 0.60 * param_rng.random()

    t = 0.0
    last_t = 0.0
    attempts = 0
    blocked_attempts = 0
    blocked_run = 0
    accessible_run = 0

    while t < 900.0 and attempts < 200:
        dt = t - last_t
        pressure *= math.exp(-dt / tau)
        last_t = t

        pressure += alpha
        p_blocked = logistic(steepness * (pressure - theta))
        blocked = rng.random() < p_blocked

        state = "blocked" if blocked else "accessible"
        attempts += 1

        if blocked:
            blocked_attempts += 1
            blocked_run += 1
            accessible_run = 0
        else:
            blocked_run = 0
            accessible_run += 1

        if accessible_run >= 2:
            return {
                "recovered": True,
                "time_s": t,
                "attempts": attempts,
                "blocked_attempts": blocked_attempts,
            }

        s = rng.choice(service[state])
        w = rng.choice(waits[state])
        t += gap_for(policy, state, blocked_run, s, w, rng)

    return {
        "recovered": False,
        "time_s": 900.0,
        "attempts": attempts,
        "blocked_attempts": blocked_attempts,
    }


def pack(results, include_delay=False):
    recovered = [r for r in results if r["recovered"]]
    out = {
        "recovery_rate": len(recovered) / len(results),
        "recovery_time_s": describe([r["time_s"] for r in recovered]),
        "attempts": describe([r["attempts"] for r in recovered]),
        "blocked_attempts": describe(
            [r["blocked_attempts"] for r in recovered]
        ),
    }
    if include_delay:
        out["detection_delay_s"] = describe(
            [r["detection_delay_s"] for r in recovered]
        )
    return out


def bootstrap_observed(transitions, trials, seed):
    rng = random.Random(seed)

    accessible = [x for x in transitions if x["state"] == "accessible"]
    blocked = [x for x in transitions if x["state"] == "blocked"]

    med_a = []
    med_b = []
    wait_a = []
    wait_b = []

    for _ in range(trials):
        a = [rng.choice(accessible) for _ in accessible]
        b = [rng.choice(blocked) for _ in blocked]

        med_a.append(statistics.median(x["gap"] for x in a))
        med_b.append(statistics.median(x["gap"] for x in b))
        wait_a.append(statistics.median(x["wait"] for x in a))
        wait_b.append(statistics.median(x["wait"] for x in b))

    def ci(values):
        return {
            "p2_5": quantile(values, 0.025),
            "p50": quantile(values, 0.50),
            "p97_5": quantile(values, 0.975),
        }

    return {
        "accessible_gap_median_s": ci(med_a),
        "blocked_gap_median_s": ci(med_b),
        "accessible_post_completion_wait_median_s": ci(wait_a),
        "blocked_post_completion_wait_median_s": ci(wait_b),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="data/paired_observations.csv",
    )
    parser.add_argument("--trials", type=int, default=20000)
    parser.add_argument("--bootstrap-trials", type=int, default=30000)
    parser.add_argument("--seed", type=int, default=0x12345678)
    parser.add_argument("--output")
    args = parser.parse_args()

    transitions, service, waits = load_transitions(Path(args.csv))

    summary = {
        "warning": (
            "Design stress test only. The pressure-feedback model is not "
            "identified from OpenAI internals."
        ),
        "trials_per_policy_per_model": args.trials,
        "bootstrap": bootstrap_observed(
            transitions,
            args.bootstrap_trials,
            args.seed ^ 0xABCDEF01,
        ),
        "policies": {},
    }

    for policy_index, (name, policy) in enumerate(POLICIES.items()):
        attempt_results = []
        latent_results = []
        pressure_results = []

        for i in range(args.trials):
            seed = (
                args.seed
                + policy_index * 0x1000003D
                + i * 2654435761
            ) & 0xFFFFFFFF

            attempt_results.append(
                simulate_attempt_driven(policy, service, waits, seed)
            )
            latent_results.append(
                simulate_latent_wallclock(policy, service, waits, seed)
            )
            pressure_results.append(
                simulate_pressure_feedback(policy, service, waits, seed)
            )

        summary["policies"][name] = {
            "policy": policy,
            "attempt_driven": pack(attempt_results),
            "latent_wallclock": pack(
                latent_results,
                include_delay=True,
            ),
            "pressure_feedback": pack(pressure_results),
        }

    text = json.dumps(summary, indent=2, sort_keys=True)

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
