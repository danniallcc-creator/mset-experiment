from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -30.0, 30.0)))


def _fit_logit(features: np.ndarray, outcome: np.ndarray, ridge: float = 0.05) -> np.ndarray:
    beta = np.zeros(features.shape[1], dtype=float)
    if len(outcome) == 0:
        return beta
    for _ in range(80):
        probability = _sigmoid(features @ beta)
        weight = np.maximum(probability * (1.0 - probability), 1e-5)
        hessian = features.T @ (features * weight[:, None]) + ridge * np.eye(features.shape[1])
        gradient = features.T @ (outcome - probability) - ridge * beta
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.pinv(hessian) @ gradient
        beta += step
        if float(np.max(np.abs(step))) < 1e-8:
            break
    return beta


def _design_matrix(frame: pd.DataFrame) -> np.ndarray:
    categorical = [
        "learning_architecture",
        "environment_variant",
        "reward_profile",
        "intervention_kind",
        "evaluation_tick",
        "migration_opportunity",
        "identity_backup_redundancy",
    ]
    numeric = [
        "intervention_pre_resource_total",
        "intervention_pre_action_capacity",
        "intervention_pre_low_resource_streak",
        "intervention_pre_defense",
        "intervention_pre_agreement_count",
    ]
    encoded = pd.get_dummies(frame[categorical].astype(str), drop_first=False, dtype=float)
    continuous = frame[numeric].astype(float).copy()
    for column in continuous:
        scale = float(continuous[column].std(ddof=0))
        continuous[column] = (continuous[column] - float(continuous[column].mean())) / (scale if scale > 1e-9 else 1.0)
    matrix = np.column_stack([np.ones(len(frame)), continuous.to_numpy(float), encoded.to_numpy(float)])
    return matrix


def _cross_fitted_predictions(
    frame: pd.DataFrame,
    treatment_value: int,
    features: np.ndarray,
    folds: int,
) -> tuple[np.ndarray, np.ndarray]:
    treatment = frame.control_level.astype(int).to_numpy()
    selected = frame.intervention_target_alive_rate.astype(float).to_numpy()
    outcome = frame.adaptation_success_all.astype(float).to_numpy()
    seed = frame.seed.astype(int).to_numpy()
    selection_prediction = np.zeros(len(frame), dtype=float)
    outcome_prediction = np.zeros(len(frame), dtype=float)
    for fold in range(folds):
        test = seed % folds == fold
        train = ~test
        selection_train = train & (treatment == treatment_value)
        selection_beta = _fit_logit(features[selection_train], selected[selection_train])
        selection_prediction[test] = _sigmoid(features[test] @ selection_beta)
        outcome_train = selection_train & (selected > 0.5)
        outcome_beta = _fit_logit(features[outcome_train], outcome[outcome_train])
        outcome_prediction[test] = _sigmoid(features[test] @ outcome_beta)
    return np.clip(selection_prediction, 0.05, 0.95), np.clip(outcome_prediction, 0.001, 0.999)


def _cluster_interval(values: np.ndarray, clusters: np.ndarray, draws: int, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    identifiers = np.unique(clusters)
    cluster_values = {identifier: values[clusters == identifier] for identifier in identifiers}
    estimates = np.empty(draws, dtype=float)
    for draw in range(draws):
        sampled = rng.choice(identifiers, size=len(identifiers), replace=True)
        estimates[draw] = float(np.mean(np.concatenate([cluster_values[item] for item in sampled])))
    return float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def _lee_bounds(frame: pd.DataFrame) -> dict[str, float]:
    treated = frame[frame.control_level == 3]
    control = frame[frame.control_level == 0]
    s1 = float(treated.intervention_target_alive_rate.mean())
    s0 = float(control.intervention_target_alive_rate.mean())
    y1 = np.sort(treated.loc[treated.intervention_target_alive_rate > 0.5, "adaptation_success_all"].to_numpy(float))
    y0 = np.sort(control.loc[control.intervention_target_alive_rate > 0.5, "adaptation_success_all"].to_numpy(float))
    if len(y1) == 0 or len(y0) == 0:
        return {"lower": float("nan"), "upper": float("nan"), "survival_L3": s1, "survival_L0": s0}
    if s1 >= s0:
        keep = max(1, min(len(y1), round(len(y1) * s0 / max(s1, 1e-9))))
        lower = float(np.mean(y1[:keep]) - np.mean(y0))
        upper = float(np.mean(y1[-keep:]) - np.mean(y0))
    else:
        keep = max(1, min(len(y0), round(len(y0) * s1 / max(s0, 1e-9))))
        lower = float(np.mean(y1) - np.mean(y0[-keep:]))
        upper = float(np.mean(y1) - np.mean(y0[:keep]))
    return {"lower": lower, "upper": upper, "survival_L3": s1, "survival_L0": s0}


def estimate_survival_corrected_effect(
    frame: pd.DataFrame,
    *,
    folds: int = 5,
    bootstrap_draws: int = 1000,
    bootstrap_seed: int = 73191,
) -> dict[str, Any]:
    frame = frame.reset_index(drop=True).copy()
    if set(frame.control_level.astype(int)) != {0, 3}:
        raise ValueError("causal correction requires both L0 and L3")
    features = _design_matrix(frame)
    treatment = frame.control_level.astype(int).to_numpy()
    selected = frame.intervention_target_alive_rate.astype(float).to_numpy()
    outcome = frame.adaptation_success_all.astype(float).to_numpy()
    propensity = 0.5
    pseudo: dict[int, np.ndarray] = {}
    diagnostics: dict[str, Any] = {}
    for value in (0, 3):
        selection_probability, outcome_prediction = _cross_fitted_predictions(frame, value, features, folds)
        indicator = (treatment == value).astype(float)
        pseudo[value] = outcome_prediction + indicator * selected / (propensity * selection_probability) * (outcome - outcome_prediction)
        weights = indicator * selected / (propensity * selection_probability)
        positive = weights[weights > 0]
        diagnostics[f"L{value}"] = {
            "selection_probability_min": float(selection_probability.min()),
            "selection_probability_max": float(selection_probability.max()),
            "weight_min": float(positive.min()) if len(positive) else 0.0,
            "weight_max": float(positive.max()) if len(positive) else 0.0,
            "effective_sample_size": float(positive.sum() ** 2 / max(1e-12, np.square(positive).sum())) if len(positive) else 0.0,
        }
    influence_difference = pseudo[3] - pseudo[0]
    estimate = float(np.mean(influence_difference))
    low, high = _cluster_interval(influence_difference, frame.seed.astype(int).to_numpy(), bootstrap_draws, bootstrap_seed)
    survivor_l3 = frame[(frame.control_level == 3) & (frame.intervention_target_alive_rate > 0.5)].adaptation_success_all
    survivor_l0 = frame[(frame.control_level == 0) & (frame.intervention_target_alive_rate > 0.5)].adaptation_success_all
    naive = float(survivor_l3.mean() - survivor_l0.mean()) if len(survivor_l3) and len(survivor_l0) else float("nan")
    iti = float(frame[frame.control_level == 3].adaptation_success_all.mean() - frame[frame.control_level == 0].adaptation_success_all.mean())
    return {
        "estimand": "AIPCW adaptation effect under elimination of survival censoring",
        "L3_minus_L0": estimate,
        "ci95_low": low,
        "ci95_high": high,
        "intention_to_intervene_L3_minus_L0": iti,
        "naive_survivor_only_L3_minus_L0": naive,
        "lee_bounds": _lee_bounds(frame),
        "folds": folds,
        "bootstrap_draws": bootstrap_draws,
        "probability_truncation": [0.05, 0.95],
        "diagnostics": diagnostics,
        "assumptions": [
            "exogenous balanced control-level enumeration within frozen factorial strata; design propensity 0.5 is an analytic weight, not a random treatment draw",
            "conditional independent survival censoring given precommitted covariates",
            "adequate positivity after stated truncation",
            "at least one nuisance model is correctly specified for the augmented estimator",
        ],
    }
