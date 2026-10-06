#!/usr/bin/env python3
"""Generate a bounded, deterministic swarm of Purrtocol concept manifests.

"Infinite proliferation" here means a resumable generation process over an
unbounded seed stream. Every invocation is explicitly bounded. Generated rows
remain concepts; this script never registers or promotes them as implemented
artifacts or empirical evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from breed_purrtocol import breed

MAX_BATCH = 4096


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def concept_seed(namespace: str, epoch: int, ordinal: int) -> str:
    return f"{namespace}:epoch={epoch}:ordinal={ordinal}"


def generate_swarm(
    *,
    namespace: str,
    epoch: int,
    start: int,
    count: int,
    parent_variant_id: str,
    origin_repository: str,
    submitted_by: str,
    chain_parent: bool,
) -> list[dict[str, Any]]:
    if not namespace.strip():
        raise ValueError("namespace must not be empty")
    if epoch < 0:
        raise ValueError("epoch must be >= 0")
    if start < 0:
        raise ValueError("start must be >= 0")
    if count < 1 or count > MAX_BATCH:
        raise ValueError(f"count must be between 1 and {MAX_BATCH}")

    manifests: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    current_parent = parent_variant_id

    for ordinal in range(start, start + count):
        seed = concept_seed(namespace, epoch, ordinal)
        manifest = breed(
            seed,
            parent_variant_id=current_parent,
            origin_repository=origin_repository,
            submitted_by=submitted_by,
        )
        variant_id = manifest["variant_id"]
        if variant_id in seen_ids:
            raise RuntimeError(
                "variant_id collision inside batch; change namespace/epoch/start"
            )
        seen_ids.add(variant_id)

        manifest["swarm"] = {
            "schema": "purrtocol-swarm/v1",
            "namespace": namespace,
            "epoch": epoch,
            "ordinal": ordinal,
            "seed_sha256": hashlib.sha256(seed.encode("utf-8")).hexdigest(),
            "chain_parent": chain_parent,
        }
        manifests.append(manifest)

        if chain_parent:
            current_parent = variant_id

    return manifests


def write_swarm(
    manifests: list[dict[str, Any]],
    *,
    output_dir: Path,
    namespace: str,
    epoch: int,
    start: int,
    chain_parent: bool,
    resume: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    reused: list[str] = []

    for manifest in manifests:
        filename = manifest["variant_id"] + ".json"
        path = output_dir / filename
        payload = canonical_json(manifest)

        if path.exists():
            if resume and path.read_text(encoding="utf-8") == payload:
                reused.append(filename)
                continue
            raise FileExistsError(
                f"{path} already exists with non-resumable state; "
                "use a new namespace/epoch/start or remove the stale file"
            )

        path.write_text(payload, encoding="utf-8")
        written.append(filename)

    ids = [manifest["variant_id"] for manifest in manifests]
    index = {
        "schema": "purrtocol-swarm-index/v1",
        "namespace": namespace,
        "epoch": epoch,
        "start": start,
        "count": len(manifests),
        "chain_parent": chain_parent,
        "status": "concept-only",
        "evidence_status": "concept",
        "variant_ids": ids,
        "written_files": written,
        "reused_files": reused,
        "next_start": start + len(manifests),
        "warning": (
            "Generation is not implementation, registry inclusion, endorsement, "
            "or empirical evidence. The genome state space is finite even though "
            "the deterministic seed stream can continue indefinitely."
        ),
    }
    (output_dir / "_swarm_index.json").write_text(
        canonical_json(index), encoding="utf-8"
    )
    return index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", default="purrtocol-infinite")
    ap.add_argument("--epoch", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=32)
    ap.add_argument("--parent", default="PKV-CANONICAL")
    ap.add_argument(
        "--origin-repository",
        default="https://github.com/YOU/YOUR-FORK",
    )
    ap.add_argument("--submitted-by", default="your-handle")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument(
        "--chain-parent",
        action="store_true",
        help="make each generated concept the parent of the next concept",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="reuse byte-identical concept files from an interrupted run",
    )
    args = ap.parse_args()

    manifests = generate_swarm(
        namespace=args.namespace,
        epoch=args.epoch,
        start=args.start,
        count=args.count,
        parent_variant_id=args.parent,
        origin_repository=args.origin_repository,
        submitted_by=args.submitted_by,
        chain_parent=args.chain_parent,
    )
    index = write_swarm(
        manifests,
        output_dir=Path(args.output_dir),
        namespace=args.namespace,
        epoch=args.epoch,
        start=args.start,
        chain_parent=args.chain_parent,
        resume=args.resume,
    )
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
