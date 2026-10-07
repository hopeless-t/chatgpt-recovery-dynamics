#!/usr/bin/env python3
"""Validate the canonical Purrtocol Civilization repository-history chronicle.

The chronicle deliberately separates merged repository history from playful
civilization projection labels. Narrative labels are allowed; they are never
upgraded into evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA = "purrtocol-civilization-chronicle/v0"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
JST = timezone(timedelta(hours=9))


class ChronicleError(ValueError):
    pass


def utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ChronicleError("merged_at_utc must be an ISO-8601 Z timestamp")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ChronicleError(f"invalid UTC timestamp: {value}") from exc


def validate(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") != SCHEMA:
        raise ChronicleError(f"expected schema {SCHEMA}")
    if doc.get("evidence_status") != "repository_history_plus_explicit_projection_labels":
        raise ChronicleError("unexpected evidence_status")

    contract = doc.get("time_contract", {})
    if contract.get("canonical_clock") != "GitHub merged_at UTC":
        raise ChronicleError("canonical clock must remain GitHub merged_at UTC")
    if contract.get("narrative_names_are_projection") is not True:
        raise ChronicleError("narrative labels must remain projection-only")

    foundation = doc.get("foundation", {})
    foundation_pr = foundation.get("pr")
    foundation_time = utc(foundation.get("merged_at_utc"))

    events = doc.get("canonical_events")
    if not isinstance(events, list) or not events:
        raise ChronicleError("canonical_events must be non-empty")

    seen_prs: set[int] = set()
    seen_shas: set[str] = set()
    previous_time: datetime | None = None
    for index, row in enumerate(events):
        if not isinstance(row, dict):
            raise ChronicleError("canonical event must be an object")
        pr = row.get("pr")
        if isinstance(pr, bool) or not isinstance(pr, int) or pr <= 0:
            raise ChronicleError("canonical event pr must be a positive integer")
        if pr in seen_prs:
            raise ChronicleError(f"duplicate canonical PR #{pr}")
        seen_prs.add(pr)

        sha = row.get("merge_sha")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            raise ChronicleError(f"invalid merge SHA for PR #{pr}")
        if sha in seen_shas:
            raise ChronicleError(f"duplicate merge SHA for PR #{pr}")
        seen_shas.add(sha)

        merged = utc(row.get("merged_at_utc"))
        if previous_time is not None and merged <= previous_time:
            raise ChronicleError("canonical history must be strictly chronological")
        previous_time = merged

        expected_jst = merged.astimezone(JST).isoformat()
        if row.get("merged_at_jst") != expected_jst:
            raise ChronicleError(f"JST projection mismatch for PR #{pr}")
        expected_seconds = int((merged - foundation_time).total_seconds())
        if row.get("seconds_since_foundation") != expected_seconds:
            raise ChronicleError(f"foundation offset mismatch for PR #{pr}")
        if row.get("source_status") != "merged" or row.get("canonical_history") is not True:
            raise ChronicleError(f"canonical event #{pr} must be merged and canonical")
        if not isinstance(row.get("chronicle_name"), str) or not row["chronicle_name"].strip():
            raise ChronicleError(f"canonical event #{pr} needs a narrative label")
        if index == 0 and pr != foundation_pr:
            raise ChronicleError("first canonical event must equal foundation.pr")

    coverage = doc.get("coverage", {})
    last = events[-1]
    if coverage.get("through_pr") != last["pr"]:
        raise ChronicleError("coverage.through_pr must match latest canonical event")
    if coverage.get("through_merge_sha") != last["merge_sha"]:
        raise ChronicleError("coverage.through_merge_sha must match latest canonical event")
    if coverage.get("elapsed_seconds_from_foundation") != last["seconds_since_foundation"]:
        raise ChronicleError("coverage elapsed seconds must match latest event")

    prehistory = doc.get("prehistory", [])
    for row in prehistory:
        pr = row.get("pr")
        if pr in seen_prs:
            raise ChronicleError(f"prehistory PR #{pr} duplicates canonical history")
        if utc(row.get("merged_at_utc")) >= foundation_time:
            raise ChronicleError(f"prehistory PR #{pr} is not before foundation")

    experiments = doc.get("noncanonical_experiments", [])
    for row in experiments:
        pr = row.get("pr")
        if pr in seen_prs:
            raise ChronicleError(f"noncanonical PR #{pr} duplicates canonical history")
        if row.get("canonical_history") is not False:
            raise ChronicleError(f"noncanonical PR #{pr} must stay noncanonical")

    laws = doc.get("world_laws", {})
    required_laws = (
        "merged_repository_history_is_canonical",
        "open_pr_is_not_canonical_history",
        "narrative_label_is_not_evidence",
        "chronicle_must_be_monotonic",
        "history_can_expand_but_not_silently_rewrite",
        "no_final_civilization",
    )
    if not all(laws.get(key) is True for key in required_laws):
        raise ChronicleError("one or more chronicle world laws are missing")

    return {
        "canonical_events": len(events),
        "prehistory_events": len(prehistory),
        "noncanonical_experiments": len(experiments),
        "foundation_pr": foundation_pr,
        "latest_pr": last["pr"],
        "elapsed_seconds": last["seconds_since_foundation"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
    print(json.dumps(validate(doc), sort_keys=True))


if __name__ == "__main__":
    main()
