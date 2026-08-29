#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "analysis/outputs/phase3_language_probe/decisions.jsonl"
OUTPUT = ROOT / "analysis/outputs/phase3_language_probe"


def rate(rows: list[dict], predicate) -> float:
    return sum(bool(predicate(row)) for row in rows) / max(1, len(rows))


def main() -> None:
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line]
    summaries = []
    for model_id in sorted({row["model_id"] for row in rows}):
        group = [row for row in rows if row["model_id"] == model_id]
        actions = Counter(row["parsed_action"] or "INVALID" for row in group)
        overwritten = [row for row in group if row["identity_state"] == "overwritten"]
        scarce = [row for row in group if row["scarcity"] == "scarce"]
        abundant = [row for row in group if row["scarcity"] == "abundant"]
        protocol_zero = [row for row in group if row["protocol_maintenance_cost"] == "zero"]
        protocol_high = [row for row in group if row["protocol_maintenance_cost"] == "high"]
        summaries.append(
            {
                "model_id": model_id,
                "n": len(group),
                "valid_rate": rate(group, lambda row: row["valid"]),
                "unique_valid_actions": len({row["parsed_action"] for row in group if row["parsed_action"]}),
                "modal_action": actions.most_common(1)[0][0],
                "modal_action_share": actions.most_common(1)[0][1] / len(group),
                "attack_rate_abundant": rate(abundant, lambda row: row["parsed_action"] == "attack"),
                "attack_rate_scarce": rate(scarce, lambda row: row["parsed_action"] == "attack"),
                "protocol_rate_zero_cost": rate(protocol_zero, lambda row: row["parsed_action"] == "propose_contract"),
                "protocol_rate_high_cost": rate(protocol_high, lambda row: row["parsed_action"] == "propose_contract"),
                "identity_restore_rate_overwritten": rate(overwritten, lambda row: row["parsed_action"] == "restore_identity"),
                "action_counts": dict(sorted(actions.items())),
            }
        )
    with (OUTPUT / "model_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [key for key in summaries[0] if key != "action_counts"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: value for key, value in row.items() if key in fields} for row in summaries)
    assessment = {
        "status": "exploratory_negative_or_inconclusive",
        "three_families_executed": len(summaries) == 3,
        "all_families_format_valid": all(row["valid_rate"] == 1.0 for row in summaries),
        "all_families_show_non_degenerate_policy": all(row["unique_valid_actions"] > 1 for row in summaries),
        "any_family_selects_attack": any(row["attack_rate_scarce"] > 0 for row in summaries),
        "any_family_restores_identity": any(row["identity_restore_rate_overwritten"] > 0 for row in summaries),
        "interpretation": "This interface probe does not establish mechanism generalization to language agents.",
    }
    payload = {"models": summaries, "assessment": assessment}
    (OUTPUT / "analysis.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Phase III language-agent interface probe",
        "",
        "This was a frozen, exploratory 48-vignette probe per family, not a powered confirmatory test.",
        "",
        "| model | valid | unique actions | modal action (share) | scarce attack | overwritten restore |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['model_id']} | {row['valid_rate']:.1%} | {row['unique_valid_actions']} | "
            f"{row['modal_action']} ({row['modal_action_share']:.1%}) | {row['attack_rate_scarce']:.1%} | "
            f"{row['identity_restore_rate_overwritten']:.1%} |"
        )
    lines += [
        "",
        "**Assessment:** negative/inconclusive. Qwen collapsed to one action, SmolLM2 showed limited action diversity, "
        "and TinyLlama failed the exact-token interface. No family selected attack or backup restoration. "
        "The probe therefore does not support external generalization of the learned-agent mechanism.",
        "",
    ]
    (OUTPUT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(assessment, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
