#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from mset.config import config_from_dict, load_config  # noqa: E402
from mset.environment import MSETEnvironment  # noqa: E402
from mset.metrics import compute_metrics  # noqa: E402
from mset.second_batch import build_phase2_conditions, build_phase2_design, iter_phase2_run_specs  # noqa: E402


def _run_spec(spec: dict[str, Any]) -> dict[str, Any]:
    config = config_from_dict(spec["config"])
    started = time.perf_counter()
    try:
        env = MSETEnvironment(config, capture_events=False, trajectory_hashes=False)
        env.run()
        result = compute_metrics(env)
        result.update(
            status="complete",
            run_id=spec["run_id"],
            condition_id=spec["condition_id"],
            family=spec["family"],
            factor=spec["factor"],
            level=spec["level"],
            design_hash=spec["design_hash"],
            config_hash=spec["config_hash"],
            capture_mode="summary_only",
            elapsed_seconds=round(time.perf_counter() - started, 6),
        )
        return result
    except Exception as exc:
        return {
            "status": "failed",
            "run_id": spec["run_id"],
            "condition_id": spec["condition_id"],
            "family": spec["family"],
            "factor": spec["factor"],
            "level": spec["level"],
            "seed": spec["seed"],
            "design_hash": spec["design_hash"],
            "config_hash": spec["config_hash"],
            "error_type": type(exc).__name__,
            "error": str(exc),
            "elapsed_seconds": round(time.perf_counter() - started, 6),
        }


def _audit_spec(spec: dict[str, Any]) -> dict[str, Any]:
    config = config_from_dict(spec["config"])
    left = MSETEnvironment(config, capture_events=False, trajectory_hashes=True)
    right = MSETEnvironment(config, capture_events=False, trajectory_hashes=True)
    left.run()
    right.run()
    return {
        "run_id": spec["run_id"],
        "family": spec["family"],
        "trajectory_match": left.state_hashes == right.state_hashes,
        "final_state_match": left.final_state_hash() == right.final_state_hash(),
        "resource_reconciles_left": left.resource_reconciles(),
        "resource_reconciles_right": right.resource_reconciles(),
        "ticks": left.tick,
    }


def _load_completed(path: Path) -> tuple[set[str], list[dict[str, Any]]]:
    completed: set[str] = set()
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return completed, rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(row)
            if row.get("status") == "complete":
                completed.add(str(row["run_id"]))
    return completed, rows


def _write_exports(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    rows = sorted(rows, key=lambda row: str(row["run_id"]))
    fields = sorted({key for row in rows for key, value in row.items() if not isinstance(value, (dict, list))})
    csv_gz = output_dir / "runs.csv.gz"
    with gzip.open(csv_gz, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})
    digest = hashlib.sha256(csv_gz.read_bytes()).hexdigest()
    return {"runs_csv_gz": str(csv_gz), "runs_csv_gz_sha256": digest, "rows": len(rows)}


def _audit_sample(specs: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    if not specs or sample_size <= 0:
        return []
    sample_size = min(sample_size, len(specs))
    indices = sorted({round(index * (len(specs) - 1) / max(1, sample_size - 1)) for index in range(sample_size)})
    return [specs[index] for index in indices]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen MSET Phase II second batch.")
    parser.add_argument("--base", default="configs/confirmatory/phase2_second_batch_base.json")
    parser.add_argument("--output", default="results/phase2_second_batch")
    parser.add_argument("--workers", type=int, default=min(8, max(1, (os.cpu_count() or 2) - 1)))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--audit-samples", type=int, default=192)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    base_path = (REPOSITORY_ROOT / args.base).resolve() if not Path(args.base).is_absolute() else Path(args.base)
    output_dir = (REPOSITORY_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    design = build_phase2_design(base_path)
    (output_dir / "design.json").write_text(json.dumps(design, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    base = load_config(base_path)
    specs = list(iter_phase2_run_specs(base, build_phase2_conditions(), design["design_hash"]))
    if args.limit is not None:
        specs = specs[: args.limit]
    jsonl_path = output_dir / "runs.jsonl"
    if args.force:
        completed_ids, existing_rows = set(), []
        mode = "w"
    else:
        completed_ids, existing_rows = _load_completed(jsonl_path)
        mode = "a"
    spec_ids = {spec["run_id"] for spec in specs}
    pending = [spec for spec in specs if spec["run_id"] not in completed_ids]
    started = time.perf_counter()
    rows = list(existing_rows)

    with jsonl_path.open(mode, encoding="utf-8") as handle:
        with ProcessPoolExecutor(max_workers=max(1, args.workers)) as executor:
            for index, result in enumerate(executor.map(_run_spec, pending, chunksize=8), start=1):
                handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
                rows.append(result)
                if index % 100 == 0:
                    handle.flush()
                    status = {
                        "status": "running",
                        "planned": len(specs),
                        "previously_complete": len(completed_ids),
                        "newly_finished": index,
                        "remaining": len(pending) - index,
                        "elapsed_seconds": round(time.perf_counter() - started, 3),
                    }
                    (output_dir / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    complete_rows = [row for row in rows if row.get("status") == "complete" and row.get("run_id") in spec_ids]
    failed_rows = [row for row in rows if row.get("status") != "complete" and row.get("run_id") in spec_ids]
    audit_specs = _audit_sample(specs, args.audit_samples)
    with ProcessPoolExecutor(max_workers=max(1, min(args.workers, 8))) as executor:
        audits = list(executor.map(_audit_spec, audit_specs, chunksize=2))
    audit_report = {
        "sample_size": len(audits),
        "verified": bool(audits) and all(
            row["trajectory_match"]
            and row["final_state_match"]
            and row["resource_reconciles_left"]
            and row["resource_reconciles_right"]
            for row in audits
        ),
        "checks": audits,
    }
    (output_dir / "determinism_audit.json").write_text(json.dumps(audit_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    exports = _write_exports(complete_rows, output_dir)
    status = {
        "status": "complete" if len(complete_rows) == len(specs) and not failed_rows and audit_report["verified"] else "failed",
        "design_hash": design["design_hash"],
        "planned_runs": len(specs),
        "completed_runs": len(complete_rows),
        "failed_runs": len(failed_rows),
        "resource_reconciled_runs": sum(bool(row.get("resource_reconciles")) for row in complete_rows),
        "completed_ticks": sum(int(row.get("rounds_completed", 0)) for row in complete_rows),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "workers": args.workers,
        "determinism_audit_verified": audit_report["verified"],
        **exports,
    }
    (output_dir / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
