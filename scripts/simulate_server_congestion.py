#!/usr/bin/env python3
"""Popular-server congestion and retry-amplification stress simulator.

Purpose
-------
Compare recovery designs when a popular service is already near capacity.

This is a design stress test, not an estimate of OpenAI production capacity,
queue lengths, rate-limit rules, or request costs.

The simulator separates:
- exogenous foreground traffic, parameterized by base load rho;
- recovery traffic and retries;
- bounded queue/admission behavior;
- client-side single-flight / cheap observation;
- server-directed retry spacing;
- a balanced server-friendly queue policy.

Standard library only.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import random
import statistics
from collections import deque
from dataclasses import dataclass


DEFAULT_RHOS = [0.70, 0.80, 0.90, 0.95, 0.98, 1.00, 1.05, 1.10]

POLICIES = (
    "naive_completion",
    "retry_after_jitter",
    "singleflight_observe",
    "server_friendly_stack",
    "foreground_first",
)


@dataclass
class Job:
    kind: str
    conv: int | None
    tab: int | None
    arrival: float
    cost: float
    bytes_kib: float
    remaining: float


class WorkQueue:
    def __init__(self):
        self.q = deque()
        self.work = 0.0

    def append(self, job: Job):
        self.q.append(job)
        self.work += job.remaining


def poisson(rng: random.Random, lam: float) -> int:
    if lam < 30.0:
        limit = math.exp(-lam)
        p = 1.0
        k = 0
        while p > limit:
            k += 1
            p *= rng.random()
        return k - 1

    # Normal approximation is adequate for this stress simulator and keeps the
    # standard-library implementation cheap at high offered load.
    return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))


def quantile(values, q):
    if not values:
        return None
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


def make_world(seed, rho, seconds, capacity, conversations):
    rng = random.Random(seed)

    # Foreground user traffic has unit work cost. rho therefore denotes
    # exogenous foreground offered work / nominal service capacity.
    normal_arrivals = [
        poisson(rng, rho * capacity)
        for _ in range(seconds)
    ]

    tabs = [rng.randint(1, 4) for _ in range(conversations)]
    initial_probe_offsets = [
        rng.random() * 2.0
        for _ in range(conversations)
    ]

    return {
        "seed": seed,
        "normal_arrivals": normal_arrivals,
        "tabs": tabs,
        "initial_probe_offsets": initial_probe_offsets,
    }


def simulate(policy, world, seconds, capacity, conversations):
    policy_seed = {
        "naive_completion": 0x11111111,
        "retry_after_jitter": 0x22222222,
        "singleflight_observe": 0x33333333,
        "server_friendly_stack": 0x44444444,
        "foreground_first": 0x55555555,
    }[policy]

    rng = random.Random(world["seed"] ^ policy_seed)

    snapshot_cost = 5.0
    probe_cost = 0.05
    snapshot_kib = 4684.0
    probe_kib = 4.0

    fifo = WorkQueue()
    q_normal = WorkQueue()
    q_probe = WorkQueue()
    q_snapshot = WorkQueue()

    events = []
    event_counter = 0

    def push_event(t, conv, tab, kind):
        nonlocal event_counter
        heapq.heappush(
            events,
            (t, event_counter, conv, tab, kind),
        )
        event_counter += 1

    state = {
        conv: {
            "probe_successes": 0,
            "recovered": False,
            "snapshot_scheduled": False,
        }
        for conv in range(conversations)
    }

    if policy in ("naive_completion", "retry_after_jitter"):
        for conv in range(conversations):
            for tab in range(world["tabs"][conv]):
                push_event(0.0, conv, tab, "snapshot")
    else:
        for conv in range(conversations):
            push_event(
                world["initial_probe_offsets"][conv],
                conv,
                0,
                "probe",
            )

    normal_latencies = []
    recovery_latencies = []

    normal_arrivals_total = 0
    normal_rejected = 0
    recovery_rejected = 0
    recovery_requests = 0
    recovery_payload_kib = 0.0

    max_queue_work = 0.0
    duplicate_recovery_work = 0.0
    completed_recovery_work = 0.0

    def total_friendly_work():
        return (
            q_normal.work
            + q_probe.work
            + q_snapshot.work
        )

    def schedule_retry(now, conv, tab, kind):
        if policy == "naive_completion":
            delay = 6.0
        elif policy == "retry_after_jitter":
            # Conceptual server-directed Retry-After + jitter.
            delay = 10.0 * (0.8 + 0.4 * rng.random())
        else:
            # Start-anchored / jittered recovery retry.
            delay = 10.0 * (0.85 + 0.30 * rng.random())

        push_event(now + delay, conv, tab, kind)

    def admit(job, now):
        nonlocal normal_rejected
        nonlocal recovery_rejected
        nonlocal recovery_requests
        nonlocal recovery_payload_kib

        if job.kind != "normal":
            recovery_requests += 1

        if policy in ("server_friendly_stack", "foreground_first"):
            if job.kind == "normal":
                queue = q_normal
                class_limit = 2.0 * capacity
            elif job.kind == "probe":
                queue = q_probe
                class_limit = 0.25 * capacity
            else:
                queue = q_snapshot
                class_limit = 1.5 * capacity

            # Bound total queueing work as well as each class. This is a
            # load-shedding/admission-control model, not an infinite backlog.
            accepted = (
                queue.work + job.cost <= class_limit
                and total_friendly_work() + job.cost <= 2.0 * capacity
            )
        else:
            queue = fifo
            accepted = fifo.work + job.cost <= 2.0 * capacity

        if not accepted:
            if job.kind == "normal":
                normal_rejected += 1
            else:
                recovery_rejected += 1
                schedule_retry(
                    now,
                    job.conv,
                    job.tab,
                    job.kind,
                )
            return

        queue.append(job)

        if job.kind != "normal":
            recovery_payload_kib += job.bytes_kib

    def finish(job, now):
        nonlocal duplicate_recovery_work
        nonlocal completed_recovery_work

        if job.kind == "normal":
            normal_latencies.append(now - job.arrival)
            return

        completed_recovery_work += job.cost

        conv = job.conv

        if state[conv]["recovered"]:
            duplicate_recovery_work += job.cost
            return

        if job.kind == "probe":
            state[conv]["probe_successes"] += 1

            if (
                state[conv]["probe_successes"] >= 2
                and not state[conv]["snapshot_scheduled"]
            ):
                state[conv]["snapshot_scheduled"] = True

                if policy == "singleflight_observe":
                    delay = 0.0
                else:
                    delay = rng.random() * 3.0

                push_event(
                    now + delay,
                    conv,
                    0,
                    "snapshot",
                )
            else:
                push_event(
                    now + 10.0 * (0.9 + 0.2 * rng.random()),
                    conv,
                    0,
                    "probe",
                )
        else:
            state[conv]["recovered"] = True
            recovery_latencies.append(now)

    def serve(queue, budget, now):
        while queue.q and budget > 1e-12:
            job = queue.q[0]
            work = min(job.remaining, budget)

            job.remaining -= work
            queue.work -= work
            budget -= work

            if job.remaining <= 1e-12:
                queue.q.popleft()
                finish(job, now)

        return budget

    for second in range(seconds):
        arrivals = world["normal_arrivals"][second]
        normal_arrivals_total += arrivals

        for _ in range(arrivals):
            admit(
                Job(
                    "normal",
                    None,
                    None,
                    second,
                    1.0,
                    1.0,
                    1.0,
                ),
                second,
            )

        while events and events[0][0] <= second:
            _, _, conv, tab, kind = heapq.heappop(events)

            if state[conv]["recovered"]:
                continue

            if kind == "snapshot":
                admit(
                    Job(
                        kind,
                        conv,
                        tab,
                        second,
                        snapshot_cost,
                        snapshot_kib,
                        snapshot_cost,
                    ),
                    second,
                )
            else:
                admit(
                    Job(
                        kind,
                        conv,
                        tab,
                        second,
                        probe_cost,
                        probe_kib,
                        probe_cost,
                    ),
                    second,
                )

        budget = capacity

        if policy in ("server_friendly_stack", "foreground_first"):
            # Cheap observations get a tiny bounded lane so they cannot be
            # starved behind multi-unit work.
            probe_budget = min(budget, 1.0)
            probe_remaining = serve(
                q_probe,
                probe_budget,
                second + 1,
            )
            budget -= probe_budget - probe_remaining

            if policy == "server_friendly_stack":
                # Balanced mode: if both queues are backlogged, guarantee only
                # a tiny recovery share. Foreground traffic gets the rest.
                recovery_reserve = (
                    2.0
                    if q_normal.q and q_snapshot.q
                    else 0.0
                )
            else:
                # Emergency overload mode: recovery snapshot work only uses
                # residual capacity after foreground traffic.
                recovery_reserve = 0.0

            normal_budget = max(
                0.0,
                budget - recovery_reserve,
            )
            normal_remaining = serve(
                q_normal,
                normal_budget,
                second + 1,
            )
            budget = recovery_reserve + normal_remaining

            budget = serve(
                q_snapshot,
                budget,
                second + 1,
            )

            # Any reserved-but-unused recovery capacity is borrowed back by
            # foreground traffic.
            if budget > 0.0:
                budget = serve(
                    q_normal,
                    budget,
                    second + 1,
                )

            queue_work = total_friendly_work()
        else:
            budget = serve(
                fifo,
                budget,
                second + 1,
            )
            queue_work = fifo.work

        max_queue_work = max(
            max_queue_work,
            queue_work,
        )

    recovered = sum(
        row["recovered"]
        for row in state.values()
    )

    normal_success = (
        len(normal_latencies) / normal_arrivals_total
        if normal_arrivals_total
        else 1.0
    )

    return {
        "normal_success": normal_success,
        "normal_p95_s": quantile(normal_latencies, 0.95),
        "recovery_rate": recovered / conversations,
        "recovery_p95_s": quantile(
            recovery_latencies,
            0.95,
        ),
        "normal_rejected": normal_rejected,
        "recovery_rejected": recovery_rejected,
        "recovery_requests": recovery_requests,
        "retry_amplification_per_logical_recovery": (
            recovery_requests / conversations
        ),
        "recovery_payload_mib": (
            recovery_payload_kib / 1024.0
        ),
        "max_queue_work": max_queue_work,
        "wasted_recovery_work_fraction": (
            duplicate_recovery_work / completed_recovery_work
            if completed_recovery_work
            else 0.0
        ),
    }


def aggregate(results):
    keys = (
        "normal_success",
        "normal_p95_s",
        "recovery_rate",
        "recovery_p95_s",
        "normal_rejected",
        "recovery_rejected",
        "recovery_requests",
        "retry_amplification_per_logical_recovery",
        "recovery_payload_mib",
        "max_queue_work",
        "wasted_recovery_work_fraction",
    )

    out = {}

    for key in keys:
        values = [
            row[key]
            for row in results
            if row[key] is not None
        ]

        out[key] = describe(values)

    return out


def operational_knee(rho_rows):
    """First sampled rho that violates the conservative service objective."""

    for rho, row in rho_rows:
        if (
            row["normal_success"]["mean"] < 0.99
            or row["recovery_rate"]["mean"] < 0.99
        ):
            return rho

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trials",
        type=int,
        default=30,
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=300,
    )
    parser.add_argument(
        "--capacity",
        type=float,
        default=100.0,
    )
    parser.add_argument(
        "--conversations",
        type=int,
        default=80,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
    )
    parser.add_argument(
        "--rho",
        nargs="*",
        type=float,
        default=DEFAULT_RHOS,
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    output = {
        "warning": (
            "Design stress test only. rho, work costs, queue bounds, and "
            "server capacity are abstract and are not estimates of OpenAI."
        ),
        "definition": {
            "rho": (
                "exogenous foreground offered work divided by nominal "
                "server service capacity, before recovery/retry traffic"
            ),
            "capacity_work_units_per_second": args.capacity,
            "simulation_seconds": args.seconds,
            "logical_recovery_conversations": args.conversations,
            "trials_per_rho_policy": args.trials,
            "queue_bound": (
                "approximately 2x one-second nominal capacity in abstract "
                "work units"
            ),
        },
        "policies": {},
        "rho_grid": args.rho,
    }

    worlds_by_rho = {}

    for rho in args.rho:
        worlds_by_rho[rho] = [
            make_world(
                args.seed + trial * 101,
                rho,
                args.seconds,
                args.capacity,
                args.conversations,
            )
            for trial in range(args.trials)
        ]

    for policy in POLICIES:
        rows = []

        for rho in args.rho:
            results = [
                simulate(
                    policy,
                    world,
                    args.seconds,
                    args.capacity,
                    args.conversations,
                )
                for world in worlds_by_rho[rho]
            ]

            summary = aggregate(results)
            rows.append((rho, summary))

        output["policies"][policy] = {
            "operational_knee_first_sampled_rho": operational_knee(rows),
            "by_rho": {
                f"{rho:.2f}": summary
                for rho, summary in rows
            },
        }

    output["guardrails"] = [
        "When base rho >= 1, no retry policy creates missing server capacity.",
        "Server admission/load shedding can preserve useful work but may defer recovery.",
        "Client-side single-flight and cheap observation reduce offered recovery load before it reaches the server.",
        "Retry-After/jitter reduce synchronized retry amplification but do not replace capacity planning.",
    ]

    text = json.dumps(
        output,
        indent=2,
        sort_keys=True,
    ) + "\n"

    if args.output:
        with open(
            args.output,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
