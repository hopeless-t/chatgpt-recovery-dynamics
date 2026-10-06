#!/usr/bin/env python3
"""Derive propagation-shape signals from an owner-visible traffic snapshot.

This tool does not infer humans, descendants, or causal attribution from clone traffic.
It intentionally emits bounded derived signals and competing hypotheses.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Snapshot:
    clones: int
    unique_cloners: int
    views: int
    unique_visitors: int


def safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def analyze(snapshot: Snapshot) -> dict:
    clone_per_cloner = safe_ratio(snapshot.clones, snapshot.unique_cloners)
    cloner_to_visitor = safe_ratio(snapshot.unique_cloners, snapshot.unique_visitors)
    clone_to_view = safe_ratio(snapshot.clones, snapshot.views)

    signals: list[str] = []
    if clone_per_cloner is not None and clone_per_cloner >= 5:
        signals.append("repeat-full-clone-heavy")
    if cloner_to_visitor is not None and cloner_to_visitor >= 5:
        signals.append("direct-clone-heavy-relative-to-web-visitors")
    if clone_to_view is not None and clone_to_view >= 5:
        signals.append("clone-heavy-relative-to-page-views")
    if not signals:
        signals.append("no-strong-shape-signal-under-current-heuristics")

    hypotheses = [
        "direct Git access without repository-page browsing",
        "CI or other automation performing fresh clones",
        "agent/tool-driven repository acquisition",
        "scanner, archival, mirror, or indexing activity",
        "human cloning mixed with repeated automated clones",
    ]

    return {
        "schema": "purrtocol-propagation-shape/v0",
        "evidence_status": "derived",
        "causal_status": "unknown",
        "raw_values_included": False,
        "ratios": {
            "clones_per_unique_cloner": clone_per_cloner,
            "unique_cloners_per_unique_visitor": cloner_to_visitor,
            "clones_per_page_view": clone_to_view,
        },
        "signals": signals,
        "competing_hypotheses": hypotheses,
        "invariants": [
            "Clone != human adopter",
            "Unique cloner != verified unique person",
            "Propagation != popularity",
            "UNKNOWN != descendant",
            "Visualization != Evidence",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clones", type=int, required=True)
    parser.add_argument("--unique-cloners", type=int, required=True)
    parser.add_argument("--views", type=int, required=True)
    parser.add_argument("--unique-visitors", type=int, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    values = [args.clones, args.unique_cloners, args.views, args.unique_visitors]
    if any(value < 0 for value in values):
        raise SystemExit("traffic counts must be non-negative")

    result = analyze(
        Snapshot(
            clones=args.clones,
            unique_cloners=args.unique_cloners,
            views=args.views,
            unique_visitors=args.unique_visitors,
        )
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
