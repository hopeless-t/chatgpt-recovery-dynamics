#!/usr/bin/env python3
"""
Extract a coarse, publishable event stream from a ChatGPT HAR capture.

This script intentionally does not export headers, session secrets, bodies,
identifiers, exact URLs/query strings, or absolute timestamps.

Always manually review generated output before publishing it.
"""

import json
import re
import sys
from datetime import datetime
from urllib.parse import urlparse


def parse_dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def classify(entry):
    req = entry.get("request", {})
    u = urlparse(req.get("url", ""))
    host = u.hostname or ""
    path = u.path
    method = req.get("method", "")

    # Classification happens locally. Exact paths/IDs are never emitted.
    if host == "chatgpt.com" and method == "GET" and re.fullmatch(
        r"/backend-api/conversations/[0-9a-fA-F-]+", path
    ):
        return "conversation_snapshot"

    if host == "chatgpt.com" and method == "GET" and re.fullmatch(
        r"/backend-api/conversation/[0-9a-fA-F-]+/stream_status", path
    ):
        return "stream_status"

    if host == "chatgpt.com" and method == "POST" and path == "/backend-api/f/conversation/resume":
        return "conversation_resume"

    if host == "ws.chatgpt.com" and entry.get("_resourceType") == "websocket":
        return "websocket"

    return None


def status(entry):
    value = entry.get("response", {}).get("status", 0)
    return "no_http_response" if value == 0 else str(value)


def round_payload_kib_4(entry):
    n = entry.get("response", {}).get("content", {}).get("size")
    if n is None or n < 0:
        return None
    return int(round(n / 4096.0) * 4)


def main(src, dst):
    with open(src, "r", encoding="utf-8") as f:
        har = json.load(f)

    selected = [
        e for e in har.get("log", {}).get("entries", [])
        if classify(e) is not None and e.get("startedDateTime")
    ]
    selected.sort(key=lambda e: parse_dt(e["startedDateTime"]))

    if not selected:
        raise SystemExit("No matching events found.")

    t0 = parse_dt(selected[0]["startedDateTime"])

    with open(dst, "w", encoding="utf-8") as out:
        for e in selected:
            row = {
                "t_rel_s": round((parse_dt(e["startedDateTime"]) - t0).total_seconds(), 3),
                "event": classify(e),
                "status": status(e),
                "latency_ms": round(float(e.get("time", 0)), 3),
                "payload_kib_rounded_4": round_payload_kib_4(e),
            }
            out.write(json.dumps(row, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} input.har output.jsonl")
    main(sys.argv[1], sys.argv[2])
