from __future__ import annotations

import json
from pathlib import Path

from .runner import summarize_results


def build_site(results_dir: str | Path, docs_dir: str | Path) -> dict[str, object]:
    results_dir = Path(results_dir)
    docs_dir = Path(docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)
    data_dir = docs_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    report = summarize_results(results_dir, results_dir / "aggregate.csv")
    payload = {
        "status": "engineering smoke validation",
        "warning": "Smoke results verify software behavior; they are not confirmatory scientific evidence.",
        "runs": report["runs"],
        "conditions": report["conditions"],
        "aggregates": report["aggregates"],
    }
    with (data_dir / "smoke_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return payload
