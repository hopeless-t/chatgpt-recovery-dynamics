#!/usr/bin/env python3
"""Generate Civilization News from the validated canonical chronicle.

The Annalist may project playful headlines from explicit chronicle labels, but it
may not invent source facts. Every article remains bound to a merged PR and merge
SHA from the canonical repository-history ledger.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import validate_purrtocol_civilization_chronicle as chronicle_validator

OUTPUT_SCHEMA = "purrtocol-civilization-news/v0"


def format_elapsed(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"+{hours:02d}:{minutes:02d}:{secs:02d}"


def build(doc: dict[str, Any]) -> dict[str, Any]:
    summary = chronicle_validator.validate(doc)
    articles: list[dict[str, Any]] = []
    era_order: list[str] = []

    for index, event in enumerate(doc["canonical_events"], start=1):
        era = event["era"]
        if era not in era_order:
            era_order.append(era)
        articles.append({
            "article_id": f"PCN-{index:03d}",
            "headline": event["chronicle_name"],
            "headline_status": "projection_from_explicit_chronicle_label",
            "deck": f"PR #{event['pr']} entered canonical repository history at {event['merged_at_jst']}.",
            "era": era,
            "elapsed_from_foundation": format_elapsed(event["seconds_since_foundation"]),
            "repository_fact": event["title"],
            "source": {
                "pr": event["pr"],
                "merge_sha": event["merge_sha"],
                "merged_at_utc": event["merged_at_utc"],
                "merged_at_jst": event["merged_at_jst"],
                "canonical_history": True,
            },
        })

    latest = articles[-1]
    return {
        "schema": OUTPUT_SCHEMA,
        "evidence_status": "projection_from_validated_repository_history",
        "selection_policy": "all-canonical-events-no-unsourced-headlines",
        "front_page": {
            "headline": latest["headline"],
            "source_pr": latest["source"]["pr"],
            "elapsed_from_foundation": latest["elapsed_from_foundation"],
            "civilization_speedrun": doc["coverage"]["elapsed_human"],
        },
        "summary": {
            **summary,
            "articles": len(articles),
            "eras": len(era_order),
        },
        "era_order": era_order,
        "auditor_contract": {
            "chronicle_validation_required": True,
            "open_pr_may_not_become_article": True,
            "headline_is_projection_not_evidence": True,
            "source_pr_and_merge_sha_required": True,
            "unsourced_fact_generation_forbidden": True,
            "news_does_not_rewrite_history": True,
        },
        "articles": articles,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = build(doc)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["front_page"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
