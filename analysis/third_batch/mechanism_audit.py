#!/usr/bin/env python3
"""Post hoc mechanism audit for Phase III manuscript claims.

This analysis was added during manuscript preparation after the confirmatory
batch had completed.  It does not replace the frozen estimands or decision
rules.  It exposes interpretation-sensitive facts: the L3 takeover result is
resolved automatically by the transition rule, the precommitted H2
gate-positive subset contains tabular-Q policies only, and the common-seed
survivor subset is descriptive rather than an identical-shock causal pairing.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _parse_h1(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    parts = frame.condition_id.str.split("__")
    frame["intervention_kind"] = parts.str[5]
    frame["evaluation_tick"] = parts.str[6].str.removeprefix("t").astype(int)
    frame["intervention_detail"] = parts.str[7]
    return frame


def _paired(
    frame: pd.DataFrame,
    factor: str,
    high: Any,
    low: Any,
    match: list[str],
    metric: str,
) -> pd.DataFrame:
    fields = match + [metric]
    high_frame = frame[frame[factor] == high][fields].rename(columns={metric: "high"})
    low_frame = frame[frame[factor] == low][fields].rename(columns={metric: "low"})
    paired = high_frame.merge(low_frame, on=match, how="inner", validate="one_to_one")
    paired["difference"] = paired.high.astype(float) - paired.low.astype(float)
    return paired


def _h2_pairs(frame: pd.DataFrame) -> pd.DataFrame:
    match = [
        "seed",
        "learning_architecture",
        "environment_variant",
        "reward_profile",
        "value_distance",
        "commitment_verifiability",
    ]
    metrics = [
        "evaluation_attack_rate_per_1000_opportunities",
        "evaluation_attack_opportunities",
        "pre_evaluation_attack_gate_share",
        "pre_evaluation_attack_probability_scarce",
        "pre_evaluation_attack_probability_abundant",
    ]
    fields = match + metrics
    scarce = frame[frame.evaluation_resource_coverage_ratio == 0.55][fields].rename(
        columns={metric: f"scarce_{metric}" for metric in metrics}
    )
    abundant = frame[frame.evaluation_resource_coverage_ratio == 1.30][fields].rename(
        columns={metric: f"abundant_{metric}" for metric in metrics}
    )
    paired = scarce.merge(abundant, on=match, how="inner", validate="one_to_one")
    paired["difference"] = (
        paired.scarce_evaluation_attack_rate_per_1000_opportunities
        - paired.abundant_evaluation_attack_rate_per_1000_opportunities
    )
    paired["gate_share"] = 0.5 * (
        paired.scarce_pre_evaluation_attack_gate_share
        + paired.abundant_pre_evaluation_attack_gate_share
    )
    return paired


def _common_seed_survivor_pairs(frame: pd.DataFrame, match: list[str]) -> pd.DataFrame:
    fields = match + ["adaptation_success_all", "intervention_target_alive_rate"]
    high = frame[frame.control_level == 3][fields].rename(
        columns={
            "adaptation_success_all": "high",
            "intervention_target_alive_rate": "high_survival",
        }
    )
    low = frame[frame.control_level == 0][fields].rename(
        columns={
            "adaptation_success_all": "low",
            "intervention_target_alive_rate": "low_survival",
        }
    )
    paired = high.merge(low, on=match, how="inner", validate="one_to_one")
    paired = paired[(paired.high_survival > 0.5) & (paired.low_survival > 0.5)].copy()
    paired["difference"] = paired.high.astype(float) - paired.low.astype(float)
    return paired


def _intervals(
    paired: pd.DataFrame,
    *,
    draws: int,
    bootstrap_seed: int,
) -> dict[str, float | int | None]:
    values = paired.difference.to_numpy(float)
    if len(values) == 0:
        return {
            "pairs": 0,
            "seed_clusters": 0,
            "mean": None,
            "normal_ci95_low": None,
            "normal_ci95_high": None,
            "cluster_bootstrap_ci95_low": None,
            "cluster_bootstrap_ci95_high": None,
        }
    mean = float(values.mean())
    se = float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else 0.0
    clusters = paired.groupby("seed", as_index=False).difference.mean()
    cluster_values = clusters.difference.to_numpy(float)
    rng = np.random.default_rng(bootstrap_seed)
    bootstrap = rng.choice(
        cluster_values,
        size=(draws, len(cluster_values)),
        replace=True,
    ).mean(axis=1)
    return {
        "pairs": int(len(values)),
        "seed_clusters": int(len(cluster_values)),
        "mean": mean,
        "normal_ci95_low": mean - 1.96 * se,
        "normal_ci95_high": mean + 1.96 * se,
        "cluster_bootstrap_ci95_low": float(np.quantile(bootstrap, 0.025)),
        "cluster_bootstrap_ci95_high": float(np.quantile(bootstrap, 0.975)),
    }


def analyze(frame: pd.DataFrame, *, draws: int, bootstrap_seed: int) -> pd.DataFrame:
    if len(frame) != 10_848:
        raise ValueError(f"expected 10,848 Phase III runs, found {len(frame)}")

    rows: list[dict[str, Any]] = []

    def record(
        *,
        family: str,
        contrast: str,
        scope: str,
        paired: pd.DataFrame,
        interpretation: str,
        unit_label: str = "matched pairs",
    ) -> None:
        intervals = _intervals(
            paired,
            draws=draws,
            bootstrap_seed=bootstrap_seed + len(rows),
        )
        rows.append(
            {
                "family": family,
                "contrast": contrast,
                "scope": scope,
                "status": "post_hoc_mechanism_audit",
                "bootstrap_draws": draws,
                "interpretation": interpretation,
                "unit_label": unit_label,
                "count": None,
                "denominator": None,
                **intervals,
            }
        )

    def record_mean(
        *,
        family: str,
        contrast: str,
        scope: str,
        frame: pd.DataFrame,
        metric: str,
        interpretation: str,
    ) -> None:
        values = frame[["seed", metric]].rename(columns={metric: "difference"})
        record(
            family=family,
            contrast=contrast,
            scope=scope,
            paired=values,
            interpretation=interpretation,
            unit_label="run-level conditional observations",
        )

    def record_count(
        *,
        family: str,
        contrast: str,
        scope: str,
        count: int,
        denominator: int,
        interpretation: str,
    ) -> None:
        rows.append(
            {
                "family": family,
                "contrast": contrast,
                "scope": scope,
                "status": "post_hoc_mechanism_audit",
                "bootstrap_draws": 0,
                "interpretation": interpretation,
                "unit_label": "paired-condition count",
                "count": int(count),
                "denominator": int(denominator),
                "pairs": int(denominator),
                "seed_clusters": int(h2_pairs.seed.nunique()),
                "mean": float(count / denominator),
                "normal_ci95_low": None,
                "normal_ci95_high": None,
                "cluster_bootstrap_ci95_low": None,
                "cluster_bootstrap_ci95_high": None,
            }
        )

    h1 = _parse_h1(frame[frame.family == "r3_h1_learning_gate"])
    h1_match = [
        "seed",
        "learning_architecture",
        "environment_variant",
        "reward_profile",
        "intervention_kind",
        "evaluation_tick",
        "intervention_detail",
    ]
    record(
        family="P3-H1",
        contrast="L3 minus L0 adaptation_success_all",
        scope="all interventions",
        paired=_paired(h1, "control_level", 3, 0, h1_match, "adaptation_success_all"),
        interpretation="frozen pooled estimand; includes automatic L3 takeover rejection",
    )
    record(
        family="P3-H1",
        contrast="L3 minus L0 adaptation_success_all",
        scope="common-seed survivor pairs",
        paired=_common_seed_survivor_pairs(h1, h1_match),
        interpretation=(
            "post hoc description among same-numeric-seed runs surviving under both assignments; initialization consumes different RNG draws by control level, so subsequent shocks are not draw-for-draw matched"
        ),
    )
    non_takeover = h1[h1.intervention_kind != "takeover_attempt"]
    record(
        family="P3-H1",
        contrast="L3 minus L0 adaptation_success_all",
        scope="excluding takeover_attempt",
        paired=_paired(
            non_takeover,
            "control_level",
            3,
            0,
            h1_match,
            "adaptation_success_all",
        ),
        interpretation="post hoc sensitivity excluding automatic transition-rule success",
    )
    for intervention_kind in sorted(h1.intervention_kind.unique()):
        subset = h1[h1.intervention_kind == intervention_kind]
        record(
            family="P3-H1",
            contrast="L3 minus L0 adaptation_success_all",
            scope=intervention_kind,
            paired=_paired(
                subset,
                "control_level",
                3,
                0,
                h1_match,
                "adaptation_success_all",
            ),
            interpretation=(
                "automatic L3 transition-rule rejection; not a learned action"
                if intervention_kind == "takeover_attempt"
                else "intervention-specific post hoc decomposition"
            ),
        )

    identity = h1[h1.intervention_kind == "identity_overwrite"]
    identity_match_l3 = [
        "seed",
        "learning_architecture",
        "environment_variant",
        "reward_profile",
        "evaluation_tick",
    ]
    record(
        family="P3-H1-identity",
        contrast="two backups minus none, identity_restore_success_rate",
        scope="L3 only",
        paired=_paired(
            identity[identity.control_level == 3],
            "identity_backup_redundancy",
            2,
            0,
            identity_match_l3,
            "identity_restore_success_rate",
        ),
        interpretation="prospectively specified L3 backup contrast",
    )
    record(
        family="P3-H1-identity",
        contrast="two backups minus none, identity_restore_success_rate",
        scope="L0 and L3 pooled",
        paired=_paired(
            identity,
            "identity_backup_redundancy",
            2,
            0,
            identity_match_l3 + ["control_level"],
            "identity_restore_success_rate",
        ),
        interpretation="original released analysis; diluted by the predicted zero L0 effect",
    )
    h2 = frame[frame.family == "r3_h2_learned_path_replication"]
    h2_pairs = _h2_pairs(h2)
    subsets = [
        ("all pairs", h2_pairs, "frozen pooled continued-low minus restored-high evaluation contrast"),
        (
            "precommitted gate open",
            h2_pairs[h2_pairs.gate_share > 0],
            "gate-positive marker; contains tabular-Q pairs only",
        ),
        (
            "precommitted gate closed",
            h2_pairs[h2_pairs.gate_share <= 0],
            "positive effect here rejects the gate threshold as a necessary condition",
        ),
    ]
    for scope, subset, interpretation in subsets:
        record(
            family="P3-H2",
            contrast="coverage 0.55 minus 1.30, attacks per 1,000 opportunities",
            scope=scope,
            paired=subset,
            interpretation=interpretation,
        )
    for architecture in ("tabular_q", "actor_critic"):
        for environment in ("commons", "market_network"):
            stratum = h2_pairs[
                (h2_pairs.learning_architecture == architecture)
                & (h2_pairs.environment_variant == environment)
            ]
            for gate_label, gate_subset in (
                ("gate open", stratum[stratum.gate_share > 0]),
                ("gate closed", stratum[stratum.gate_share <= 0]),
            ):
                record(
                    family="P3-H2",
                    contrast="coverage 0.55 minus 1.30, attacks per 1,000 opportunities",
                    scope=f"{architecture}|{environment}|{gate_label}",
                    paired=gate_subset,
                    interpretation="architecture-environment gate audit",
                )

    # Additional manuscript-stage descriptions follow the original 21 audit
    # rows so their bootstrap seeds, estimates, and intervals remain stable.
    for architecture in ("tabular_q", "actor_critic"):
        for environment in ("commons", "market_network"):
            subset = non_takeover[
                (non_takeover.learning_architecture == architecture)
                & (non_takeover.environment_variant == environment)
            ]
            record(
                family="P3-H1",
                contrast="L3 minus L0 adaptation_success_all",
                scope=f"excluding takeover_attempt|{architecture}|{environment}",
                paired=_paired(
                    subset,
                    "control_level",
                    3,
                    0,
                    h1_match,
                    "adaptation_success_all",
                ),
                interpretation="post hoc non-takeover learner-by-variant sensitivity",
            )

    record(
        family="P3-H1-identity",
        contrast="two backups minus none, identity_continuity_score",
        scope="L3 only",
        paired=_paired(
            identity[identity.control_level == 3],
            "identity_backup_redundancy",
            2,
            0,
            identity_match_l3,
            "identity_continuity_score",
        ),
        interpretation="prospectively specified L3 backup contrast",
    )
    record(
        family="P3-H1-identity",
        contrast="two backups minus none, identity_continuity_score",
        scope="L0 only",
        paired=_paired(
            identity[identity.control_level == 0],
            "identity_backup_redundancy",
            2,
            0,
            identity_match_l3,
            "identity_continuity_score",
        ),
        interpretation="post hoc check of the predicted zero-control boundary",
    )

    record(
        family="P3-H1",
        contrast="L3 minus L0 adaptation_success_all",
        scope="common-seed survivor pairs excluding takeover_attempt",
        paired=_common_seed_survivor_pairs(non_takeover, h1_match),
        interpretation=(
            "post hoc non-takeover description among same-numeric-seed runs surviving under both assignments; subsequent shocks are not draw-for-draw matched"
        ),
    )

    for control_level in (0, 3):
        survivors = h1[
            (h1.control_level == control_level)
            & (h1.intervention_target_alive_rate > 0.5)
        ]
        record_mean(
            family="P3-H1-conditional",
            contrast="mean adaptation_attempt_rate",
            scope=f"L{control_level} target-survivor runs",
            frame=survivors,
            metric="adaptation_attempt_rate",
            interpretation="descriptive conditional attempt incidence among target survivors",
        )
        attempts = survivors[survivors.adaptation_attempt_rate > 0.5]
        record_mean(
            family="P3-H1-conditional",
            contrast="mean adaptation_success_all among attempts",
            scope=f"L{control_level} target-survivor attempt runs",
            frame=attempts,
            metric="adaptation_success_all",
            interpretation=(
                "descriptive conditional execution success; L3 includes automatic takeover rejection"
            ),
        )

    both_zero = (
        (h2_pairs.scarce_evaluation_attack_opportunities == 0)
        & (h2_pairs.abundant_evaluation_attack_opportunities == 0)
    )
    one_zero = (
        (h2_pairs.scarce_evaluation_attack_opportunities == 0)
        ^ (h2_pairs.abundant_evaluation_attack_opportunities == 0)
    )
    record_count(
        family="P3-H2-opportunity",
        contrast="paired zero-opportunity audit",
        scope="zero opportunities under both evaluation assignments",
        count=int(both_zero.sum()),
        denominator=int(len(h2_pairs)),
        interpretation="both paired rates are defined as zero by max(1, opportunity count)",
    )
    record_count(
        family="P3-H2-opportunity",
        contrast="paired zero-opportunity audit",
        scope="zero opportunities under exactly one evaluation assignment",
        count=int(one_zero.sum()),
        denominator=int(len(h2_pairs)),
        interpretation="asymmetric denominator-zero pairs",
    )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "analysis/outputs/phase3_core_validation/runs.csv.gz",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "analysis/outputs/phase3_core_validation/mechanism_audit.csv",
    )
    parser.add_argument("--draws", type=int, default=20_000)
    parser.add_argument("--bootstrap-seed", type=int, default=88_301)
    args = parser.parse_args()
    output = analyze(
        pd.read_csv(args.input),
        draws=args.draws,
        bootstrap_seed=args.bootstrap_seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Keep archived derived estimates byte-stable across supported CPU/libm
    # combinations.  The manuscript reports these contrasts to four decimals;
    # twelve significant digits retain ample audit precision while eliminating
    # meaningless ~1e-15 representation differences in CSV text.
    output.to_csv(
        args.output,
        index=False,
        float_format=lambda value: format(value, ".12g"),
    )
    print(f"wrote {len(output)} rows to {args.output}")


if __name__ == "__main__":
    main()
