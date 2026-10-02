#!/usr/bin/env python3
"""Recompute public recovery-dynamics statistics from sanitized JSONL.

Uses only Python's standard library and published derivative telemetry.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

PAIR_WINDOW_S = 0.050
SESSION_GAP_S = 60.0


def load_events(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    rows.sort(key=lambda r: r["t_rel_s"])
    return rows


def pair_observations(events, window_s=PAIR_WINDOW_S):
    streams = [e for e in events if e["event"] == "stream_status"]
    snapshots = [e for e in events if e["event"] == "conversation_snapshot"]
    used = set()
    pairs = []

    for stream in streams:
        best_i = None
        best_delta = None
        for i, snap in enumerate(snapshots):
            if i in used:
                continue
            delta = abs(snap["t_rel_s"] - stream["t_rel_s"])
            if delta <= window_s and (best_delta is None or delta < best_delta):
                best_i = i
                best_delta = delta

        if best_i is None:
            continue

        used.add(best_i)
        snap = snapshots[best_i]

        if stream["status"] == "200" and snap["status"] == "200":
            state = "accessible"
        elif stream["status"] == "no_http_response" and snap["status"] == "429":
            state = "blocked"
        else:
            state = "mixed"

        pairs.append(
            {
                "t_rel_s": stream["t_rel_s"],
                "state": state,
                "stream_status": stream["status"],
                "snapshot_status": snap["status"],
                "pair_skew_ms": best_delta * 1000.0,
                "stream_latency_ms": stream["latency_ms"],
                "snapshot_latency_ms": snap["latency_ms"],
                "snapshot_payload_kib_rounded_4": snap.get(
                    "payload_kib_rounded_4"
                ),
            }
        )

    return pairs


def active_transitions(pairs, session_gap_s=SESSION_GAP_S):
    rows = []
    excluded = []
    for cur, nxt in zip(pairs, pairs[1:]):
        gap = nxt["t_rel_s"] - cur["t_rel_s"]
        if gap > session_gap_s:
            excluded.append(gap)
            continue

        service_s = max(
            cur["stream_latency_ms"], cur["snapshot_latency_ms"]
        ) / 1000.0

        rows.append(
            {
                "cur": cur,
                "next": nxt,
                "gap_s": gap,
                "service_s": service_s,
                "post_completion_wait_s": gap - service_s,
            }
        )
    return rows, excluded


def ols_one_predictor(xs, ys):
    n = len(xs)
    sx = sum(xs)
    sy = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))

    denom = n * sxx - sx * sx
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n

    mean_y = sy / n
    sse = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    sst = sum((y - mean_y) ** 2 for y in ys)

    return {
        "intercept_s": intercept,
        "service_time_coefficient": slope,
        "r2": 1.0 - sse / sst,
    }


def wilson_interval(k, n, z=1.959963984540054):
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = (
        z
        * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
        / denom
    )
    return [center - half, center + half]


def blocked_runs(pairs, session_gap_s=SESSION_GAP_S):
    segments = []
    start = 0
    for i in range(len(pairs) - 1):
        if pairs[i + 1]["t_rel_s"] - pairs[i]["t_rel_s"] > session_gap_s:
            segments.append(pairs[start : i + 1])
            start = i + 1
    segments.append(pairs[start:])

    out = []
    for seg_i, seg in enumerate(segments, start=1):
        i = 0
        while i < len(seg):
            if seg[i]["state"] != "blocked":
                i += 1
                continue
            j = i
            while j + 1 < len(seg) and seg[j + 1]["state"] == "blocked":
                j += 1
            out.append(
                {
                    "segment": seg_i,
                    "length_observations": j - i + 1,
                    "duration_s": seg[j]["t_rel_s"] - seg[i]["t_rel_s"],
                    "right_censored": j == len(seg) - 1,
                }
            )
            i = j + 1
    return out


def resume_episodes(events):
    episodes = []
    resumes = [
        e
        for e in events
        if e["event"] == "conversation_resume" and e["status"] == "404"
    ]

    for resume in resumes:
        later = [e for e in events if e["t_rel_s"] > resume["t_rel_s"]]
        first_429 = next(
            (
                e
                for e in later
                if e["event"] == "conversation_snapshot"
                and e["status"] == "429"
            ),
            None,
        )
        if first_429 is None:
            continue

        successes = [
            e
            for e in later
            if e["event"] == "conversation_snapshot"
            and e["status"] == "200"
            and e["t_rel_s"] < first_429["t_rel_s"]
        ]
        public_kib = sum(
            (e.get("payload_kib_rounded_4") or 0) for e in successes
        )

        episodes.append(
            {
                "seconds_to_first_snapshot_429": round(
                    first_429["t_rel_s"] - resume["t_rel_s"], 3
                ),
                "successful_snapshots_before_429": len(successes),
                "successful_snapshot_payload_mib_from_public_rounded_data": round(
                    public_kib / 1024.0, 3
                ),
            }
        )
    return episodes


def summarize(events, pairs, transitions, excluded_gaps):
    pair_counts = {
        "total": len(pairs),
        "accessible": sum(p["state"] == "accessible" for p in pairs),
        "blocked": sum(p["state"] == "blocked" for p in pairs),
        "mixed": sum(p["state"] == "mixed" for p in pairs),
    }

    transition_counts = {
        "accessible->accessible": 0,
        "accessible->blocked": 0,
        "blocked->accessible": 0,
        "blocked->blocked": 0,
    }
    for row in transitions:
        key = row["cur"]["state"] + "->" + row["next"]["state"]
        if key in transition_counts:
            transition_counts[key] += 1

    a_out = (
        transition_counts["accessible->accessible"]
        + transition_counts["accessible->blocked"]
    )
    b_out = (
        transition_counts["blocked->accessible"]
        + transition_counts["blocked->blocked"]
    )

    by_state = {
        state: [t for t in transitions if t["cur"]["state"] == state]
        for state in ("accessible", "blocked")
    }

    xs = [t["service_s"] for t in transitions]
    ys = [t["gap_s"] for t in transitions]

    total_active_time = sum(t["gap_s"] for t in transitions)
    blocked_active_time = sum(t["gap_s"] for t in by_state["blocked"])
    runs = blocked_runs(pairs)

    later_resume_200 = next(
        (
            e
            for e in events
            if e["event"] == "conversation_resume" and e["status"] == "200"
        ),
        None,
    )

    return {
        "pairing": {
            **pair_counts,
            "pairing_window_ms": PAIR_WINDOW_S * 1000.0,
            "max_pair_skew_ms": max(p["pair_skew_ms"] for p in pairs),
        },
        "sessionization": {
            "gap_threshold_s": SESSION_GAP_S,
            "excluded_cross_epoch_transition_count": len(excluded_gaps),
            "excluded_gaps_s": [round(x, 3) for x in excluded_gaps],
        },
        "transition_counts_active_epochs_only": transition_counts,
        "transition_probabilities": {
            "p_blocked_next_given_accessible": transition_counts[
                "accessible->blocked"
            ]
            / a_out,
            "p_blocked_next_given_blocked": transition_counts[
                "blocked->blocked"
            ]
            / b_out,
            "wilson_95_p_blocked_next_given_accessible": wilson_interval(
                transition_counts["accessible->blocked"], a_out
            ),
            "wilson_95_p_blocked_next_given_blocked": wilson_interval(
                transition_counts["blocked->blocked"], b_out
            ),
        },
        "cycle_time": {
            "median_gap_s": {
                state: statistics.median(t["gap_s"] for t in rows)
                for state, rows in by_state.items()
            },
            "mean_gap_s": {
                state: statistics.fmean(t["gap_s"] for t in rows)
                for state, rows in by_state.items()
            },
            "median_post_completion_wait_s": {
                state: statistics.median(
                    t["post_completion_wait_s"] for t in rows
                )
                for state, rows in by_state.items()
            },
            "service_time_regression": ols_one_predictor(xs, ys),
            "blocked_fraction_by_observation_count": pair_counts["blocked"]
            / pair_counts["total"],
            "blocked_fraction_by_active_time": blocked_active_time
            / total_active_time,
        },
        "blocked_runs": {
            "count": len(runs),
            "right_censored": sum(r["right_censored"] for r in runs),
            "median_length_observations": statistics.median(
                r["length_observations"] for r in runs
            ),
            "median_duration_s": statistics.median(
                r["duration_s"] for r in runs
            ),
        },
        "resume_observations": {
            "resume_404_episodes": resume_episodes(events),
            "later_resume_200_observed": later_resume_200 is not None,
            "later_resume_200_latency_ms": (
                later_resume_200["latency_ms"]
                if later_resume_200 is not None
                else None
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "jsonl",
        nargs="?",
        default="data/session_b_events.jsonl",
        help="sanitized public event JSONL",
    )
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    events = load_events(Path(args.jsonl))
    pairs = pair_observations(events)
    transitions, excluded = active_transitions(pairs)
    summary = summarize(events, pairs, transitions, excluded)

    if args.compact:
        print(json.dumps(summary, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
