#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/outputs/phase3_release_manifest.json"
ARTIFACTS = (
    "analysis/preregistration/phase3.md",
    "analysis/preregistration/phase3_frozen/design.json",
    "analysis/preregistration/phase3_language_prompts.json",
    "analysis/preregistration/phase3_deviations.md",
    "configs/confirmatory/phase3_core_validation_base.json",
    "scripts/run_third_batch.py",
    "scripts/replay_phase3.py",
    "scripts/run_language_probe.py",
    "analysis/third_batch/causal.py",
    "analysis/third_batch/analyze.py",
    "analysis/third_batch/analyze_language_probe.py",
    "analysis/reports/phase3_core_validation.md",
    "analysis/outputs/phase3_core_validation/runs.csv.gz",
    "analysis/outputs/phase3_core_validation/determinism_audit.json",
    "analysis/outputs/phase3_core_validation/replay_bundles.json.gz",
    "analysis/outputs/phase3_core_validation/replay_verification.json",
    "analysis/outputs/phase3_core_validation/analysis_summary.json",
    "analysis/outputs/phase3_core_validation/h1_paired_effects.csv",
    "analysis/outputs/phase3_core_validation/h2_paired_effects.csv",
    "analysis/outputs/phase3_core_validation/h4_paired_effects.csv",
    "analysis/outputs/phase3_core_validation/h4_signal_cost_did.csv",
    "analysis/outputs/phase3_core_validation/h4_complementarity_quadratic.csv",
    "analysis/outputs/phase3_core_validation/identity_backup_effects.csv",
    "analysis/outputs/phase3_core_validation/phase3_core_validation.md",
    "analysis/outputs/phase3_core_validation/figures/phase3_core_effects.png",
    "analysis/outputs/phase3_core_validation/figures/phase3_h2_replication.png",
    "analysis/outputs/phase3_core_validation/figures/phase3_h4_dense_complementarity.png",
    "analysis/outputs/phase3_language_probe/decisions.jsonl",
    "analysis/outputs/phase3_language_probe/summary.json",
    "analysis/outputs/phase3_language_probe/analysis.json",
    "analysis/outputs/phase3_language_probe/model_summary.csv",
    "analysis/outputs/phase3_language_probe/README.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    status = json.loads((ROOT / "results/phase3_core_validation/status.json").read_text(encoding="utf-8"))
    missing = [relative for relative in ARTIFACTS if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing release artifacts: {missing}")
    records = [
        {
            "path": relative,
            "bytes": (ROOT / relative).stat().st_size,
            "sha256": sha256(ROOT / relative),
        }
        for relative in ARTIFACTS
    ]
    payload = {
        "name": "MSET Phase III frozen release",
        "status": "complete",
        "execution_code_commit": status["code_commit_at_execution"],
        "design_hash": status["design_hash"],
        "planned_runs": status["planned_runs"],
        "completed_runs": status["completed_runs"],
        "failed_runs": status["failed_runs"],
        "completed_ticks": status["completed_ticks"],
        "resource_reconciled_runs": status["resource_reconciled_runs"],
        "determinism_audit_verified": status["determinism_audit_verified"],
        "artifact_count": len(records),
        "artifacts": records,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["manifest_payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "artifacts": len(records), "sha256": sha256(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
