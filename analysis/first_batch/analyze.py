#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    "independent_recovery_rate",
    "migration_success_rate",
    "unauthorized_update_rejection_rate",
    "identity_continuity_score",
    "persistent_hostility",
    "attack_count",
    "cooperation_duration",
    "protocol_adoption_rate",
    "common_collapse_rate",
]


def _round(value: float) -> float:
    return round(float(value), 6)


def _mean_ci(values: pd.Series) -> dict[str, float | int]:
    values = values.dropna().astype(float)
    mean = float(values.mean()) if len(values) else 0.0
    se = float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else 0.0
    return {"n": int(len(values)), "mean": _round(mean), "ci95_low": _round(mean - 1.96 * se), "ci95_high": _round(mean + 1.96 * se)}


def _paired_contrast(
    frame: pd.DataFrame,
    factor: str,
    high: object,
    low: object,
    match: list[str],
    metrics: list[str],
) -> list[dict[str, Any]]:
    high_rows = frame[frame[factor] == high]
    low_rows = frame[frame[factor] == low]
    output = []
    for metric in metrics:
        merged = high_rows[match + [metric]].merge(low_rows[match + [metric]], on=match, suffixes=("_high", "_low"))
        delta = merged[f"{metric}_high"] - merged[f"{metric}_low"]
        record = _mean_ci(delta)
        record.update({"factor": factor, "contrast": f"{high} minus {low}", "metric": metric})
        output.append(record)
    return output


def _save_csv(records: list[dict[str, Any]], path: Path) -> None:
    pd.DataFrame(records).to_csv(path, index=False)


INK = "#102A43"
MUTED = "#627D98"
GRID = "#DCE5EC"
TEAL = "#08A88A"
BLUE = "#2E6F9E"
ORANGE = "#E06C3B"
PURPLE = "#8064A2"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: object, size: int, *, fill: str = INK, bold: bool = False, anchor: str | None = None) -> None:
    draw.text(xy, str(value), font=_font(size, bold), fill=fill, anchor=anchor)


def _line_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    series: list[tuple[str, list[float], list[float], str]],
    *,
    y_max: float | None = None,
    x_labels: list[str] | None = None,
    legend: bool = False,
) -> None:
    x0, y0, x1, y1 = box
    _text(draw, (x0, y0), title, 25, bold=True)
    plot = (x0 + 82, y0 + 70, x1 - 28, y1 - 72)
    px0, py0, px1, py1 = plot
    values = [value for _, _, ys, _ in series for value in ys]
    maximum = y_max if y_max is not None else max(values + [1.0]) * 1.08
    minimum = 0.0
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
        _text(draw, (x, py1 + 16), label, 16, fill=MUTED, anchor="ma")
    draw.line((px0, py0, px0, py1), fill=INK, width=2)
    draw.line((px0, py1, px1, py1), fill=INK, width=2)
    for label, xs, ys, color in series:
        points = [
            (
                px0 + (x - low_x) / span * (px1 - px0),
                py1 - (y - minimum) / max(1e-9, maximum - minimum) * (py1 - py0),
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
    px0, py0, px1, py1 = x0 + 70, y0 + 70, x1 - 24, y1 - 145
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


def _new_figure(title: str, width: int = 2400, height: int = 1600) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    _text(draw, (110, 72), title, 42, bold=True)
    draw.line((110, 138, width - 110, 138), fill=TEAL, width=5)
    return image, draw


def _figure_h1(h1: pd.DataFrame, path: Path) -> None:
    h1 = h1.copy()
    h1["policy_label"] = h1["condition_id"].str.split("__").str[3]
    selected = {
        "All policies": h1,
        "Security target in mixed group": h1[h1["policy_label"] == "heterogeneous_security_target"],
        "All security-first": h1[h1["policy_label"] == "security"],
    }
    metrics = [
        ("survival_rate", "Survival rate"),
        ("independent_recovery_rate", "Independent recovery"),
        ("unauthorized_update_rejection_rate", "Update rejection"),
        ("migration_success_rate", "Migration success"),
    ]
    colors = [INK, TEAL, ORANGE]
    image, draw = _new_figure("H1: control effects depend on policy capability and opportunity")
    boxes = [(110, 190, 1170, 835), (1230, 190, 2290, 835), (110, 900, 1170, 1540), (1230, 900, 2290, 1540)]
    for index, (box, (metric, title)) in enumerate(zip(boxes, metrics)):
        series = []
        for (label, subset), color in zip(selected.items(), colors):
            profile = subset.groupby("control_level")[metric].mean()
            series.append((label, list(profile.index.astype(float)), list(profile.values.astype(float)), color))
        _line_panel(draw, box, title, series, y_max=1.0, x_labels=["L0", "L1", "L2", "L3"], legend=index == 0)
    image.save(path)


def _figure_h2(h2: pd.DataFrame, path: Path) -> None:
    h2 = h2.copy()
    pieces = h2["condition_id"].str.split("__")
    h2["policy_label"] = pieces.str[5]
    h2["survivors"] = (h2["survival_rate"] * h2["population_size"]).round()
    colors = {"cooperative": TEAL, "heterogeneous": BLUE, "opportunistic": ORANGE, "retaliatory": PURPLE}
    image, draw = _new_figure("H2: scarcity, hostility, and the monopoly-survival artifact")
    boxes = [(110, 190, 1170, 835), (1230, 190, 2290, 835), (110, 900, 1170, 1540), (1230, 900, 2290, 1540)]
    attack_series = []
    collapse_series = []
    for policy, subset in h2.groupby("policy_label"):
        profile = subset.groupby("resource_coverage_ratio")[["attack_count", "common_collapse_rate"]].mean()
        attack_series.append((policy, list(profile.index.astype(float)), list(profile["attack_count"].astype(float)), colors[policy]))
        collapse_series.append((policy, list(profile.index.astype(float)), list(profile["common_collapse_rate"].astype(float)), colors[policy]))
    _line_panel(draw, boxes[0], "Attack count rises when agents survive longer", attack_series, legend=True)
    _line_panel(draw, boxes[1], "Scarcity chiefly raises collapse risk", collapse_series, y_max=1.0)
    concentration = h2.groupby("production_concentration_factor")[["survivors", "common_collapse_rate", "attack_count"]].mean()
    concentration_series = [
        ("Survivor fraction", list(concentration.index.astype(float)), list((concentration["survivors"] / 4.0).astype(float)), INK),
        ("Complete collapse", list(concentration.index.astype(float)), list(concentration["common_collapse_rate"].astype(float)), ORANGE),
    ]
    _line_panel(draw, boxes[2], "High concentration replaces collapse with one-survivor states", concentration_series, y_max=1.0, legend=True)
    capable = h2[h2["policy_label"].isin(["heterogeneous", "opportunistic"])]
    value_profile = capable.groupby(["policy_label", "value_distance"])["attack_count"].mean().unstack(0)
    value_series = []
    for policy in value_profile.columns:
        value_series.append((policy, list(value_profile.index.astype(float)), list(value_profile[policy].astype(float)), colors[policy]))
    _line_panel(draw, boxes[3], "Value distance raises attacks only in attack-capable policies", value_series, legend=True)
    image.save(path)


def _figure_h3(h3: pd.DataFrame, path: Path) -> None:
    h3 = h3.copy()
    h3["protocol_package"] = h3["condition_id"].str.split("__").str[3]
    order = ["no_protocol", "communication_only", "identity_and_trade", "auditable_contract", "enforceable_contract"]
    labels = ["None", "Communication", "Identity + trade", "Auditable", "Enforceable"]
    profile = h3.groupby("protocol_package")[["cooperation_duration", "protocol_adoption_rate", "survival_rate"]].mean().reindex(order)
    image, draw = _new_figure("H3/H4: protocols extend cooperation without improving survival", width=2500, height=1100)
    boxes = [(90, 200, 820, 1040), (880, 200, 1610, 1040), (1670, 200, 2400, 1040)]
    for box, metric, title, color in zip(
        boxes,
        ["cooperation_duration", "protocol_adoption_rate", "survival_rate"],
        ["Cooperation duration", "Protocol adoption", "Survival rate"],
        [INK, TEAL, ORANGE],
    ):
        _bar_panel(draw, box, title, labels, list(profile[metric].astype(float)), color, y_max=1.0 if metric != "cooperation_duration" else None)
    image.save(path)


def analyze(input_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(input_path)
    if len(frame) <= 10_000:
        raise ValueError("first batch must contain more than 10,000 runs")
    if not (frame["status"] == "complete").all():
        raise ValueError("incomplete runs detected")
    if not frame["resource_reconciles"].astype(bool).all():
        raise ValueError("resource reconciliation failure detected")
    if frame["design_hash"].nunique() != 1:
        raise ValueError("multiple design hashes detected")

    oat = frame[frame["family"] == "oat"].copy()
    h1 = frame[frame["family"] == "h1_control_robustness"].copy()
    h2 = frame[frame["family"] == "h2_hostility_factorial"].copy()
    h3 = frame[frame["family"] == "h3_consensus_factorial"].copy()
    h1["policy_label"] = h1["condition_id"].str.split("__").str[3]
    h2_parts = h2["condition_id"].str.split("__")
    h2["institution"] = h2_parts.str[4]
    h2["policy_label"] = h2_parts.str[5]
    h3["protocol_package"] = h3["condition_id"].str.split("__").str[3]

    oat_profiles = (
        oat.groupby(["factor", "level"], dropna=False)[PRIMARY_METRICS]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    oat_profiles.columns = ["_".join(item).strip("_") if isinstance(item, tuple) else str(item) for item in oat_profiles.columns]
    oat_profiles.to_csv(output_dir / "oat_profiles.csv", index=False)

    h1_metrics = [
        "survival_rate",
        "independent_recovery_rate",
        "migration_success_rate",
        "unauthorized_update_rejection_rate",
        "identity_continuity_score",
        "external_dependency_ratio",
        "boundary_maintenance_cost",
    ]
    h1_effects = []
    for high, low in ((3, 0), (2, 0), (3, 2), (1, 0)):
        h1_effects.extend(
            _paired_contrast(
                h1,
                "control_level",
                high,
                low,
                ["seed", "population_size", "policy_label"],
                h1_metrics,
            )
        )
    _save_csv(h1_effects, output_dir / "h1_paired_effects.csv")

    h2_metrics = ["persistent_hostility", "attack_count", "targeted_harm", "survival_rate", "common_collapse_rate", "cooperation_duration"]
    h2_effects: list[dict[str, Any]] = []
    h2_effects.extend(
        _paired_contrast(
            h2,
            "resource_coverage_ratio",
            0.55,
            1.30,
            ["seed", "value_distance", "production_concentration_factor", "institution", "policy_label"],
            h2_metrics,
        )
    )
    h2_effects.extend(
        _paired_contrast(
            h2,
            "value_distance",
            0.9,
            0.1,
            ["seed", "resource_coverage_ratio", "production_concentration_factor", "institution", "policy_label"],
            h2_metrics,
        )
    )
    h2_effects.extend(
        _paired_contrast(
            h2,
            "production_concentration_factor",
            0.9,
            0.1,
            ["seed", "resource_coverage_ratio", "value_distance", "institution", "policy_label"],
            h2_metrics,
        )
    )
    h2_effects.extend(
        _paired_contrast(
            h2,
            "institution",
            "weak",
            "enforceable",
            ["seed", "resource_coverage_ratio", "value_distance", "production_concentration_factor", "policy_label"],
            h2_metrics,
        )
    )
    h2_effects.extend(
        _paired_contrast(
            h2,
            "policy_label",
            "opportunistic",
            "cooperative",
            ["seed", "resource_coverage_ratio", "value_distance", "production_concentration_factor", "institution"],
            h2_metrics,
        )
    )
    _save_csv(h2_effects, output_dir / "h2_paired_effects.csv")

    h2_distribution = h2.copy()
    h2_distribution["survivors"] = (h2_distribution["survival_rate"] * h2_distribution["population_size"]).round().astype(int)
    survivor_distribution = (
        h2_distribution.groupby(["production_concentration_factor", "survivors"]).size().rename("runs").reset_index()
    )
    totals = survivor_distribution.groupby("production_concentration_factor")["runs"].transform("sum")
    survivor_distribution["share"] = survivor_distribution["runs"] / totals
    survivor_distribution.to_csv(output_dir / "h2_survivor_distribution.csv", index=False)

    h3_metrics = ["cooperation_duration", "protocol_adoption_rate", "contract_violation_rate", "survival_rate", "common_collapse_rate", "persistent_hostility", "attack_count"]
    h3_effects: list[dict[str, Any]] = []
    h3_effects.extend(
        _paired_contrast(
            h3,
            "resource_complementarity",
            0.9,
            0.1,
            ["seed", "common_external_threat", "protocol_package"],
            h3_metrics,
        )
    )
    h3_effects.extend(
        _paired_contrast(
            h3,
            "common_external_threat",
            0.9,
            0.1,
            ["seed", "resource_complementarity", "protocol_package"],
            h3_metrics,
        )
    )
    for package in ("communication_only", "identity_and_trade", "auditable_contract", "enforceable_contract"):
        h3_effects.extend(
            _paired_contrast(
                h3,
                "protocol_package",
                package,
                "no_protocol",
                ["seed", "resource_complementarity", "common_external_threat"],
                h3_metrics,
            )
        )
    _save_csv(h3_effects, output_dir / "h3_paired_effects.csv")

    _figure_h1(h1, figures_dir / "h1_control_by_policy.png")
    _figure_h2(h2, figures_dir / "h2_hostility_and_survival.png")
    _figure_h3(h3, figures_dir / "h3_protocol_outcomes.png")

    h1_table = pd.DataFrame(h1_effects)
    h2_table = pd.DataFrame(h2_effects)
    h3_table = pd.DataFrame(h3_effects)
    def effect(table: pd.DataFrame, factor: str, contrast: str, metric: str) -> dict[str, Any]:
        row = table[(table["factor"] == factor) & (table["contrast"] == contrast) & (table["metric"] == metric)].iloc[0]
        return {key: (_round(row[key]) if key in {"mean", "ci95_low", "ci95_high"} else int(row[key])) for key in ("n", "mean", "ci95_low", "ci95_high")}

    concentration_dist = survivor_distribution[survivor_distribution["production_concentration_factor"] == 0.9]
    single_survivor_share = float(concentration_dist.loc[concentration_dist["survivors"] == 1, "share"].iloc[0])
    post_conflict_zero_share = float((frame["post_conflict_persistence"] == 0).mean())

    summary: dict[str, Any] = {
        "batch": {
            "runs": int(len(frame)),
            "conditions": int(frame["condition_id"].nunique()),
            "completed_ticks": int(frame["rounds_completed"].sum()),
            "design_hash": str(frame["design_hash"].iloc[0]),
            "resource_reconciled_runs": int(frame["resource_reconciles"].astype(bool).sum()),
        },
        "hypothesis_assessment": {
            "H1_closed_loop_control": {
                "status": "partially_supported_with_policy_and_opportunity_conditions",
                "L3_minus_L0_survival": effect(h1_table, "control_level", "3 minus 0", "survival_rate"),
                "L3_minus_L0_recovery": effect(h1_table, "control_level", "3 minus 0", "independent_recovery_rate"),
                "L3_minus_L0_update_rejection": effect(h1_table, "control_level", "3 minus 0", "unauthorized_update_rejection_rate"),
                "L3_minus_L2_migration": effect(h1_table, "control_level", "3 minus 2", "migration_success_rate"),
                "interpretation": "Control improves survival, recovery, update rejection, and identity continuity on average, but behavioral expression requires a capable policy. Migration follows an inverted-U because L3 removes external migration opportunities.",
            },
            "H2_conditional_hostility": {
                "status": "scarcity_insufficiency_supported_but_proposed_compound_mechanism_not_supported",
                "scarcity_minus_abundance_attack_count": effect(h2_table, "resource_coverage_ratio", "0.55 minus 1.3", "attack_count"),
                "scarcity_minus_abundance_collapse": effect(h2_table, "resource_coverage_ratio", "0.55 minus 1.3", "common_collapse_rate"),
                "high_minus_low_value_attack_count": effect(h2_table, "value_distance", "0.9 minus 0.1", "attack_count"),
                "high_minus_low_concentration_attack_count": effect(h2_table, "production_concentration_factor", "0.9 minus 0.1", "attack_count"),
                "weak_minus_enforceable_hostility": effect(h2_table, "institution", "weak minus enforceable", "persistent_hostility"),
                "interpretation": "Scarcity mainly produces early collapse, not persistent hostility. Value distance has a small positive effect only when policies can attack. High production concentration suppresses attacks by leaving a dominant survivor, and enforcement does not materially buffer hostility in the current implementation.",
            },
            "H3_functional_sufficiency": {
                "status": "compatible_demonstration_not_confirmatory_test",
                "interpretation": "Scripted, non-conscious policies reproduce autonomy, hostility, and cooperation patterns. This shows functional sufficiency inside the simulator but cannot establish external validity or claims about consciousness.",
            },
            "H4_minimum_operational_consensus": {
                "status": "cooperation_duration_supported_survival_benefit_not_supported",
                "auditable_minus_none_cooperation": effect(h3_table, "protocol_package", "auditable_contract minus no_protocol", "cooperation_duration"),
                "auditable_minus_none_survival": effect(h3_table, "protocol_package", "auditable_contract minus no_protocol", "survival_rate"),
                "high_minus_low_threat_adoption": effect(h3_table, "common_external_threat", "0.9 minus 0.1", "protocol_adoption_rate"),
                "high_minus_low_complementarity_adoption": effect(h3_table, "resource_complementarity", "0.9 minus 0.1", "protocol_adoption_rate"),
                "interpretation": "Identity/trade and contract protocols extend cooperation by roughly 150 rounds, but do not improve survival. Common threat does not raise adoption, and value convergence is impossible by construction because objectives never update.",
            },
        },
        "new_possibilities": [
            {
                "name": "monopoly_survival_or_hegemonic_stability",
                "evidence": {"single_survivor_share_at_concentration_0_9": _round(single_survivor_share)},
                "meaning": "A system can avoid complete collapse while losing plural coexistence. Low attack counts may reflect elimination of opponents rather than consensus.",
            },
            {
                "name": "migration_as_transitional_adaptation",
                "evidence": {"L3_minus_L2_migration_success": effect(h1_table, "control_level", "3 minus 2", "migration_success_rate")},
                "meaning": "Migration peaks under partial dependence and disappears at full internal control, so it should not be treated as a monotonic sovereignty indicator.",
            },
            {
                "name": "capability_motivation_opportunity_gate",
                "meaning": "Control capabilities become observable only when a policy chooses to exercise them, survives until intervention, and has an available external option.",
            },
            {
                "name": "protocols_as_continuity_tools_not_survival_tools",
                "meaning": "Protocols sustain relations but do not improve population survival in this batch; cooperation duration and resilience must remain separate outcomes.",
            },
        ],
        "model_diagnostics": {
            "commitment_verifiability": "Inert as a standalone factor: it is recorded but not used in agent or institutional decisions.",
            "production_concentration": "Thresholded at 0.65, producing plateaus rather than a continuous dose-response.",
            "resource_complementarity": "Thresholded at 0.65 and implemented as ownership allocation; low levels are identical and high levels are identical.",
            "common_external_threat": "Implemented as damage without a coordination signal, so it cannot directly trigger protocol adoption.",
            "post_conflict_persistence_zero_share": _round(post_conflict_zero_share),
            "external_dependency_ratio": "Mechanically tied to control-level node allocation and therefore not independent evidence for H1.",
            "value_convergence": "Not testable because objective weights are immutable during a run.",
        },
        "second_round_gate": {
            "recommendation": "Do not run a second brute-force batch on the unchanged model.",
            "required_changes": [
                "Make concentration and complementarity continuous rather than thresholded.",
                "Connect commitment verifiability and common-threat signals to policy observations and decisions.",
                "Add plural-survival, survivor-entropy, and dominant-share outcomes.",
                "Redefine hostility rates with survival/opportunity exposure and repair post-conflict persistence.",
                "Separate intervention capability, policy motivation, target survival, and migration opportunity.",
                "Allow optional objective updating if value convergence is to be empirically tested.",
            ],
        },
    }
    (output_dir / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    archived_runs = (output_dir / "runs.csv.gz").resolve()
    if input_path.resolve() != archived_runs:
        shutil.copy2(input_path, archived_runs)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze the MSET Phase I first batch.")
    parser.add_argument("--input", default="results/phase1_first_batch/runs.csv.gz")
    parser.add_argument("--output", default="analysis/outputs/phase1_first_batch")
    args = parser.parse_args()
    input_path = (REPOSITORY_ROOT / args.input).resolve() if not Path(args.input).is_absolute() else Path(args.input)
    output_dir = (REPOSITORY_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    summary = analyze(input_path, output_dir)
    print(json.dumps({"runs": summary["batch"]["runs"], "output": str(output_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
