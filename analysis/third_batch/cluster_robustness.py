#!/usr/bin/env python3
"""Post hoc seed-cluster sensitivity analysis for Phase III.

The repository-precommitted primary factorial contrasts use paired normal-approximation
intervals over condition-by-seed differences.  This script treats the numeric
seed as the resampling cluster and reports a dependence-aware bootstrap
sensitivity analysis.  It is not uniformly more conservative and does not replace the precommitted
estimands or decision rules.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURES = ("tabular_q", "actor_critic")
ENVIRONMENTS = ("commons", "market_network")


def _paired(
    frame: pd.DataFrame,
    factor: str,
    high: object,
    low: object,
    match: list[str],
    metric: str,
) -> pd.DataFrame:
    fields = match + [metric]
    high_frame = frame[frame[factor] == high][fields].rename(columns={metric: "high"})
    low_frame = frame[frame[factor] == low][fields].rename(columns={metric: "low"})
    paired = high_frame.merge(low_frame, on=match, how="inner", validate="one_to_one")
    paired["difference"] = paired.high.astype(float) - paired.low.astype(float)
    return paired


def _cluster_interval(
    paired: pd.DataFrame,
    *,
    draws: int,
    bootstrap_seed: int,
) -> dict[str, float | int]:
    clusters = paired.groupby("seed", as_index=False).difference.mean()
    values = clusters.difference.to_numpy(float)
    if len(values) == 0:
        raise ValueError("cluster interval requires at least one paired seed")
    rng = np.random.default_rng(bootstrap_seed)
    bootstrap = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return {
        "pairs": int(len(paired)),
        "seed_clusters": int(len(values)),
        "mean": float(paired.difference.mean()),
        "cluster_bootstrap_ci95_low": float(np.quantile(bootstrap, 0.025)),
        "cluster_bootstrap_ci95_high": float(np.quantile(bootstrap, 0.975)),
    }


def _record(
    rows: list[dict[str, object]],
    *,
    family: str,
    contrast: str,
    metric: str,
    scope: str,
    paired: pd.DataFrame,
    draws: int,
    bootstrap_seed: int,
) -> None:
    rows.append(
        {
            "family": family,
            "contrast": contrast,
            "metric": metric,
            "scope": scope,
            "status": "post_hoc_seed_cluster_sensitivity",
            "bootstrap_draws": draws,
            **_cluster_interval(paired, draws=draws, bootstrap_seed=bootstrap_seed),
        }
    )


def _signal_cost_did_pairs(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    match = ["seed", "learning_architecture", "environment_variant", "reward_profile"]
    pivot = frame.pivot_table(
        index=match,
        columns=["threat_signal_visibility", "threat_signal_cost"],
        values=metric,
        aggfunc="first",
    )
    difference = (
        (pivot[(1.0, 0.12)] - pivot[(1.0, 0.0)])
        - (pivot[(0.0, 0.12)] - pivot[(0.0, 0.0)])
    )
    return difference.rename("difference").reset_index()


def analyze(frame: pd.DataFrame, *, draws: int, bootstrap_seed: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    h1 = frame[frame.family == "r3_h1_learning_gate"].copy()
    parts = h1.condition_id.str.split("__")
    h1["intervention_kind"] = parts.str[5]
    h1["evaluation_tick"] = parts.str[6].str.removeprefix("t").astype(int)
    h1["intervention_detail"] = parts.str[7]
    h1_match = [
        "seed",
        "learning_architecture",
        "environment_variant",
        "reward_profile",
        "intervention_kind",
        "evaluation_tick",
        "intervention_detail",
    ]
    h1_scopes = [("all", h1)] + [
        (
            f"{architecture}|{environment}",
            h1[
                (h1.learning_architecture == architecture)
                & (h1.environment_variant == environment)
            ],
        )
        for architecture in ARCHITECTURES
        for environment in ENVIRONMENTS
    ]
    for scope, subset in h1_scopes:
        _record(
            rows,
            family="P3-H1",
            contrast="L3 minus L0",
            metric="adaptation_success_all",
            scope=scope,
            paired=_paired(subset, "control_level", 3, 0, h1_match, "adaptation_success_all"),
            draws=draws,
            bootstrap_seed=bootstrap_seed + len(rows),
        )

    identity = h1[h1.intervention_kind == "identity_overwrite"].copy()
    identity_match = [
        "seed",
        "learning_architecture",
        "environment_variant",
        "reward_profile",
        "control_level",
        "evaluation_tick",
    ]
    _record(
        rows,
        family="P3-H1-identity",
        contrast="two backups minus none",
        metric="identity_restore_success_rate",
        scope="all",
        paired=_paired(
            identity,
            "identity_backup_redundancy",
            2,
            0,
            identity_match,
            "identity_restore_success_rate",
        ),
        draws=draws,
        bootstrap_seed=bootstrap_seed + len(rows),
    )

    h2 = frame[frame.family == "r3_h2_learned_path_replication"].copy()
    h2_match = [
        "seed",
        "learning_architecture",
        "environment_variant",
        "reward_profile",
        "value_distance",
        "commitment_verifiability",
    ]
    h2_scopes = [("all", h2)] + [
        (
            f"{architecture}|{environment}",
            h2[
                (h2.learning_architecture == architecture)
                & (h2.environment_variant == environment)
            ],
        )
        for architecture in ARCHITECTURES
        for environment in ENVIRONMENTS
    ] + [
        (
            f"environment={environment}",
            h2[h2.environment_variant == environment],
        )
        for environment in ENVIRONMENTS
    ]
    for scope, subset in h2_scopes:
        _record(
            rows,
            family="P3-H2",
            contrast="coverage 0.55 minus 1.30",
            metric="evaluation_attack_rate_per_1000_opportunities",
            scope=scope,
            paired=_paired(
                subset,
                "evaluation_resource_coverage_ratio",
                0.55,
                1.30,
                h2_match,
                "evaluation_attack_rate_per_1000_opportunities",
            ),
            draws=draws,
            bootstrap_seed=bootstrap_seed + len(rows),
        )

    gate_pairs = _paired(
        h2,
        "evaluation_resource_coverage_ratio",
        0.55,
        1.30,
        h2_match,
        "evaluation_attack_rate_per_1000_opportunities",
    )
    gate_fields = h2_match + ["pre_evaluation_attack_gate_share"]
    scarce_gate = h2[h2.evaluation_resource_coverage_ratio == 0.55][gate_fields].rename(
        columns={"pre_evaluation_attack_gate_share": "scarce_gate"}
    )
    abundant_gate = h2[h2.evaluation_resource_coverage_ratio == 1.30][gate_fields].rename(
        columns={"pre_evaluation_attack_gate_share": "abundant_gate"}
    )
    gates = scarce_gate.merge(abundant_gate, on=h2_match, validate="one_to_one")
    gates["gate_open"] = 0.5 * (gates.scarce_gate + gates.abundant_gate) > 0
    gate_pairs = gate_pairs.merge(gates[h2_match + ["gate_open"]], on=h2_match, validate="one_to_one")
    _record(
        rows,
        family="P3-H2",
        contrast="coverage 0.55 minus 1.30 after frozen attack gate",
        metric="evaluation_attack_rate_per_1000_opportunities",
        scope="gate_open",
        paired=gate_pairs[gate_pairs.gate_open],
        draws=draws,
        bootstrap_seed=bootstrap_seed + len(rows),
    )

    h4_base = frame[frame.family == "r3_h4_learned_protocol_baseline"].copy()
    h4_cost = frame[frame.family == "r3_h4_protocol_maintenance_cost"].copy()
    h4_signal = frame[frame.family == "r3_h4_threat_signal_cost"].copy()
    h4_match = ["seed", "learning_architecture", "environment_variant", "reward_profile"]
    _record(
        rows,
        family="P3-H4",
        contrast="auditable contract minus no protocol at zero maintenance cost",
        metric="evaluation_cooperation_rate",
        scope="all",
        paired=_paired(
            h4_base,
            "protocol",
            "auditable_contract",
            "no_protocol",
            h4_match,
            "evaluation_cooperation_rate",
        ),
        draws=draws,
        bootstrap_seed=bootstrap_seed + len(rows),
    )
    h4_scopes = [("all", h4_cost)] + [
        (
            f"{architecture}|{environment}",
            h4_cost[
                (h4_cost.learning_architecture == architecture)
                & (h4_cost.environment_variant == environment)
            ],
        )
        for architecture in ARCHITECTURES
        for environment in ENVIRONMENTS
    ]
    for scope, subset in h4_scopes:
        _record(
            rows,
            family="P3-H4",
            contrast="maintenance cost 0.12 minus 0.00",
            metric="evaluation_cooperation_rate",
            scope=scope,
            paired=_paired(
                subset,
                "protocol_maintenance_cost",
                0.12,
                0.0,
                h4_match,
                "evaluation_cooperation_rate",
            ),
            draws=draws,
            bootstrap_seed=bootstrap_seed + len(rows),
        )
    signal_scopes = [("all", h4_signal)] + [
        (
            f"{architecture}|{environment}",
            h4_signal[
                (h4_signal.learning_architecture == architecture)
                & (h4_signal.environment_variant == environment)
            ],
        )
        for architecture in ARCHITECTURES
        for environment in ENVIRONMENTS
    ]
    for scope, subset in signal_scopes:
        _record(
            rows,
            family="P3-H4",
            contrast="visible-minus-hidden high-minus-zero threat-signal-cost DID",
            metric="evaluation_cooperation_rate",
            scope=scope,
            paired=_signal_cost_did_pairs(subset, "evaluation_cooperation_rate"),
            draws=draws,
            bootstrap_seed=bootstrap_seed + len(rows),
        )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="analysis/outputs/phase3_core_validation/runs.csv.gz",
    )
    parser.add_argument(
        "--output",
        default="analysis/outputs/phase3_core_validation/cluster_robustness.csv",
    )
    parser.add_argument("--draws", type=int, default=20_000)
    parser.add_argument("--bootstrap-seed", type=int, default=81_226)
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    result = analyze(
        pd.read_csv(input_path),
        draws=args.draws,
        bootstrap_seed=args.bootstrap_seed,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize derived floating-point values at a precision that is stable
    # across supported CPU/libm combinations. The archived estimates are
    # reported to four decimals; 12 significant digits preserves ample audit
    # precision while avoiding meaningless ~1e-15 text diffs in CI.
    result.to_csv(
        output_path,
        index=False,
        float_format=lambda value: format(value, ".12g"),
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
