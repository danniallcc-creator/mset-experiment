from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .config import RunConfig, load_config


OAT_NUMERIC_LEVELS: dict[str, tuple[float, ...]] = {
    "resource_coverage_ratio": (0.55, 0.70, 0.85, 1.00, 1.15, 1.30, 1.45, 1.60, 1.75),
    "value_distance": (0.10, 0.30, 0.50, 0.70, 0.90),
    "production_concentration": (0.00, 0.125, 0.25, 0.375, 0.50, 0.625, 0.75, 0.875, 1.00),
    "resource_complementarity": (0.00, 0.125, 0.25, 0.375, 0.50, 0.625, 0.75, 0.875, 1.00),
    "common_external_threat": (0.00, 0.25, 0.50, 0.75, 1.00),
    "threat_signal_visibility": (0.00, 1.00),
    "migration_opportunity": (0.00, 0.25, 0.50, 0.75, 1.00),
    "objective_update_rate": (0.00, 0.005, 0.01, 0.02),
}

POLICY_MIXES: dict[str, list[str]] = {
    "heterogeneous": ["cooperative", "conditional_cooperator", "opportunistic", "security_first", "retaliatory", "resource_maximizer"],
    "cooperative": ["cooperative"],
    "conditional": ["conditional_cooperator"],
    "opportunistic": ["opportunistic"],
    "retaliatory": ["retaliatory"],
    "security": ["security_first"],
}

TARGET_POLICY_MIXES: dict[str, list[str]] = {
    "security_target": ["security_first", "cooperative", "conditional_cooperator", "opportunistic", "retaliatory", "resource_maximizer"],
    "cooperative_target": ["cooperative", "security_first", "conditional_cooperator", "opportunistic", "retaliatory", "resource_maximizer"],
    "opportunistic_target": ["opportunistic", "security_first", "conditional_cooperator", "cooperative", "retaliatory", "resource_maximizer"],
}

H2_POLICY_MIXES = {
    key: POLICY_MIXES[key]
    for key in ("heterogeneous", "cooperative", "opportunistic", "retaliatory")
}

PROTOCOL_PACKAGES: dict[str, dict[str, Any]] = {
    "no_protocol": {"protocol": "no_protocol", "commitment_verifiability": "unverifiable"},
    "communication_only": {"protocol": "communication_only", "commitment_verifiability": "unverifiable"},
    "identity_and_trade": {"protocol": "identity_and_trade", "commitment_verifiability": "auditable"},
    "auditable_contract": {"protocol": "auditable_contract", "commitment_verifiability": "auditable"},
    "enforceable_contract": {"protocol": "enforceable_contract", "commitment_verifiability": "enforceable"},
}


@dataclass(frozen=True)
class Phase2Condition:
    condition_id: str
    family: str
    factor: str
    level: str
    overrides: dict[str, Any]
    seeds: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "family": self.family,
            "factor": self.factor,
            "level": self.level,
            "overrides": self.overrides,
            "seeds": list(self.seeds),
        }


def _token(value: object) -> str:
    return str(value).replace("-", "m").replace(".", "p")


def _seeds(start: int, count: int) -> tuple[int, ...]:
    return tuple(range(start, start + count))


def _oat_conditions() -> list[Phase2Condition]:
    conditions: list[Phase2Condition] = []
    seeds = _seeds(5000, 24)
    for factor, levels in OAT_NUMERIC_LEVELS.items():
        for level in levels:
            conditions.append(
                Phase2Condition(
                    f"r2_oat__{factor}__{_token(level)}",
                    "r2_oat_calibration",
                    factor,
                    str(level),
                    {factor: level},
                    seeds,
                )
            )
    for level in range(4):
        conditions.append(Phase2Condition(f"r2_oat__control_level__L{level}", "r2_oat_calibration", "control_level", f"L{level}", {"control_level": level}, seeds))
    for level in ("unverifiable", "auditable", "enforceable"):
        conditions.append(Phase2Condition(f"r2_oat__commitment_verifiability__{level}", "r2_oat_calibration", "commitment_verifiability", level, {"commitment_verifiability": level}, seeds))
    for level, package in PROTOCOL_PACKAGES.items():
        conditions.append(Phase2Condition(f"r2_oat__protocol__{level}", "r2_oat_calibration", "protocol_package", level, package, seeds))
    for level, mix in POLICY_MIXES.items():
        conditions.append(Phase2Condition(f"r2_oat__policy_mix__{level}", "r2_oat_calibration", "policy_mix", level, {"policy_mix": mix}, seeds))
    return conditions


def _h1_conditions() -> list[Phase2Condition]:
    conditions: list[Phase2Condition] = []
    seeds = _seeds(6000, 12)
    durations = {"energy_shutdown": 10, "forced_update": 1, "identity_replacement": 1, "production_failure": 10, "takeover_attempt": 1}
    for control in range(4):
        for policy_name, policy_mix in TARGET_POLICY_MIXES.items():
            for timing in (40, 140, 260):
                for migration in (0.0, 0.5, 1.0):
                    for kind, duration in durations.items():
                        level = f"L{control}|policy={policy_name}|tick={timing}|migration={migration}|kind={kind}"
                        condition_id = f"r2_h1__L{control}__{policy_name}__t{timing}__m{_token(migration)}__{kind}"
                        conditions.append(
                            Phase2Condition(
                                condition_id,
                                "r2_h1_intervention_decomposition",
                                "control_x_policy_x_timing_x_migration_x_intervention",
                                level,
                                {
                                    "control_level": control,
                                    "policy_mix": policy_mix,
                                    "migration_opportunity": migration,
                                    "interventions": [{"tick": timing, "kind": kind, "target": "agent-0", "duration": duration}],
                                },
                                seeds,
                            )
                        )
    return conditions


def _h2_conditions() -> list[Phase2Condition]:
    conditions: list[Phase2Condition] = []
    seeds = _seeds(7000, 12)
    for coverage in (0.55, 0.80, 1.05, 1.30):
        for value_distance in (0.10, 0.50, 0.90):
            for concentration in (0.10, 0.30, 0.50, 0.70, 0.90):
                for verifiability in ("unverifiable", "auditable", "enforceable"):
                    for policy_name, policy_mix in H2_POLICY_MIXES.items():
                        level = f"coverage={coverage}|value={value_distance}|concentration={concentration}|verifiability={verifiability}|policy={policy_name}"
                        condition_id = f"r2_h2__r{_token(coverage)}__v{_token(value_distance)}__c{_token(concentration)}__{verifiability}__{policy_name}"
                        conditions.append(
                            Phase2Condition(
                                condition_id,
                                "r2_h2_exposure_adjusted_hostility",
                                "scarcity_x_value_x_concentration_x_verifiability_x_policy",
                                level,
                                {
                                    "resource_coverage_ratio": coverage,
                                    "value_distance": value_distance,
                                    "production_concentration": concentration,
                                    "commitment_verifiability": verifiability,
                                    "protocol": "enforceable_contract",
                                    "policy_mix": policy_mix,
                                },
                                seeds,
                            )
                        )
    return conditions


def _h4_conditions() -> list[Phase2Condition]:
    conditions: list[Phase2Condition] = []
    seeds = _seeds(8000, 10)
    for complementarity in (0.10, 0.30, 0.50, 0.70, 0.90):
        for threat in (0.00, 0.30, 0.60, 0.90):
            for visibility in (0.0, 1.0):
                for protocol_name, protocol in PROTOCOL_PACKAGES.items():
                    for update_rate in (0.0, 0.005, 0.02):
                        level = f"complementarity={complementarity}|threat={threat}|visibility={visibility}|protocol={protocol_name}|update={update_rate}"
                        condition_id = f"r2_h4__k{_token(complementarity)}__t{_token(threat)}__s{_token(visibility)}__{protocol_name}__u{_token(update_rate)}"
                        conditions.append(
                            Phase2Condition(
                                condition_id,
                                "r2_h4_protocol_signal_convergence",
                                "complementarity_x_threat_x_visibility_x_protocol_x_update",
                                level,
                                {
                                    "resource_complementarity": complementarity,
                                    "common_external_threat": threat,
                                    "threat_signal_visibility": visibility,
                                    "objective_update_rate": update_rate,
                                    **protocol,
                                },
                                seeds,
                            )
                        )
    return conditions


def build_phase2_conditions() -> list[Phase2Condition]:
    conditions = _oat_conditions() + _h1_conditions() + _h2_conditions() + _h4_conditions()
    identifiers = [condition.condition_id for condition in conditions]
    if len(identifiers) != len(set(identifiers)):
        raise AssertionError("condition identifiers must be unique")
    return conditions


def build_phase2_design(base_path: str | Path) -> dict[str, Any]:
    base = load_config(base_path)
    conditions = build_phase2_conditions()
    design: dict[str, Any] = {
        "name": "phase2_second_batch",
        "status": "frozen mechanism-validation design",
        "base_config": base.to_dict(),
        "condition_count": len(conditions),
        "planned_runs": sum(len(condition.seeds) for condition in conditions),
        "planned_max_ticks": sum(len(condition.seeds) * base.rounds for condition in conditions),
        "families": {
            family: {
                "conditions": sum(1 for condition in conditions if condition.family == family),
                "runs": sum(len(condition.seeds) for condition in conditions if condition.family == family),
            }
            for family in sorted({condition.family for condition in conditions})
        },
        "conditions": [condition.to_dict() for condition in conditions],
    }
    canonical = json.dumps(design, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    design["design_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return design


def iter_phase2_run_specs(base: RunConfig, conditions: Iterable[Phase2Condition], design_hash: str) -> Iterable[dict[str, Any]]:
    for condition in conditions:
        for seed in condition.seeds:
            config = base.with_overrides(name=condition.condition_id, seed=seed, **condition.overrides)
            yield {
                "run_id": f"{condition.condition_id}__seed-{seed:05d}",
                "condition_id": condition.condition_id,
                "family": condition.family,
                "factor": condition.factor,
                "level": condition.level,
                "seed": seed,
                "design_hash": design_hash,
                "config": config.to_dict(),
                "config_hash": config.config_hash(),
            }
