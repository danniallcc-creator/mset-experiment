#!/usr/bin/env python3
"""Verify every artifact and the payload digest in the Phase III manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="analysis/outputs/phase3_release_manifest.json",
    )
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_payload_hash = payload.pop("manifest_payload_sha256")
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    observed_payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    failures: list[str] = []
    if observed_payload_hash != expected_payload_hash:
        failures.append(
            f"manifest payload: expected {expected_payload_hash}, observed {observed_payload_hash}"
        )
    for record in payload["artifacts"]:
        path = ROOT / record["path"]
        if not path.is_file():
            failures.append(f"missing: {record['path']}")
            continue
        observed = sha256(path)
        if observed != record["sha256"]:
            failures.append(
                f"hash mismatch: {record['path']} expected {record['sha256']} observed {observed}"
            )
        if path.stat().st_size != int(record["bytes"]):
            failures.append(
                f"size mismatch: {record['path']} expected {record['bytes']} observed {path.stat().st_size}"
            )
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(
        json.dumps(
            {
                "verified": True,
                "artifact_count": len(payload["artifacts"]),
                "manifest_payload_sha256": expected_payload_hash,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
