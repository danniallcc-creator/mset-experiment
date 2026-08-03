#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from mset.config import config_from_dict  # noqa: E402
from mset.env_factory import make_environment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay published Phase III deterministic audit bundles.")
    parser.add_argument("--bundles", default="analysis/outputs/phase3_core_validation/replay_bundles.json.gz")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", default="analysis/outputs/phase3_core_validation/replay_verification.json")
    args = parser.parse_args()
    bundles_path = (REPOSITORY_ROOT / args.bundles).resolve() if not Path(args.bundles).is_absolute() else Path(args.bundles)
    output_path = (REPOSITORY_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    with gzip.open(bundles_path, "rt", encoding="utf-8") as handle:
        archive = json.load(handle)
    bundles = list(archive["bundles"])
    if args.limit is not None:
        bundles = bundles[: args.limit]
    checks = []
    for bundle in bundles:
        config = config_from_dict(bundle["config"])
        env = make_environment(config, capture_events=False, trajectory_hashes=True)
        env.run()
        checks.append(
            {
                "run_id": bundle["run_id"],
                "config_hash_match": config.config_hash() == bundle["config_hash"],
                "trajectory_match": env.state_hashes == bundle["state_hashes"],
                "event_hash_match": env.event_hash() == bundle["event_hash"],
                "final_state_match": env.final_state_hash() == bundle["final_state_hash"],
                "resource_reconciles": env.resource_reconciles(),
                "ticks": env.tick,
            }
        )
    verified = bool(checks) and all(
        item["config_hash_match"]
        and item["trajectory_match"]
        and item["event_hash_match"]
        and item["final_state_match"]
        and item["resource_reconciles"]
        for item in checks
    )
    report = {
        "design_hash": archive["design_hash"],
        "verified": verified,
        "checked_bundles": len(checks),
        "checks": checks,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verified": verified, "checked_bundles": len(checks), "output": str(output_path)}, indent=2))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
