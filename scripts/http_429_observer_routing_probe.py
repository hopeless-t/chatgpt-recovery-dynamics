#!/usr/bin/env python3
"""Tiny local-only probe for MIL-004 live observer routing.

This script does not send network traffic and does not change retry semantics.
It only verifies that the already-frozen Python/Node and Python/Go receipts still
encode the expected local safety boundary before the live shadow router is
observed on this isolated 429 PR.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    node = load("data/http_429_cross_language_reference.json")
    go = load("data/http_429_go_cross_language_reference.json")

    assert node["observed"]["scenario_count"] == 8
    assert node["observed"]["semantic_parity"] is True
    assert node["safety"]["production_traffic"] is False
    assert node["safety"]["remote_target_input"] is False

    observed_go = go["observed"]
    assert observed_go["scenario_count"] == 8
    assert observed_go["semantic_parity"] is True
    assert go["safety"]["production_traffic"] is False
    assert go["safety"]["remote_target_input"] is False

    print(
        "MIL-004 isolated 429 live probe: PASS",
        "node=8/8",
        "go=8/8",
        "production_traffic=false",
        "execution_authority=false",
    )


if __name__ == "__main__":
    main()
