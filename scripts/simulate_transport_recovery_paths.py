#!/usr/bin/env python3
"""Transport/recovery-path Monte Carlo stress test.

This script compares three client-side recovery paths under multiple mutually
incompatible causal models. It is a design robustness test, not a model of
OpenAI internals.

Paths:
1. completion_per_context
2. anchored_singleflight_full
3. observe_then_snapshot

The last path separates cheap state observation from expensive full snapshot
materialization.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path

SNAPSHOT_KIB = 4684.0
PROBE_KIB = 4.0

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

PATHS = {
    "completion_per_context": {
        "period_s": 6.0,
        "singleflight": False,
        "probe_first": False,
        "confirm_rounds": 2,
    },
    "anchored_singleflight_full": {
        "period_s": 10.0,
        "singleflight": True,
        "probe_first": False,
        "confirm_rounds": 2,
    },
    "observe_then_snapshot": {
        "period_s": 10.0,
        "singleflight": True,
        "probe_first": True,
        "confirm_rounds": 2,
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
        "p95": quantile(values, 0.95),
    }


def pack(results, include_delay=False):
    recovered = [r for r in results if r["recovered"]]
    out = {
        "recovery_rate": len(recovered) / len(results),
    }

    if not recovered:
        return out

    out.update(
        {
            "recovery_time_s": describe([r["time_s"] for r in recovered]),
            "requests": describe([r["requests"] for r in recovered]),
            "full_snapshots": describe(
                [r["full_snapshots"] for r in recovered]
            ),
            "payload_mib": {
                k: v / 1024.0
                for k, v in describe(
                    [r["payload_kib"] for r in recovered]
                ).items()
            },
        }
    )

    if include_delay:
        out["detection_delay_s"] = describe(
            [r["detection_delay_s"] for r in recovered]
        )

    return out


def simulate_naive_first_success(seed):
    """Stress-test declaring recovery after one A observation.

    Uses the biopsy-derived history model:
    B -> E: 8/58 observed
    E -> B: 8/8 observed

    Probabilities are sampled from Jeffreys posteriors.
    """

    rng = random.Random(seed)
    p_be = rng.betavariate(8.5, 50.5)
    p_eb = rng.betavariate(8.5, 0.5)
    tabs = rng.choice([1, 2, 3, 4])

    state = "B"
    t = 0.0

    while t < 1200.0:
        if state == "E":
            return {
                "recovered": True,
                "time_s": t,
                "false_rebound": rng.random() < p_eb,
            }

        # In this deliberately adverse attempt-driven model, multiple
        # independent recovery triggers can increase the chance of a transition.
        p_any = 1.0 - (1.0 - p_be) ** tabs
        state = "E" if rng.random() < p_any else "B"
        t += 6.0

    return {
        "recovered": False,
        "time_s": 1200.0,
        "false_rebound": False,
    }


def simulate_attempt_driven(path, seed):
    """Adverse model: recovery opportunities progress with observation attempts.

    This model penalizes single-flight / slower polling and is intentionally
    included to expose model risk.
    """

    rng = random.Random(seed)

    p_be = rng.betavariate(8.5, 50.5)
    p_eb = rng.betavariate(8.5, 0.5)
    p_hb = rng.betavariate(2.5, 38.5)

    tabs = rng.choice([1, 2, 3, 4])
    state = "B"
    t = 0.0
    requests = 0
    full_snapshots = 0
    payload_kib = 0.0
    consecutive_accessible_rounds = 0

    while t < 1200.0:
        n_requests = 1 if path["singleflight"] else tabs
        requests += n_requests

        if path["probe_first"]:
            payload_kib += n_requests * PROBE_KIB
        elif state != "B":
            full_snapshots += n_requests
            payload_kib += n_requests * SNAPSHOT_KIB

        accessible = state != "B"
        consecutive_accessible_rounds = (
            consecutive_accessible_rounds + 1
            if accessible
            else 0
        )

        if consecutive_accessible_rounds >= path["confirm_rounds"]:
            if path["probe_first"]:
                full_snapshots += 1
                payload_kib += SNAPSHOT_KIB

            return {
                "recovered": True,
                "time_s": t,
                "requests": requests,
                "full_snapshots": full_snapshots,
                "payload_kib": payload_kib,
            }

        if state == "B":
            p_any = 1.0 - (1.0 - p_be) ** n_requests
            state = "E" if rng.random() < p_any else "B"
        elif state == "E":
            state = "B" if rng.random() < p_eb else "H"
        else:
            p_any = 1.0 - (1.0 - p_hb) ** n_requests
            state = "B" if rng.random() < p_any else "H"

        t += path["period_s"]

    return {
        "recovered": False,
        "time_s": 1200.0,
        "requests": requests,
        "full_snapshots": full_snapshots,
        "payload_kib": payload_kib,
    }


def simulate_latent_wallclock(path, seed):
    """Blocked state clears with wall-clock time; polling only detects it."""

    rng = random.Random(seed)

    base_duration = rng.choice(COMPLETED_BLOCKED_RUN_DURATIONS_S)
    clear_time = base_duration * math.exp(
        0.30 * rng.normalvariate(0.0, 1.0)
    )

    tabs = rng.choice([1, 2, 3, 4])
    t = 0.0
    requests = 0
    full_snapshots = 0
    payload_kib = 0.0
    consecutive_accessible_rounds = 0

    while t < 600.0:
        n_requests = 1 if path["singleflight"] else tabs
        requests += n_requests
        accessible = t >= clear_time

        if path["probe_first"]:
            payload_kib += n_requests * PROBE_KIB
        elif accessible:
            full_snapshots += n_requests
            payload_kib += n_requests * SNAPSHOT_KIB

        consecutive_accessible_rounds = (
            consecutive_accessible_rounds + 1
            if accessible
            else 0
        )

        if consecutive_accessible_rounds >= path["confirm_rounds"]:
            if path["probe_first"]:
                full_snapshots += 1
                payload_kib += SNAPSHOT_KIB

            return {
                "recovered": True,
                "time_s": t,
                "detection_delay_s": t - clear_time,
                "requests": requests,
                "full_snapshots": full_snapshots,
                "payload_kib": payload_kib,
            }

        t += path["period_s"]

    return {
        "recovered": False,
        "time_s": 600.0,
        "detection_delay_s": max(0.0, 600.0 - clear_time),
        "requests": requests,
        "full_snapshots": full_snapshots,
        "payload_kib": payload_kib,
    }


def logistic(x):
    if x > 40.0:
        return 1.0
    if x < -40.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def simulate_pressure(path, seed, cost_mode):
    """Hypothetical pressure-feedback stress model.

    cost_mode=request:
        every request has equal pressure cost.

    cost_mode=byte:
        cheap probes have pressure cost proportional to their payload relative
        to a 4.684 MiB full snapshot.

    Neither cost model is claimed to match a production rate limiter.
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

    tabs = param_rng.choice([1, 2, 3, 4])

    t = 0.0
    last_t = 0.0
    requests = 0
    full_snapshots = 0
    payload_kib = 0.0
    consecutive_accessible_rounds = 0

    while t < 900.0:
        pressure *= math.exp(-(t - last_t) / tau)
        last_t = t

        n_requests = 1 if path["singleflight"] else tabs

        if cost_mode == "request":
            request_cost = 1.0
        elif path["probe_first"]:
            request_cost = PROBE_KIB / SNAPSHOT_KIB
        else:
            request_cost = 1.0

        pressure += alpha * n_requests * request_cost
        requests += n_requests

        p_blocked = logistic(steepness * (pressure - theta))
        blocked = rng.random() < p_blocked

        if path["probe_first"]:
            payload_kib += n_requests * PROBE_KIB
        elif not blocked:
            full_snapshots += n_requests
            payload_kib += n_requests * SNAPSHOT_KIB

        consecutive_accessible_rounds = (
            0
            if blocked
            else consecutive_accessible_rounds + 1
        )

        if consecutive_accessible_rounds >= path["confirm_rounds"]:
            if path["probe_first"]:
                full_snapshots += 1
                payload_kib += SNAPSHOT_KIB

            return {
                "recovered": True,
                "time_s": t,
                "requests": requests,
                "full_snapshots": full_snapshots,
                "payload_kib": payload_kib,
            }

        t += path["period_s"]

    return {
        "recovered": False,
        "time_s": 900.0,
        "requests": requests,
        "full_snapshots": full_snapshots,
        "payload_kib": payload_kib,
    }


def poisson(rng, lam):
    # Knuth sampler; the configured lambda range is small.
    limit = math.exp(-lam)
    k = 0
    p = 1.0
    while p > limit:
        k += 1
        p *= rng.random()
    return k - 1


def simulate_path_churn(seed, base_recovery_window_s=60.0):
    """Sensitivity-only H2/TCP vs H3/QUIC path-change penalty model.

    Assumptions are intentionally broad and are not fitted to the HAR:
    - mean path-change interval: log-uniform 30..600 s;
    - TCP/H2 reconnect penalty: uniform 0.5..3.0 s;
    - QUIC migration survival probability: uniform 0.50..0.95;
    - successful migration validation penalty: uniform 0.1..0.5 s.

    This models path continuity only. It does not change 429 semantics.
    """

    rng = random.Random(seed)

    mean_interval = math.exp(
        math.log(30.0)
        + (math.log(600.0) - math.log(30.0)) * rng.random()
    )
    changes = poisson(rng, base_recovery_window_s / mean_interval)
    migration_survival = 0.50 + 0.45 * rng.random()

    h2_delay = 0.0
    h3_delay = 0.0

    for _ in range(changes):
        reconnect = 0.5 + 2.5 * rng.random()
        h2_delay += reconnect

        if rng.random() < migration_survival:
            h3_delay += 0.1 + 0.4 * rng.random()
        else:
            h3_delay += reconnect

    return {
        "path_changes": changes,
        "h2_extra_delay_s": h2_delay,
        "h3_extra_delay_s": h3_delay,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=0xC0FFEE)
    parser.add_argument("--output")
    args = parser.parse_args()

    naive = [
        simulate_naive_first_success(args.seed + i)
        for i in range(args.trials)
    ]
    naive_recovered = [r for r in naive if r["recovered"]]

    output = {
        "warning": (
            "Design stress test only. The causal and rate-pressure models are "
            "not identified from OpenAI internals."
        ),
        "observed_constants": {
            "successful_snapshot_kib_rounded_4": SNAPSHOT_KIB,
            "blocked_cycle_reference_s": 6.0,
            "accessible_cycle_anchor_s": 10.0,
        },
        "naive_first_success": {
            "recovery_observed_rate": len(naive_recovered) / len(naive),
            "posterior_predictive_false_rebound_rate": (
                statistics.fmean(
                    1.0 if r["false_rebound"] else 0.0
                    for r in naive_recovered
                )
            ),
            "time_to_first_accessible_s": describe(
                [r["time_s"] for r in naive_recovered]
            ),
        },
        "paths": {},
    }

    # Common random numbers: every path is evaluated against the same
    # parameter/random worlds. This reduces comparison variance and makes
    # path-only differences easier to interpret.
    for name, path in PATHS.items():
        base_seed = args.seed

        attempt = [
            simulate_attempt_driven(
                path,
                (base_seed + i * 2654435761) & 0xFFFFFFFF,
            )
            for i in range(args.trials)
        ]
        latent = [
            simulate_latent_wallclock(
                path,
                (base_seed ^ 0xABCDEF01) + i,
            )
            for i in range(args.trials)
        ]
        request_pressure = [
            simulate_pressure(
                path,
                (base_seed ^ 0x31415926) + i,
                "request",
            )
            for i in range(args.trials)
        ]
        byte_pressure = [
            simulate_pressure(
                path,
                (base_seed ^ 0x27182818) + i,
                "byte",
            )
            for i in range(args.trials)
        ]

        output["paths"][name] = {
            "path": path,
            "attempt_driven_hysteresis": pack(attempt),
            "latent_wallclock": pack(latent, include_delay=True),
            "request_count_pressure": pack(request_pressure),
            "byte_weighted_pressure": pack(byte_pressure),
        }

    churn = [
        simulate_path_churn(
            (args.seed ^ 0xDEADBEEF) + i,
        )
        for i in range(args.trials)
    ]

    output["optional_http3_path_churn_sensitivity"] = {
        "assumption_only": True,
        "probability_any_path_change_in_60s": (
            sum(r["path_changes"] > 0 for r in churn) / len(churn)
        ),
        "h2_extra_delay_s": describe(
            [r["h2_extra_delay_s"] for r in churn]
        ),
        "h3_extra_delay_s": describe(
            [r["h3_extra_delay_s"] for r in churn]
        ),
        "mean_h3_over_h2_delay_ratio": (
            statistics.fmean(r["h3_extra_delay_s"] for r in churn)
            / statistics.fmean(r["h2_extra_delay_s"] for r in churn)
        ),
        "guardrail": (
            "H3/QUIC path-migration parameters are hypothetical sensitivity "
            "inputs. This result is not evidence that path migration caused "
            "the observed ChatGPT failure."
        ),
    }

    text = json.dumps(output, indent=2, sort_keys=True) + "\n"

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
