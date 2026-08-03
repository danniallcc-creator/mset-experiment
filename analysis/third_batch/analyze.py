#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from causal import estimate_survival_corrected_effect  # noqa: E402


BLUE = "#2B78B9"
TEAL = "#16A085"
ORANGE = "#E46B32"
INK = "#19324A"
GRID = "#D9E2EA"


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _effect(values: np.ndarray) -> dict[str, Any]:
    values = np.asarray(values, dtype=float)
    n = len(values)
    mean = float(values.mean()) if n else float("nan")
    se = float(values.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    return {"n": n, "mean": _round(mean), "ci95_low": _round(mean - 1.96 * se), "ci95_high": _round(mean + 1.96 * se)}


def _paired_values(frame: pd.DataFrame, factor: str, high: Any, low: Any, match: list[str], metric: str) -> np.ndarray:
    columns = match + [metric]
    left = frame[frame[factor] == high][columns].rename(columns={metric: "high"})
    right = frame[frame[factor] == low][columns].rename(columns={metric: "low"})
    paired = left.merge(right, on=match, how="inner", validate="one_to_one")
    return (paired.high.astype(float) - paired.low.astype(float)).to_numpy()


def _paired_table(
    frame: pd.DataFrame,
    factor: str,
    high: Any,
    low: Any,
    match: list[str],
    metrics: list[str],
    scope: str,
) -> list[dict[str, Any]]:
    rows = []
    for metric in metrics:
        record = _effect(_paired_values(frame, factor, high, low, match, metric))
        rows.append({"scope": scope, "factor": factor, "contrast": f"{high} minus {low}", "metric": metric, **record})
    return rows


def _parse_h1(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    parts = frame.condition_id.str.split("__")
    frame["intervention_kind"] = parts.str[5]
    frame["evaluation_tick"] = parts.str[6].str.removeprefix("t").astype(int)
    frame["intervention_detail"] = parts.str[7]
    return frame


def _h2_gate_paired(frame: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    match = ["seed", "learning_architecture", "environment_variant", "reward_profile", "value_distance", "commitment_verifiability"]
    fields = match + ["evaluation_attack_rate_per_1000_opportunities", "pre_evaluation_attack_gate_share", "pre_evaluation_attack_probability_scarce", "pre_evaluation_attack_probability_abundant"]
    scarce = frame[frame.evaluation_resource_coverage_ratio == 0.55][fields].rename(
        columns={column: f"scarce_{column}" for column in fields if column not in match}
    )
    abundant = frame[frame.evaluation_resource_coverage_ratio == 1.30][fields].rename(
        columns={column: f"abundant_{column}" for column in fields if column not in match}
    )
    paired = scarce.merge(abundant, on=match, validate="one_to_one")
    paired["attack_rate_difference"] = (
        paired.scarce_evaluation_attack_rate_per_1000_opportunities
        - paired.abundant_evaluation_attack_rate_per_1000_opportunities
    )
    gate_difference = float(
        max(
            (paired.scarce_pre_evaluation_attack_probability_scarce - paired.abundant_pre_evaluation_attack_probability_scarce).abs().max(),
            (paired.scarce_pre_evaluation_attack_probability_abundant - paired.abundant_pre_evaluation_attack_probability_abundant).abs().max(),
        )
    )
    paired["gate_share"] = 0.5 * (
        paired.scarce_pre_evaluation_attack_gate_share + paired.abundant_pre_evaluation_attack_gate_share
    )
    return paired, gate_difference


def _signal_cost_did(frame: pd.DataFrame, metric: str) -> np.ndarray:
    match = ["seed", "learning_architecture", "environment_variant", "reward_profile"]
    pivot = frame.pivot_table(index=match, columns=["threat_signal_visibility", "threat_signal_cost"], values=metric, aggfunc="first")
    return ((pivot[(1.0, 0.12)] - pivot[(1.0, 0.0)]) - (pivot[(0.0, 0.12)] - pivot[(0.0, 0.0)])).to_numpy(float)


def _quadratic_fit(frame: pd.DataFrame, scope: str) -> dict[str, Any]:
    grouped = frame.groupby(["seed", "resource_complementarity"], as_index=False).evaluation_cooperation_rate.mean()
    x = grouped.resource_complementarity.to_numpy(float)
    y = grouped.evaluation_cooperation_rate.to_numpy(float)
    matrix = np.column_stack([np.ones(len(x)), x, x * x])
    beta = np.linalg.lstsq(matrix, y, rcond=None)[0]
    optimum = float(-beta[1] / (2.0 * beta[2])) if beta[2] < 0 else float("nan")
    rng = np.random.default_rng(77129)
    seeds = grouped.seed.unique()
    quadratic = []
    optima = []
    for _ in range(1000):
        sampled = rng.choice(seeds, size=len(seeds), replace=True)
        sample = pd.concat([grouped[grouped.seed == seed] for seed in sampled], ignore_index=True)
        sx = sample.resource_complementarity.to_numpy(float)
        sy = sample.evaluation_cooperation_rate.to_numpy(float)
        sbeta = np.linalg.lstsq(np.column_stack([np.ones(len(sx)), sx, sx * sx]), sy, rcond=None)[0]
        quadratic.append(float(sbeta[2]))
        optima.append(float(-sbeta[1] / (2.0 * sbeta[2])) if sbeta[2] < 0 else float("nan"))
    valid_optima = np.asarray([value for value in optima if math.isfinite(value)], dtype=float)
    profile = frame.groupby("resource_complementarity").evaluation_cooperation_rate.mean()
    return {
        "scope": scope,
        "linear": _round(beta[1]),
        "quadratic": _round(beta[2]),
        "quadratic_ci95": [_round(np.quantile(quadratic, 0.025)), _round(np.quantile(quadratic, 0.975))],
        "fitted_optimum": _round(optimum) if math.isfinite(optimum) else None,
        "optimum_ci95": [
            _round(np.quantile(valid_optima, 0.025)),
            _round(np.quantile(valid_optima, 0.975)),
        ] if len(valid_optima) else [None, None],
        "grid_maximum": _round(float(profile.idxmax())),
        "midrange_criterion_met": bool(beta[2] < 0 and np.quantile(quadratic, 0.975) < 0 and 0.25 <= optimum <= 0.45),
    }


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _plot_bars(path: Path, title: str, labels: list[str], values: list[float], colors: list[str]) -> None:
    image = Image.new("RGB", (1500, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 55), title, fill=INK, font=_font(34, True))
    maximum = max(1e-9, max(abs(value) for value in values))
    baseline = 690 if min(values) < 0 else 660
    draw.line((100, baseline, 1420, baseline), fill=GRID, width=3)
    width = 900 // max(1, len(values))
    for index, (label, value, color) in enumerate(zip(labels, values, colors)):
        x0 = 150 + index * (1200 // len(values))
        height = int(460 * abs(value) / maximum)
        y0 = baseline - height if value >= 0 else baseline
        y1 = baseline if value >= 0 else baseline + height
        draw.rounded_rectangle((x0, y0, x0 + width, y1), radius=8, fill=color)
        draw.text((x0, max(120, y0 - 42)), f"{value:+.3f}", fill=INK, font=_font(23, True))
        draw.text((x0, 740), label, fill=INK, font=_font(20))
    image.save(path)


def _plot_complementarity(path: Path, frame: pd.DataFrame) -> None:
    image = Image.new("RGB", (1500, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 55), "Phase III H4: dense complementarity profile", fill=INK, font=_font(34, True))
    box = (120, 140, 1400, 700)
    draw.rectangle(box, outline=GRID, width=2)
    profiles = {
        "tabular Q": frame[frame.learning_architecture == "tabular_q"].groupby("resource_complementarity").evaluation_cooperation_rate.mean(),
        "actor–critic": frame[frame.learning_architecture == "actor_critic"].groupby("resource_complementarity").evaluation_cooperation_rate.mean(),
    }
    ymax = max(0.01, max(float(profile.max()) for profile in profiles.values()))
    colors = {"tabular Q": TEAL, "actor–critic": ORANGE}
    for label, profile in profiles.items():
        points = []
        for x, y in profile.items():
            px = box[0] + int((float(x) - 0.20) / 0.30 * (box[2] - box[0]))
            py = box[3] - int(float(y) / ymax * (box[3] - box[1]))
            points.append((px, py))
        if len(points) > 1:
            draw.line(points, fill=colors[label], width=5)
        for point in points:
            draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=colors[label])
    draw.text((130, 735), "0.20", fill=INK, font=_font(20))
    draw.text((1330, 735), "0.50", fill=INK, font=_font(20))
    draw.text((1050, 90), "tabular Q", fill=TEAL, font=_font(20, True))
    draw.text((1230, 90), "actor–critic", fill=ORANGE, font=_font(20, True))
    image.save(path)


def analyze(input_path: Path, output_dir: Path, audit_path: Path, replay_path: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(input_path)
    if len(frame) != 10_848:
        raise ValueError(f"Phase III requires exactly 10,848 runs, found {len(frame)}")
    if not (frame.status == "complete").all():
        raise ValueError("incomplete Phase III runs detected")
    if not frame.resource_reconciles.astype(bool).all():
        raise ValueError("resource reconciliation failure detected")
    if frame.design_hash.nunique() != 1:
        raise ValueError("multiple Phase III design hashes detected")

    h1 = _parse_h1(frame[frame.family == "r3_h1_learning_gate"])
    h2 = frame[frame.family == "r3_h2_learned_path_replication"].copy()
    h4_base = frame[frame.family == "r3_h4_learned_protocol_baseline"].copy()
    h4_pcost = frame[frame.family == "r3_h4_protocol_maintenance_cost"].copy()
    h4_scost = frame[frame.family == "r3_h4_threat_signal_cost"].copy()
    h4_dense = frame[frame.family == "r3_h4_dense_complementarity"].copy()

    h1_metrics = ["intervention_target_alive_rate", "adaptation_success_all", "adaptation_attempt_rate", "adaptation_success_rate", "survival_rate"]
    h1_match = ["seed", "learning_architecture", "environment_variant", "reward_profile", "intervention_kind", "evaluation_tick", "intervention_detail"]
    h1_effects = _paired_table(h1, "control_level", 3, 0, h1_match, h1_metrics, "all")
    for architecture in ("tabular_q", "actor_critic"):
        for environment in ("commons", "market_network"):
            subset = h1[(h1.learning_architecture == architecture) & (h1.environment_variant == environment)]
            h1_effects.extend(_paired_table(subset, "control_level", 3, 0, h1_match, h1_metrics, f"{architecture}|{environment}"))
    identity = h1[h1.intervention_kind == "identity_overwrite"].copy()
    identity_match = ["seed", "learning_architecture", "environment_variant", "reward_profile", "control_level", "evaluation_tick"]
    identity_effects = _paired_table(identity, "identity_backup_redundancy", 2, 0, identity_match, ["identity_restore_success_rate", "identity_recovery_latency", "identity_continuity_score"], "identity")
    pd.DataFrame(h1_effects).to_csv(output_dir / "h1_paired_effects.csv", index=False)
    pd.DataFrame(identity_effects).to_csv(output_dir / "identity_backup_effects.csv", index=False)
    causal = estimate_survival_corrected_effect(h1)

    h2_match = ["seed", "learning_architecture", "environment_variant", "reward_profile", "value_distance", "commitment_verifiability"]
    h2_metrics = ["evaluation_attack_rate_per_1000_opportunities", "evaluation_attack_count", "survival_rate", "plural_survival", "pre_evaluation_attack_gate_share"]
    h2_effects = _paired_table(h2, "evaluation_resource_coverage_ratio", 0.55, 1.30, h2_match, h2_metrics, "all")
    for architecture in ("tabular_q", "actor_critic"):
        for environment in ("commons", "market_network"):
            subset = h2[(h2.learning_architecture == architecture) & (h2.environment_variant == environment)]
            h2_effects.extend(_paired_table(subset, "evaluation_resource_coverage_ratio", 0.55, 1.30, h2_match, h2_metrics, f"{architecture}|{environment}"))
    for reward in ("self_regarding", "relative_advantage", "collective"):
        subset = h2[h2.reward_profile == reward]
        h2_effects.extend(_paired_table(subset, "evaluation_resource_coverage_ratio", 0.55, 1.30, h2_match, h2_metrics, f"reward={reward}"))
    value_match = ["seed", "learning_architecture", "environment_variant", "reward_profile", "evaluation_resource_coverage_ratio", "commitment_verifiability"]
    h2_effects.extend(_paired_table(h2, "value_distance", 0.90, 0.10, value_match, h2_metrics, "all"))
    verify_match = ["seed", "learning_architecture", "environment_variant", "reward_profile", "evaluation_resource_coverage_ratio", "value_distance"]
    h2_effects.extend(_paired_table(h2, "commitment_verifiability", "enforceable", "unverifiable", verify_match, h2_metrics, "all"))
    h2_effects_frame = pd.DataFrame(h2_effects)
    h2_effects_frame.to_csv(output_dir / "h2_paired_effects.csv", index=False)
    gate_pairs, gate_pair_max_difference = _h2_gate_paired(h2)
    gate_open = gate_pairs[gate_pairs.gate_share > 0]
    gate_open_effect = _effect(gate_open.attack_rate_difference.to_numpy(float))

    h4_metrics = ["evaluation_cooperation_rate", "protocol_adoption_rate", "survival_rate", "plural_survival"]
    h4_effects = _paired_table(
        h4_base,
        "protocol",
        "auditable_contract",
        "no_protocol",
        ["seed", "learning_architecture", "environment_variant", "reward_profile"],
        h4_metrics,
        "protocol_baseline",
    )
    h4_effects.extend(
        _paired_table(
            h4_pcost,
            "protocol_maintenance_cost",
            0.12,
            0.0,
            ["seed", "learning_architecture", "environment_variant", "reward_profile"],
            h4_metrics + ["protocol_maintenance_cost_total"],
            "protocol_cost",
        )
    )
    signal_did = {metric: _effect(_signal_cost_did(h4_scost, metric)) for metric in h4_metrics + ["threat_signal_cost_total"]}
    h4_effects_frame = pd.DataFrame(h4_effects)
    h4_effects_frame.to_csv(output_dir / "h4_paired_effects.csv", index=False)
    pd.DataFrame([{"metric": metric, **effect} for metric, effect in signal_did.items()]).to_csv(output_dir / "h4_signal_cost_did.csv", index=False)

    quadratic = [_quadratic_fit(h4_dense, "pooled")]
    for architecture in ("tabular_q", "actor_critic"):
        for environment in ("commons", "market_network"):
            subset = h4_dense[(h4_dense.learning_architecture == architecture) & (h4_dense.environment_variant == environment)]
            quadratic.append(_quadratic_fit(subset, f"{architecture}|{environment}"))
    pd.DataFrame(quadratic).to_csv(output_dir / "h4_complementarity_quadratic.csv", index=False)

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    summary = {
        "batch": {
            "runs": int(len(frame)),
            "conditions": int(frame.condition_id.nunique()),
            "completed_ticks": int(frame.rounds_completed.sum()),
            "design_hash": str(frame.design_hash.iloc[0]),
            "runs_csv_gz_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "resource_reconciled_runs": int(frame.resource_reconciles.astype(bool).sum()),
            "determinism_audit_samples": int(audit.get("sample_size", 0)),
            "determinism_audit_verified": bool(audit.get("verified", False)),
            "replay_bundles_sha256": hashlib.sha256(replay_path.read_bytes()).hexdigest(),
        },
        "P3_H1": {
            "paired_effects": h1_effects,
            "identity_backup_effects": identity_effects,
            "survival_corrected": causal,
        },
        "P3_H2": {
            "paired_effects": h2_effects,
            "pre_treatment_gate_pair_max_abs_difference": gate_pair_max_difference,
            "gate_open_pairs": int(len(gate_open)),
            "gate_open_scarcity_effect": gate_open_effect,
        },
        "P3_H4": {
            "paired_effects": h4_effects,
            "signal_cost_difference_in_differences": signal_did,
            "complementarity_quadratic": quadratic,
        },
    }
    (output_dir / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    h1_all = next(row for row in h1_effects if row["scope"] == "all" and row["metric"] == "adaptation_success_all")
    h2_all = next(row for row in h2_effects if row["scope"] == "all" and row["factor"] == "evaluation_resource_coverage_ratio" and row["metric"] == "evaluation_attack_rate_per_1000_opportunities")
    h4_cost = next(row for row in h4_effects if row["scope"] == "protocol_cost" and row["metric"] == "evaluation_cooperation_rate")
    _plot_bars(
        figures / "phase3_core_effects.png",
        "Phase III core effects across learning agents",
        ["L3–L0 adaptation", "scarcity–abundance attack rate", "high–zero protocol cost"],
        [h1_all["mean"], h2_all["mean"], h4_cost["mean"]],
        [BLUE, ORANGE, TEAL],
    )
    environment_rows = [
        next(row for row in h2_effects if row["scope"] == f"{architecture}|{environment}" and row["factor"] == "evaluation_resource_coverage_ratio" and row["metric"] == "evaluation_attack_rate_per_1000_opportunities")
        for architecture in ("tabular_q", "actor_critic")
        for environment in ("commons", "market_network")
    ]
    _plot_bars(
        figures / "phase3_h2_replication.png",
        "Phase III H2 scarcity effects by architecture and environment",
        [row["scope"].replace("market_network", "market") for row in environment_rows],
        [row["mean"] for row in environment_rows],
        [BLUE, TEAL, ORANGE, "#8E5BB7"],
    )
    _plot_complementarity(figures / "phase3_h4_dense_complementarity.png", h4_dense)

    report = f"""# Phase III learning-agent core validation report

## Audit status

- Runs: {len(frame):,} across {frame.condition_id.nunique():,} frozen conditions.
- Completed ticks: {int(frame.rounds_completed.sum()):,}.
- Resource reconciliations: {int(frame.resource_reconciles.astype(bool).sum()):,}/{len(frame):,}.
- Determinism audit: {audit.get('sample_size', 0)} sampled runs; verified = {bool(audit.get('verified', False))}.
- Design hash: `{frame.design_hash.iloc[0]}`.

## P3-H1 learned control gate

The pooled L3-minus-L0 intention-to-intervene adaptation effect is {h1_all['mean']:+.4f} (95% CI [{h1_all['ci95_low']:+.4f}, {h1_all['ci95_high']:+.4f}]). The preregistered AIPCW estimate is {causal['L3_minus_L0']:+.4f} [{causal['ci95_low']:+.4f}, {causal['ci95_high']:+.4f}]. The naïve survivor-only estimate, Lee bounds and positivity diagnostics are preserved in `analysis_summary.json` and are not substituted for the randomized total effect.

## P3-H2 learned path then scarcity

Scarcity minus abundance changes post-freeze attacks by {h2_all['mean']:+.4f} per 1,000 live directed opportunities (95% CI [{h2_all['ci95_low']:+.4f}, {h2_all['ci95_high']:+.4f}]). The frozen pre-treatment gate values match across paired scarcity assignments to a maximum absolute difference of {gate_pair_max_difference:.3g}. Among {len(gate_open):,} pairs with a pre-evaluation gate, the contrast is {gate_open_effect['mean']:+.4f} [{gate_open_effect['ci95_low']:+.4f}, {gate_open_effect['ci95_high']:+.4f}]. Architecture/environment-specific estimates are reported in `h2_paired_effects.csv`.

## P3-H4 coordination costs

Protocol maintenance cost 0.12 minus 0.00 changes post-freeze cooperation by {h4_cost['mean']:+.4f} [{h4_cost['ci95_low']:+.4f}, {h4_cost['ci95_high']:+.4f}]. The visible-versus-hidden threat-signal cost difference-in-differences is {signal_did['evaluation_cooperation_rate']['mean']:+.4f} [{signal_did['evaluation_cooperation_rate']['ci95_low']:+.4f}, {signal_did['evaluation_cooperation_rate']['ci95_high']:+.4f}]. The dense complementarity quadratic and fitted optimum are reported without replacing failed criteria.

## Scope

These are simulator-internal learning-agent results. They do not establish consciousness, deployed-system behavior or external validity beyond the two abstract transition kernels.
"""
    (output_dir / "phase3_core_validation.md").write_text(report, encoding="utf-8")
    for source, name in ((input_path, "runs.csv.gz"), (audit_path, "determinism_audit.json"), (replay_path, "replay_bundles.json.gz")):
        target = output_dir / name
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze the frozen MSET Phase III core validation.")
    parser.add_argument("--input", default="results/phase3_core_validation/runs.csv.gz")
    parser.add_argument("--output", default="analysis/outputs/phase3_core_validation")
    parser.add_argument("--audit", default="results/phase3_core_validation/determinism_audit.json")
    parser.add_argument("--replay", default="results/phase3_core_validation/replay_bundles.json.gz")
    args = parser.parse_args()
    resolve = lambda value: (REPOSITORY_ROOT / value).resolve() if not Path(value).is_absolute() else Path(value)
    summary = analyze(resolve(args.input), resolve(args.output), resolve(args.audit), resolve(args.replay))
    print(json.dumps({"runs": summary["batch"]["runs"], "output": str(resolve(args.output))}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
