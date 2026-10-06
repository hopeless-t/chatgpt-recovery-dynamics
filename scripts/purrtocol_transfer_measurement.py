#!/usr/bin/env python3
"""Measure a deterministic compressed-transfer proxy for Purrtocol assets.

This is deliberately a *measurement contract*, not a network truth model and
not an Arena fitness objective. It uses Python stdlib gzip with level=9 and
mtime=0 so the same bytes produce stable proxy bytes in the same contract.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

SCHEMA = "purrtocol-transfer-proxy/v0"
MAX_ASSET_BYTES = 4 * 1024 * 1024


class TransferMeasurementError(ValueError):
    pass


def measure(data: bytes, renderer_id: str) -> dict[str, object]:
    if not renderer_id.strip():
        raise TransferMeasurementError("renderer_id must be non-empty")
    if not data:
        raise TransferMeasurementError("asset must be non-empty")
    if len(data) > MAX_ASSET_BYTES:
        raise TransferMeasurementError("asset exceeds bounded measurement limit")

    compressed = gzip.compress(data, compresslevel=9, mtime=0)
    raw_sha = hashlib.sha256(data).hexdigest()
    gzip_sha = hashlib.sha256(compressed).hexdigest()
    ratio = len(compressed) / len(data)

    return {
        "schema": SCHEMA,
        "renderer_id": renderer_id.strip(),
        "asset_sha256": raw_sha,
        "raw_bytes": len(data),
        "gzip_bytes": len(compressed),
        "compression_ratio": round(ratio, 9),
        "gzip_sha256": gzip_sha,
        "contract": {
            "codec": "gzip",
            "compresslevel": 9,
            "mtime": 0,
            "deterministic_proxy": True,
            "included_in_pareto": False,
            "proxy_not_wire_truth": True,
        },
        "evidence_status": "engineering_observation",
        "world_laws": {
            "compressed_bytes_are_not_network_load": True,
            "one_transfer_is_not_retry_amplification": True,
            "measurement_does_not_imply_fitness": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True)
    parser.add_argument("--renderer-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    data = Path(args.asset).read_bytes()
    result = measure(data, args.renderer_id)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "renderer_id": result["renderer_id"],
        "raw_bytes": result["raw_bytes"],
        "gzip_bytes": result["gzip_bytes"],
        "compression_ratio": result["compression_ratio"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
