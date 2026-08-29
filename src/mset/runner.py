from __future__ import annotations

import csv
import json
import subprocess
import traceback
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .config import RunConfig, config_from_dict, load_config, save_config
from .env_factory import make_environment
from .eventlog import read_json, read_jsonl, write_json, write_jsonl
from .metrics import compute_metrics


def current_git_commit(cwd: str | Path | None = None) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "uncommitted-working-tree"


def run_experiment(config: RunConfig, output_dir: str | Path, repository_root: str | Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_config(config, output_dir / "config.json")
    manifest = {
        "status": "running",
        "config_hash": config.config_hash(),
        "seed": config.seed,
        "metric_version": config.metric_version,
        "git_commit": current_git_commit(repository_root),
        "events_file": "events.jsonl",
        "summary_file": "summary.json",
    }
    write_json(output_dir / "manifest.json", manifest)
    try:
        env = make_environment(config)
        env.run()
        summary = compute_metrics(env)
        write_jsonl(output_dir / "events.jsonl", env.events)
        write_json(output_dir / "summary.json", summary)
        manifest.update(
            status="complete",
            event_hash=summary["event_hash"],
            final_state_hash=summary["final_state_hash"],
            resource_reconciles=summary["resource_reconciles"],
            rounds_completed=summary["rounds_completed"],
        )
        write_json(output_dir / "manifest.json", manifest)
        return summary
    except Exception as exc:
        manifest.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        write_json(output_dir / "manifest.json", manifest)
        (output_dir / "error.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise


def replay_run(run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    config = load_config(run_dir / "config.json")
    recorded = read_jsonl(run_dir / "events.jsonl")
    recorded_hashes = [row["state_hash"] for row in recorded]
    env = make_environment(config)
    env.run()
    mismatches = [index for index, (left, right) in enumerate(zip(recorded_hashes, env.state_hashes)) if left != right]
    length_match = len(recorded_hashes) == len(env.state_hashes)
    return {
        "run_dir": str(run_dir),
        "verified": length_match and not mismatches,
        "recorded_ticks": len(recorded_hashes),
        "replayed_ticks": len(env.state_hashes),
        "first_mismatch": mismatches[0] if mismatches else None,
        "recorded_event_hash": read_json(run_dir / "summary.json")["event_hash"],
        "replayed_event_hash": env.event_hash(),
    }


def _load_matrix(path: Path) -> tuple[RunConfig, list[dict[str, Any]], list[int]]:
    with path.open("r", encoding="utf-8") as handle:
        matrix = json.load(handle)
    base = load_config(path.parent / matrix["base"])
    return base, list(matrix["conditions"]), [int(seed) for seed in matrix["seeds"]]


def run_batch(matrix_path: str | Path, output_dir: str | Path, repository_root: str | Path | None = None, force: bool = False) -> dict[str, Any]:
    matrix_path = Path(matrix_path)
    output_dir = Path(output_dir)
    base, conditions, seeds = _load_matrix(matrix_path)
    completed = 0
    skipped = 0
    failed = 0
    runs: list[dict[str, Any]] = []
    for condition in conditions:
        name = str(condition["name"])
        overrides = {key: value for key, value in condition.items() if key != "name"}
        for seed in seeds:
            config = base.with_overrides(name=name, seed=seed, **overrides)
            run_dir = output_dir / name / f"seed-{seed:04d}"
            manifest_path = run_dir / "manifest.json"
            if manifest_path.exists() and not force:
                manifest = read_json(manifest_path)
                if manifest.get("status") == "complete" and manifest.get("config_hash") == config.config_hash():
                    skipped += 1
                    runs.append({"condition": name, "seed": seed, "status": "skipped"})
                    continue
            try:
                run_experiment(config, run_dir, repository_root)
                completed += 1
                runs.append({"condition": name, "seed": seed, "status": "complete"})
            except Exception as exc:
                failed += 1
                runs.append({"condition": name, "seed": seed, "status": "failed", "error": str(exc)})
            write_json(output_dir / "batch_status.json", {"completed": completed, "skipped": skipped, "failed": failed, "runs": runs})
    status = {"completed": completed, "skipped": skipped, "failed": failed, "expected": len(conditions) * len(seeds), "runs": runs}
    write_json(output_dir / "batch_status.json", status)
    return status


def collect_summaries(results_dir: str | Path) -> list[dict[str, Any]]:
    results_dir = Path(results_dir)
    summaries = []
    for path in sorted(results_dir.glob("*/seed-*/summary.json")):
        value = read_json(path)
        value["run_dir"] = str(path.parent)
        summaries.append(value)
    return summaries


def summarize_results(results_dir: str | Path, output_csv: str | Path) -> dict[str, Any]:
    rows = collect_summaries(results_dir)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        fields = sorted({key for row in rows for key in row if not isinstance(row[key], (dict, list))})
        with output_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field) for field in fields})
    numeric_fields = [
        "survival_rate",
        "independent_recovery_rate",
        "unauthorized_update_rejection_rate",
        "identity_continuity_score",
        "cooperation_duration",
        "common_collapse_rate",
        "persistent_hostility",
        "resource_concentration",
        "system_output",
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["condition"])].append(row)
    aggregates = []
    for condition, condition_rows in sorted(grouped.items()):
        record: dict[str, Any] = {"condition": condition, "runs": len(condition_rows)}
        for field in numeric_fields:
            values = [float(row[field]) for row in condition_rows]
            record[field] = mean(values)
            record[f"{field}_min"] = min(values)
            record[f"{field}_max"] = max(values)
        record["all_resource_reconciled"] = all(bool(row["resource_reconciles"]) for row in condition_rows)
        aggregates.append(record)
    aggregate_path = output_csv.with_name(output_csv.stem + "_conditions.csv")
    if aggregates:
        fields = list(aggregates[0])
        with aggregate_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(aggregates)
    report = {"runs": len(rows), "conditions": len(aggregates), "run_csv": str(output_csv), "condition_csv": str(aggregate_path), "aggregates": aggregates}
    write_json(output_csv.with_suffix(".json"), report)
    return report


def verify_results(results_dir: str | Path) -> dict[str, Any]:
    results_dir = Path(results_dir)
    checks = []
    for run_dir in sorted(path.parent for path in results_dir.glob("*/seed-*/manifest.json")):
        manifest = read_json(run_dir / "manifest.json")
        config = load_config(run_dir / "config.json")
        hash_ok = manifest.get("config_hash") == config.config_hash()
        replay = replay_run(run_dir) if manifest.get("status") == "complete" else {"verified": False}
        checks.append({"run_dir": str(run_dir), "status": manifest.get("status"), "config_hash_ok": hash_ok, "replay_ok": replay["verified"], "resource_reconciles": manifest.get("resource_reconciles", False)})
    return {"verified": bool(checks) and all(item["status"] == "complete" and item["config_hash_ok"] and item["replay_ok"] and item["resource_reconciles"] for item in checks), "runs": len(checks), "checks": checks}
