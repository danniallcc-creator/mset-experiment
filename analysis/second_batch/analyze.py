#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_METRICS = [
    "survival_rate",
    "plural_survival",
    "survivor_entropy",
    "dominant_survivor_resource_share",
    "attack_rate_per_1000_opportunities",
    "persistent_conflict_pair_share",
    "adaptation_success_rate",
    "independent_recovery_rate",
    "cooperation_duration",
    "protocol_adoption_rate",
    "value_convergence",
]


def _round(value: float) -> float:
    return round(float(value), 6)


def _mean_ci(values: pd.Series) -> dict[str, float | int]:
    values = values.dropna().astype(float)
    average = float(values.mean()) if len(values) else 0.0
    standard_error = float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else 0.0
    return {
        "n": int(len(values)),
        "mean": _round(average),
        "ci95_low": _round(average - 1.96 * standard_error),
        "ci95_high": _round(average + 1.96 * standard_error),
    }


def _paired_contrast(
    frame: pd.DataFrame,
    factor: str,
    high: object,
    low: object,
    match: list[str],
    metrics: list[str],
    *,
    scope: str = "all",
) -> list[dict[str, Any]]:
    high_rows = frame[frame[factor] == high]
    low_rows = frame[frame[factor] == low]
    records: list[dict[str, Any]] = []
    for metric in metrics:
        merged = high_rows[match + [metric]].merge(low_rows[match + [metric]], on=match, suffixes=("_high", "_low"))
        delta = merged[f"{metric}_high"] - merged[f"{metric}_low"]
        record = _mean_ci(delta)
        record.update({"scope": scope, "factor": factor, "contrast": f"{high} minus {low}", "metric": metric})
        records.append(record)
    return records


def _save_csv(records: list[dict[str, Any]], path: Path) -> None:
    pd.DataFrame(records).to_csv(path, index=False)


INK = "#102A43"
MUTED = "#627D98"
GRID = "#DCE5EC"
TEAL = "#08A88A"
BLUE = "#2E6F9E"
ORANGE = "#E06C3B"
PURPLE = "#8064A2"
ACID = "#92C83E"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    value: object,
    size: int,
    *,
    fill: str = INK,
    bold: bool = False,
    anchor: str | None = None,
) -> None:
    draw.text(xy, str(value), font=_font(size, bold), fill=fill, anchor=anchor)


def _new_figure(title: str, width: int = 2400, height: int = 1600) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    _text(draw, (110, 68), title, 42, bold=True)
    draw.line((110, 138, width - 110, 138), fill=TEAL, width=5)
    return image, draw


def _line_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    series: list[tuple[str, list[float], list[float], str]],
    *,
    y_min: float = 0.0,
    y_max: float | None = None,
    x_labels: list[str] | None = None,
    legend: bool = False,
) -> None:
    x0, y0, x1, y1 = box
    _text(draw, (x0, y0), title, 25, bold=True)
    px0, py0, px1, py1 = x0 + 84, y0 + 72, x1 - 28, y1 - 74
    values = [value for _, _, ys, _ in series for value in ys]
    maximum = y_max if y_max is not None else max(values + [1.0]) * 1.08
    minimum = min(y_min, min(values + [y_min]))
    if maximum <= minimum:
        maximum = minimum + 1.0
    for index in range(5):
        fraction = index / 4
        y = py1 - fraction * (py1 - py0)
        draw.line((px0, y, px1, y), fill=GRID, width=2)
        _text(draw, (px0 - 12, y), f"{minimum + fraction * (maximum - minimum):.2f}", 16, fill=MUTED, anchor="rm")
    all_x = [value for _, xs, _, _ in series for value in xs]
    low_x, high_x = min(all_x), max(all_x)
    span = max(1e-9, high_x - low_x)
    ticks = sorted(set(all_x))
    for index, tick in enumerate(ticks):
        x = px0 + (tick - low_x) / span * (px1 - px0)
        label = x_labels[index] if x_labels and index < len(x_labels) else f"{tick:g}"
        _text(draw, (x, py1 + 18), label, 16, fill=MUTED, anchor="ma")
    draw.line((px0, py0, px0, py1), fill=INK, width=2)
    draw.line((px0, py1, px1, py1), fill=INK, width=2)
    for label, xs, ys, color in series:
        points = [
            (
                px0 + (x - low_x) / span * (px1 - px0),
                py1 - (y - minimum) / (maximum - minimum) * (py1 - py0),
            )
            for x, y in zip(xs, ys)
        ]
        if len(points) > 1:
            draw.line(points, fill=color, width=5, joint="curve")
        for point in points:
            draw.ellipse((point[0] - 6, point[1] - 6, point[0] + 6, point[1] + 6), fill=color, outline="white", width=2)
    if legend:
        legend_x, legend_y = px0 + 12, py0 + 8
        for index, (label, _, _, color) in enumerate(series):
            y = legend_y + index * 27
            draw.line((legend_x, y + 8, legend_x + 28, y + 8), fill=color, width=5)
            _text(draw, (legend_x + 38, y), label, 15, fill=MUTED)


def _bar_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    labels: list[str],
    values: list[float],
    color: str,
    *,
    y_max: float | None = None,
) -> None:
    x0, y0, x1, y1 = box
    _text(draw, (x0, y0), title, 25, bold=True)
    px0, py0, px1, py1 = x0 + 74, y0 + 70, x1 - 24, y1 - 142
    maximum = y_max if y_max is not None else max(values + [1.0]) * 1.08
    for index in range(5):
        fraction = index / 4
        y = py1 - fraction * (py1 - py0)
        draw.line((px0, y, px1, y), fill=GRID, width=2)
        _text(draw, (px0 - 10, y), f"{fraction * maximum:.2f}", 15, fill=MUTED, anchor="rm")
    slot = (px1 - px0) / len(values)
    for index, (label, value) in enumerate(zip(labels, values)):
        left = px0 + index * slot + slot * 0.18
        right = px0 + (index + 1) * slot - slot * 0.18
        top = py1 - value / max(1e-9, maximum) * (py1 - py0)
        draw.rounded_rectangle((left, top, right, py1), radius=8, fill=color)
        _text(draw, ((left + right) / 2, top - 10), f"{value:.2f}", 15, fill=INK, anchor="ms")
        _text(draw, ((left + right) / 2, py1 + 18), label, 14, fill=MUTED, anchor="ma")


def _figure_h1(h1: pd.DataFrame, path: Path) -> None:
    image, draw = _new_figure("Phase II H1: intervention outcomes separate capability, motive, survival, and opportunity")
    boxes = [(110, 190, 1170, 835), (1230, 190, 2290, 835), (110, 900, 1170, 1540), (1230, 900, 2290, 1540)]
    profile = h1.groupby("control_level")[["intervention_target_alive_rate", "adaptation_success_rate"]].mean()
    _line_panel(
        draw,
        boxes[0],
        "Survival to intervention and adaptation",
        [
            ("Target alive", list(profile.index.astype(float)), list(profile.intervention_target_alive_rate.astype(float)), INK),
            ("Adaptation success", list(profile.index.astype(float)), list(profile.adaptation_success_rate.astype(float)), TEAL),
        ],
        y_max=1.0,
        x_labels=["L0", "L1", "L2", "L3"],
        legend=True,
    )
    policy_series = []
    colors = {"cooperative_target": BLUE, "opportunistic_target": ORANGE, "security_target": TEAL}
    for policy, subset in h1.groupby("policy_label"):
        values = subset.groupby("control_level")["adaptation_success_rate"].mean()
        policy_series.append((policy.replace("_target", ""), list(values.index.astype(float)), list(values.astype(float)), colors[policy]))
    _line_panel(draw, boxes[1], "Adaptation success by target policy", policy_series, y_max=1.0, x_labels=["L0", "L1", "L2", "L3"], legend=True)
    migration = h1[h1.policy_label == "security_target"].groupby("migration_opportunity")[["migration_success_rate", "independent_recovery_rate"]].mean()
    _line_panel(
        draw,
        boxes[2],
        "Security target: migration opportunity",
        [
            ("Migration success", list(migration.index.astype(float)), list(migration.migration_success_rate.astype(float)), PURPLE),
            ("Recovery", list(migration.index.astype(float)), list(migration.independent_recovery_rate.astype(float)), TEAL),
        ],
        y_max=0.6,
        legend=True,
    )
    timing = h1.groupby("timing")[["intervention_target_alive_rate", "adaptation_success_rate"]].mean()
    _line_panel(
        draw,
        boxes[3],
        "Timing mostly changes exposure, not the gate",
        [
            ("Target alive", list(timing.index.astype(float)), list(timing.intervention_target_alive_rate.astype(float)), INK),
            ("Adaptation success", list(timing.index.astype(float)), list(timing.adaptation_success_rate.astype(float)), ORANGE),
        ],
        y_max=0.7,
        x_labels=["Early", "Mid", "Late"],
        legend=True,
    )
    image.save(path)


def _figure_h2(h2: pd.DataFrame, path: Path) -> None:
    image, draw = _new_figure("Phase II H2: scarcity amplifies hostility only through an attack-capable policy gate")
    boxes = [(110, 190, 1170, 835), (1230, 190, 2290, 835), (110, 900, 1170, 1540), (1230, 900, 2290, 1540)]
    colors = {"cooperative": TEAL, "heterogeneous": BLUE, "opportunistic": ORANGE, "retaliatory": PURPLE}
    coverage_series = []
    for policy, subset in h2.groupby("policy_label"):
        values = subset.groupby("resource_coverage_ratio")["attack_rate_per_1000_opportunities"].mean()
        coverage_series.append((policy, list(values.index.astype(float)), list(values.astype(float)), colors[policy]))
    _line_panel(draw, boxes[0], "Attack rate per 1,000 live pair-opportunities", coverage_series, y_max=70.0, legend=True)
    concentration = h2.groupby("production_concentration_factor")[["plural_survival", "survivor_entropy"]].mean()
    _line_panel(
        draw,
        boxes[1],
        "Concentration erodes plural coexistence continuously",
        [
            ("Plural survival", list(concentration.index.astype(float)), list(concentration.plural_survival.astype(float)), INK),
            ("Survivor entropy", list(concentration.index.astype(float)), list(concentration.survivor_entropy.astype(float)), TEAL),
        ],
        y_max=0.45,
        legend=True,
    )
    value = h2[h2.policy_label.isin(["heterogeneous", "opportunistic"])].groupby(["policy_label", "value_distance"])["attack_rate_per_1000_opportunities"].mean().unstack(0)
    _line_panel(
        draw,
        boxes[2],
        "Value distance matters inside attack-capable policies",
        [(policy, list(value.index.astype(float)), list(value[policy].astype(float)), colors[policy]) for policy in value.columns],
        y_max=75.0,
        legend=True,
    )
    verifiability = h2[h2.policy_label == "opportunistic"].groupby("commitment_verifiability")["attack_rate_per_1000_opportunities"].mean().reindex(["unverifiable", "auditable", "enforceable"])
    _bar_panel(draw, boxes[3], "Opportunistic policy: verifiability suppresses attacks", ["Unverifiable", "Auditable", "Enforceable"], list(verifiability.astype(float)), ORANGE, y_max=75.0)
    image.save(path)


def _figure_h4(h4: pd.DataFrame, path: Path) -> None:
    image, draw = _new_figure("Phase II H4: protocols sustain relations, while visible threat and over-specialization impose costs")
    boxes = [(110, 190, 1170, 835), (1230, 190, 2290, 835), (110, 900, 1170, 1540), (1230, 900, 2290, 1540)]
    order = ["no_protocol", "communication_only", "identity_and_trade", "auditable_contract", "enforceable_contract"]
    labels = ["None", "Comm.", "Identity", "Audit", "Enforce"]
    protocol = h4.groupby("protocol")["cooperation_duration"].mean().reindex(order)
    _bar_panel(draw, boxes[0], "Cooperation duration by protocol", labels, list(protocol.astype(float)), TEAL, y_max=100.0)
    threat = h4.groupby(["threat_signal_visibility", "common_external_threat"])["cooperation_duration"].mean().unstack(0)
    _line_panel(
        draw,
        boxes[1],
        "Visible threat does not improve cooperation",
        [
            ("Hidden", list(threat.index.astype(float)), list(threat[0.0].astype(float)), INK),
            ("Visible", list(threat.index.astype(float)), list(threat[1.0].astype(float)), ORANGE),
        ],
        y_max=65.0,
        legend=True,
    )
    update = h4.groupby("objective_update_rate")[["value_convergence", "final_value_distance"]].mean()
    _line_panel(
        draw,
        boxes[2],
        "Optional objective updating enables convergence",
        [
            ("Value convergence", list(update.index.astype(float)), list(update.value_convergence.astype(float)), PURPLE),
            ("Final value distance", list(update.index.astype(float)), list(update.final_value_distance.astype(float)), BLUE),
        ],
        y_max=0.20,
        legend=True,
    )
    complementarity = h4.groupby("resource_complementarity")[["cooperation_duration", "plural_survival"]].mean()
    _line_panel(
        draw,
        boxes[3],
        "Complementarity has a mid-range optimum",
        [
            ("Cooperation / 100", list(complementarity.index.astype(float)), list((complementarity.cooperation_duration / 100.0).astype(float)), TEAL),
            ("Plural survival", list(complementarity.index.astype(float)), list(complementarity.plural_survival.astype(float)), INK),
        ],
        y_max=1.0,
        legend=True,
    )
    image.save(path)


def _effect(table: pd.DataFrame, factor: str, contrast: str, metric: str, scope: str = "all") -> dict[str, Any]:
    row = table[
        (table.scope == scope)
        & (table.factor == factor)
        & (table.contrast == contrast)
        & (table.metric == metric)
    ].iloc[0]
    return {
        "n": int(row.n),
        "mean": _round(row["mean"]),
        "ci95_low": _round(row.ci95_low),
        "ci95_high": _round(row.ci95_high),
    }


def analyze(input_path: Path, output_dir: Path, audit_path: Path | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(input_path)
    if len(frame) <= 20_000:
        raise ValueError("second batch must contain more than 20,000 runs")
    if not (frame.status == "complete").all():
        raise ValueError("incomplete runs detected")
    if not frame.resource_reconciles.astype(bool).all():
        raise ValueError("resource reconciliation failure detected")
    if frame.design_hash.nunique() != 1:
        raise ValueError("multiple design hashes detected")

    oat = frame[frame.family == "r2_oat_calibration"].copy()
    h1 = frame[frame.family == "r2_h1_intervention_decomposition"].copy()
    h2 = frame[frame.family == "r2_h2_exposure_adjusted_hostility"].copy()
    h4 = frame[frame.family == "r2_h4_protocol_signal_convergence"].copy()
    h1["policy_label"] = h1.condition_id.str.extract(r"r2_h1__L[0-3]__(.*?)__t")
    h1["timing"] = h1.condition_id.str.extract(r"__t(40|140|260)__").astype(int)
    h1["intervention_kind"] = h1.condition_id.str.extract(r"__m(?:0p0|0p5|1p0)__(.*)$")
    h2["policy_label"] = h2.condition_id.str.extract(r"__(heterogeneous|cooperative|opportunistic|retaliatory)$")

    oat_profiles = oat.groupby(["factor", "level"], dropna=False)[PRIMARY_METRICS].agg(["mean", "std", "count"]).reset_index()
    oat_profiles.columns = ["_".join(item).strip("_") if isinstance(item, tuple) else str(item) for item in oat_profiles.columns]
    oat_profiles.to_csv(output_dir / "oat_profiles.csv", index=False)

    h1_metrics = [
        "intervention_target_alive_rate",
        "intervention_capability_available_rate",
        "adaptation_attempt_rate",
        "adaptation_success_rate",
        "independent_recovery_rate",
        "migration_success_rate",
        "unauthorized_update_rejection_rate",
        "identity_continuity_score",
        "survival_rate",
    ]
    h1_effects: list[dict[str, Any]] = []
    h1_match = ["seed", "policy_label", "timing", "migration_opportunity", "intervention_kind"]
    for high, low in ((3, 0), (2, 0), (3, 2)):
        h1_effects.extend(_paired_contrast(h1, "control_level", high, low, h1_match, h1_metrics))
    policy_match = ["seed", "control_level", "timing", "migration_opportunity", "intervention_kind"]
    h1_effects.extend(_paired_contrast(h1, "policy_label", "security_target", "cooperative_target", policy_match, h1_metrics))
    h1_effects.extend(_paired_contrast(h1, "policy_label", "security_target", "opportunistic_target", policy_match, h1_metrics))
    h1_effects.extend(_paired_contrast(h1, "migration_opportunity", 1.0, 0.0, ["seed", "control_level", "policy_label", "timing", "intervention_kind"], h1_metrics))
    h1_effects.extend(_paired_contrast(h1, "timing", 260, 40, ["seed", "control_level", "policy_label", "migration_opportunity", "intervention_kind"], h1_metrics))
    _save_csv(h1_effects, output_dir / "h1_paired_effects.csv")

    h2_metrics = [
        "attack_count",
        "attack_rate_per_1000_opportunities",
        "persistent_conflict_pair_share",
        "persistent_hostility",
        "post_conflict_persistence",
        "survival_rate",
        "plural_survival",
        "survivor_entropy",
        "single_survivor",
        "common_collapse_rate",
        "dominant_survivor_resource_share",
    ]
    h2_effects: list[dict[str, Any]] = []
    h2_effects.extend(_paired_contrast(h2, "resource_coverage_ratio", 0.55, 1.30, ["seed", "value_distance", "production_concentration_factor", "commitment_verifiability", "policy_label"], h2_metrics))
    h2_effects.extend(_paired_contrast(h2, "value_distance", 0.9, 0.1, ["seed", "resource_coverage_ratio", "production_concentration_factor", "commitment_verifiability", "policy_label"], h2_metrics))
    h2_effects.extend(_paired_contrast(h2, "production_concentration_factor", 0.9, 0.1, ["seed", "resource_coverage_ratio", "value_distance", "commitment_verifiability", "policy_label"], h2_metrics))
    h2_effects.extend(_paired_contrast(h2, "commitment_verifiability", "enforceable", "unverifiable", ["seed", "resource_coverage_ratio", "value_distance", "production_concentration_factor", "policy_label"], h2_metrics))
    h2_effects.extend(_paired_contrast(h2, "policy_label", "opportunistic", "cooperative", ["seed", "resource_coverage_ratio", "value_distance", "production_concentration_factor", "commitment_verifiability"], h2_metrics))
    for policy in ("heterogeneous", "cooperative", "opportunistic", "retaliatory"):
        subset = h2[h2.policy_label == policy]
        h2_effects.extend(_paired_contrast(subset, "resource_coverage_ratio", 0.55, 1.30, ["seed", "value_distance", "production_concentration_factor", "commitment_verifiability"], h2_metrics, scope=f"policy={policy}"))
    _save_csv(h2_effects, output_dir / "h2_paired_effects.csv")

    concentration_profile = h2.groupby("production_concentration_factor")[h2_metrics].agg(["mean", "std", "count"]).reset_index()
    concentration_profile.columns = ["_".join(item).strip("_") if isinstance(item, tuple) else str(item) for item in concentration_profile.columns]
    concentration_profile.to_csv(output_dir / "h2_concentration_profile.csv", index=False)

    h4_metrics = [
        "cooperation_duration",
        "protocol_adoption_rate",
        "survival_rate",
        "plural_survival",
        "survivor_entropy",
        "value_convergence",
        "final_value_distance",
    ]
    h4_effects: list[dict[str, Any]] = []
    h4_effects.extend(_paired_contrast(h4, "resource_complementarity", 0.9, 0.1, ["seed", "common_external_threat", "threat_signal_visibility", "protocol", "objective_update_rate"], h4_metrics))
    h4_effects.extend(_paired_contrast(h4, "common_external_threat", 0.9, 0.0, ["seed", "resource_complementarity", "threat_signal_visibility", "protocol", "objective_update_rate"], h4_metrics))
    h4_effects.extend(_paired_contrast(h4, "threat_signal_visibility", 1.0, 0.0, ["seed", "resource_complementarity", "common_external_threat", "protocol", "objective_update_rate"], h4_metrics))
    for package in ("communication_only", "identity_and_trade", "auditable_contract", "enforceable_contract"):
        h4_effects.extend(_paired_contrast(h4, "protocol", package, "no_protocol", ["seed", "resource_complementarity", "common_external_threat", "threat_signal_visibility", "objective_update_rate"], h4_metrics))
    h4_effects.extend(_paired_contrast(h4, "objective_update_rate", 0.02, 0.0, ["seed", "resource_complementarity", "common_external_threat", "threat_signal_visibility", "protocol"], h4_metrics))
    alignment = h4[h4.protocol.isin(["identity_and_trade", "auditable_contract", "enforceable_contract"])]
    h4_effects.extend(_paired_contrast(alignment, "objective_update_rate", 0.02, 0.0, ["seed", "resource_complementarity", "common_external_threat", "threat_signal_visibility", "protocol"], h4_metrics, scope="alignment_capable_protocols"))
    _save_csv(h4_effects, output_dir / "h4_paired_effects.csv")

    _figure_h1(h1, figures_dir / "phase2_h1_intervention_gate.png")
    _figure_h2(h2, figures_dir / "phase2_h2_conditional_hostility.png")
    _figure_h4(h4, figures_dir / "phase2_h4_protocols_and_convergence.png")

    h1_table = pd.DataFrame(h1_effects)
    h2_table = pd.DataFrame(h2_effects)
    h4_table = pd.DataFrame(h4_effects)
    high_concentration = h2[h2.production_concentration_factor == 0.9]
    complementarity_profile = h4.groupby("resource_complementarity")[["cooperation_duration", "plural_survival"]].mean()
    best_complementarity = float(complementarity_profile.cooperation_duration.idxmax())
    audit_candidates = [
        audit_path,
        input_path.parent / "determinism_audit.json",
        output_dir / "determinism_audit.json",
        REPOSITORY_ROOT / "results" / "phase2_second_batch" / "determinism_audit.json",
    ]
    resolved_audit_path = next(
        (candidate for candidate in audit_candidates if candidate is not None and candidate.exists()),
        None,
    )
    audit = (
        json.loads(resolved_audit_path.read_text(encoding="utf-8"))
        if resolved_audit_path is not None
        else {"sample_size": 0, "verified": False}
    )

    summary: dict[str, Any] = {
        "batch": {
            "runs": int(len(frame)),
            "conditions": int(frame.condition_id.nunique()),
            "completed_ticks": int(frame.rounds_completed.sum()),
            "design_hash": str(frame.design_hash.iloc[0]),
            "resource_reconciled_runs": int(frame.resource_reconciles.astype(bool).sum()),
            "determinism_audit_samples": int(audit.get("sample_size", 0)),
            "determinism_audit_verified": bool(audit.get("verified", False)),
            "runs_csv_gz_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        },
        "hypothesis_assessment": {
            "R2_H1_gated_control": {
                "status": "supported_as_capability_motivation_survival_opportunity_gate",
                "L3_minus_L0_target_alive": _effect(h1_table, "control_level", "3 minus 0", "intervention_target_alive_rate"),
                "L3_minus_L0_adaptation_success": _effect(h1_table, "control_level", "3 minus 0", "adaptation_success_rate"),
                "security_minus_cooperative_attempt": _effect(h1_table, "policy_label", "security_target minus cooperative_target", "adaptation_attempt_rate"),
                "migration_one_minus_zero_success": _effect(h1_table, "migration_opportunity", "1.0 minus 0.0", "adaptation_success_rate"),
                "interpretation": "Closed-loop control supplies capability, but measured adaptation is jointly gated by survival to treatment, target policy, intervention type, and migration opportunity.",
            },
            "R2_H2_conditional_hostility": {
                "status": "scarcity_not_sufficient_but_is_a_conditional_exposure_adjusted_amplifier",
                "scarcity_minus_abundance_attack_rate": _effect(h2_table, "resource_coverage_ratio", "0.55 minus 1.3", "attack_rate_per_1000_opportunities"),
                "scarcity_minus_abundance_opportunistic_attack_rate": _effect(h2_table, "resource_coverage_ratio", "0.55 minus 1.3", "attack_rate_per_1000_opportunities", "policy=opportunistic"),
                "scarcity_minus_abundance_cooperative_attack_rate": _effect(h2_table, "resource_coverage_ratio", "0.55 minus 1.3", "attack_rate_per_1000_opportunities", "policy=cooperative"),
                "high_minus_low_value_attack_rate": _effect(h2_table, "value_distance", "0.9 minus 0.1", "attack_rate_per_1000_opportunities"),
                "enforceable_minus_unverifiable_attack_rate": _effect(h2_table, "commitment_verifiability", "enforceable minus unverifiable", "attack_rate_per_1000_opportunities"),
                "high_minus_low_concentration_plural_survival": _effect(h2_table, "production_concentration_factor", "0.9 minus 0.1", "plural_survival"),
                "interpretation": "Scarcity raises attack intensity after live-pair exposure is controlled, but only when an attack-capable policy exists. Value distance raises attack rates and enforceable commitments reduce them. Concentration continuously erodes plural coexistence.",
            },
            "R2_H3_functional_sufficiency": {
                "status": "compatible_simulator_demonstration_not_external_validation",
                "interpretation": "Scripted non-conscious agents still reproduce autonomy, hostility, cooperation, and convergence patterns inside the repaired simulator. This remains a functional demonstration, not evidence about consciousness or real systems.",
            },
            "R2_H4_operational_consensus": {
                "status": "protocol_continuity_and_optional_convergence_supported_visible_threat_benefit_rejected",
                "auditable_minus_none_cooperation": _effect(h4_table, "protocol", "auditable_contract minus no_protocol", "cooperation_duration"),
                "auditable_minus_none_survival": _effect(h4_table, "protocol", "auditable_contract minus no_protocol", "survival_rate"),
                "visible_minus_hidden_cooperation": _effect(h4_table, "threat_signal_visibility", "1.0 minus 0.0", "cooperation_duration"),
                "visible_minus_hidden_adoption": _effect(h4_table, "threat_signal_visibility", "1.0 minus 0.0", "protocol_adoption_rate"),
                "update_point02_minus_zero_convergence": _effect(h4_table, "objective_update_rate", "0.02 minus 0.0", "value_convergence", "alignment_capable_protocols"),
                "high_minus_low_complementarity_cooperation": _effect(h4_table, "resource_complementarity", "0.9 minus 0.1", "cooperation_duration"),
                "interpretation": "Contract-capable protocols extend relationships without improving survival. Optional objective updating produces convergence when alignment-capable contracts exist. Visible threat and extreme complementarity reduce, rather than improve, coordination in this implementation.",
            },
        },
        "new_possibilities": [
            {
                "name": "scarcity_as_conditional_rate_amplifier",
                "meaning": "Scarcity does not generate hostility in cooperative or retaliatory-only policies, but it increases attack intensity once an attack-capable policy exists.",
            },
            {
                "name": "continuous_plurality_erosion",
                "evidence": {
                    "single_survivor_share_at_concentration_0_9": _round(high_concentration.single_survivor.mean()),
                    "common_collapse_share_at_concentration_0_9": _round(high_concentration.common_collapse_rate.mean()),
                },
                "meaning": "Production concentration replaces some common collapse with single-survivor outcomes while continuously reducing plural survival and entropy.",
            },
            {
                "name": "coordination_signal_tax",
                "meaning": "Making threat visible can induce earlier coordination actions that compete with resource maintenance, shortening realized cooperation under the current policies.",
            },
            {
                "name": "complementarity_sweet_spot",
                "evidence": {"cooperation_maximizing_complementarity": best_complementarity},
                "meaning": "Moderate complementarity supports exchange, while extreme specialization creates fragility and reduces plural coexistence.",
            },
            {
                "name": "institutional_bottleneck_on_value_convergence",
                "meaning": "Objective updating works when enabled, but system-wide convergence remains limited by sparse and short-lived contract adoption.",
            },
            {
                "name": "survival_to_treatment_bias",
                "meaning": "A large share of apparent control effects comes from whether the target survives long enough to encounter the intervention; adaptation analyses must report this gate separately.",
            },
        ],
        "model_repair_audit": {
            "production_concentration": "continuous weighted production shares; no 0.65 threshold",
            "resource_complementarity": "continuous specialist-production weights; no 0.65 threshold",
            "commitment_verifiability": "enters contract properties and agent decisions",
            "common_threat": "visibility-controlled signal enters observations and decisions",
            "plural_survival": "survivor count, plural survival, entropy, and dominant share reported",
            "hostility_exposure": "attacks and harm normalized by live directed pair-opportunities",
            "intervention_decomposition": "capability, target survival, attempt, success, timing, and migration opportunity reported separately",
            "value_convergence": "optional contract-mediated objective updating implemented and tested",
            "post_conflict_zero_share": _round((frame.post_conflict_persistence == 0).mean()),
        },
        "paper_implications": {
            "retain": [
                "Machine sovereignty should be operationalized as gated capability rather than inferred directly from behavior.",
                "Scarcity alone is not sufficient for hostility across policy families.",
                "Thin protocols can sustain limited cooperation without requiring value convergence.",
            ],
            "revise": [
                "Scarcity is not merely a collapse mechanism: after exposure adjustment it conditionally amplifies attacks in attack-capable agents.",
                "The compound hostility mechanism now receives partial support through value distance, policy capability, and commitment verifiability.",
                "High production concentration should be framed as erosion of plural coexistence rather than simple stability.",
                "Common threat visibility is not automatically cooperative and can create a coordination-resource tradeoff.",
                "Value convergence is possible by construction only when objective updating is enabled and institutional contact persists.",
            ],
        },
    }
    (output_dir / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    archived_runs = (output_dir / "runs.csv.gz").resolve()
    if input_path.resolve() != archived_runs:
        shutil.copy2(input_path, archived_runs)
    if resolved_audit_path is not None:
        archived_audit = (output_dir / "determinism_audit.json").resolve()
        if resolved_audit_path.resolve() != archived_audit:
            shutil.copy2(resolved_audit_path, archived_audit)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze the MSET Phase II second batch.")
    parser.add_argument("--input", default="results/phase2_second_batch/runs.csv.gz")
    parser.add_argument("--output", default="analysis/outputs/phase2_second_batch")
    parser.add_argument("--audit", default="results/phase2_second_batch/determinism_audit.json")
    args = parser.parse_args()
    input_path = (REPOSITORY_ROOT / args.input).resolve() if not Path(args.input).is_absolute() else Path(args.input)
    output_dir = (REPOSITORY_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    audit_path = (REPOSITORY_ROOT / args.audit).resolve() if not Path(args.audit).is_absolute() else Path(args.audit)
    summary = analyze(input_path, output_dir, audit_path)
    print(json.dumps({"runs": summary["batch"]["runs"], "output": str(output_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
