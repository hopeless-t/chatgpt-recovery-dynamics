#!/usr/bin/env python3
"""Summarize the curated public-report archaeology corpus.

The corpus is a convenience archive, not a population sample. This script
computes recurrence and feature co-occurrence only; it deliberately does not
estimate prevalence or a posterior probability of root cause.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path


TRIGGER_FEATURES = {
    "multiple_tabs_association",
    "conversation_mutation_association",
    "sidebar_refresh_hypothesis",
}

STATE_DISSOCIATION_FEATURES = {
    "canonical_conversation_apparently_present",
    "cross_client_divergence",
    "multi_client_symptom",
    "client_state_dissociation",
    "temporary_recovery",
}

TRANSPORT_RECOVERY_FEATURES = {
    "stream_recovery_polling_timeout",
    "conversation_resume_404",
    "stream_status_reports_streaming",
    "websocket_failure",
    "transport_recovery_anomaly",
}


def load_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def is_incident_confounded(row):
    value = str(row.get("incident_overlap", ""))
    return (
        "confirmed" in value
        or "same_day" in value
        or "near_official" in value
    )


def has_all(row, *features):
    fs = set(row.get("features", []))
    return all(x in fs for x in features)


def has_any(row, features):
    fs = set(row.get("features", []))
    return bool(fs & set(features))


def summarize(rows):
    default = [
        r
        for r in rows
        if not r.get("negative_control", False)
        and not r.get("possible_local_overlap", False)
    ]

    clean = [r for r in default if not is_incident_confounded(r)]

    dates = sorted({r["date"] for r in default if r.get("date")})
    start = date.fromisoformat(dates[0])
    end = date.fromisoformat(dates[-1])

    core = [
        r
        for r in default
        if r.get("date") and "2026-03-28" <= r["date"] <= "2026-09-29"
    ]

    counts = Counter()
    for row in default:
        counts.update(row.get("features", []))

    def cooccurrence(subset):
        return {
            "unable_load_and_too_many_requests": sum(
                has_all(r, "unable_to_load_conversation", "too_many_requests")
                for r in subset
            ),
            "too_many_requests_and_local_trigger_association": sum(
                "too_many_requests" in set(r.get("features", []))
                and has_any(r, TRIGGER_FEATURES)
                for r in subset
            ),
            "state_dissociation_signature": sum(
                has_any(r, STATE_DISSOCIATION_FEATURES) for r in subset
            ),
            "transport_recovery_signature": sum(
                has_any(r, TRANSPORT_RECOVERY_FEATURES) for r in subset
            ),
        }

    return {
        "archive_total": len(rows),
        "default_inference_subset": len(default),
        "negative_controls": sum(
            bool(r.get("negative_control", False)) for r in rows
        ),
        "possible_local_overlap_excluded": sum(
            bool(r.get("possible_local_overlap", False)) for r in rows
        ),
        "distinct_dates_default": len(dates),
        "archaeology_span_days": (end - start).days,
        "core_2026": {
            "reports": len(core),
            "distinct_dates": len({r["date"] for r in core}),
            "span_days": (
                date(2026, 9, 29) - date(2026, 3, 28)
            ).days,
        },
        "incident_confounded_reports": sum(
            is_incident_confounded(r) for r in default
        ),
        "incident_unconfounded_reports": len(clean),
        "feature_counts_default_subset": dict(sorted(counts.items())),
        "cooccurrence_default_subset": cooccurrence(default),
        "incident_unconfounded_sensitivity_subset": {
            "n": len(clean),
            **cooccurrence(clean),
        },
        "guardrail": (
            "Convenience archive only: counts are not prevalence estimates, "
            "reports are not assumed IID, and no root-cause posterior is "
            "computed."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "jsonl",
        nargs="?",
        default="data/external_observations.jsonl",
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    summary = summarize(load_jsonl(Path(args.jsonl)))
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
