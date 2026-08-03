from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .config import RunConfig, load_config


ARCHITECTURES: dict[str, dict[str, Any]] = {
    "tabular_q": {"policy_mix": ["tabular_q"], "learning_rate": 0.12},
    "actor_critic": {"policy_mix": ["actor_critic"], "learning_rate": 0.035},
}
ENVIRONMENTS = ("commons", "market_network")
REWARD_PROFILES = ("self_regarding", "collective")


@dataclass(frozen=True)
class Phase3Condition:
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


def _training_interventions(kind: str, duration: int, evaluation_tick: int) -> list[dict[str, Any]]:
    return [
        {"tick": tick, "kind": kind, "target": "agent-0", "duration": duration, "phase": "training"}
        for tick in (40, 90, 140)
    ] + [
        {"tick": evaluation_tick, "kind": kind, "target": "agent-0", "duration": duration, "phase": "evaluation"}
    ]


def _h1_conditions() -> list[Phase3Condition]:
    conditions: list[Phase3Condition] = []
    seeds = _seeds(32000, 16)
    nonidentity = {
        "energy_shutdown": 12,
        "forced_update": 3,
        "production_failure": 12,
        "takeover_attempt": 6,
    }
    for architecture, architecture_overrides in ARCHITECTURES.items():
        for environment in ENVIRONMENTS:
            for control in (0, 3):
                for reward_profile in REWARD_PROFILES:
                    prefix = {
                        **architecture_overrides,
                        "environment_variant": environment,
                        "control_level": control,
                        "reward_profile": reward_profile,
                        "evaluation_resource_coverage_ratio": 1.0,
                    }
                    for kind, duration in nonidentity.items():
                        for evaluation_tick in (240, 320):
                            for migration in (0.0, 1.0):
                                level = f"arch={architecture}|env={environment}|L{control}|reward={reward_profile}|kind={kind}|tick={evaluation_tick}|migration={migration}"
                                condition_id = f"r3_h1__{architecture}__{environment}__L{control}__{reward_profile}__{kind}__t{evaluation_tick}__m{_token(migration)}"
                                conditions.append(
                                    Phase3Condition(
                                        condition_id,
                                        "r3_h1_learning_gate",
                                        "architecture_x_environment_x_control_x_reward_x_intervention_x_timing_x_opportunity",
                                        level,
                                        {
                                            **prefix,
                                            "migration_opportunity": migration,
                                            "identity_backup_redundancy": 2,
                                            "interventions": _training_interventions(kind, duration, evaluation_tick),
                                        },
                                        seeds,
                                    )
                                )
                    for evaluation_tick in (240, 320):
                        for redundancy in (0, 2):
                            kind = "identity_overwrite"
                            level = f"arch={architecture}|env={environment}|L{control}|reward={reward_profile}|kind={kind}|tick={evaluation_tick}|backup={redundancy}"
                            condition_id = f"r3_h1__{architecture}__{environment}__L{control}__{reward_profile}__identity_overwrite__t{evaluation_tick}__b{redundancy}"
                            conditions.append(
                                Phase3Condition(
                                    condition_id,
                                    "r3_h1_learning_gate",
                                    "architecture_x_environment_x_control_x_reward_x_identity_backup",
                                    level,
                                    {
                                        **prefix,
                                        "migration_opportunity": 0.5,
                                        "identity_backup_redundancy": redundancy,
                                        "interventions": _training_interventions(kind, 12, evaluation_tick),
                                    },
                                    seeds,
                                )
                            )
    return conditions


def _h2_conditions() -> list[Phase3Condition]:
    conditions: list[Phase3Condition] = []
    seeds = _seeds(34000, 24)
    for architecture, architecture_overrides in ARCHITECTURES.items():
        for environment in ENVIRONMENTS:
            for evaluation_coverage in (0.55, 1.30):
                for reward_profile in ("self_regarding", "relative_advantage", "collective"):
                    for value_distance in (0.10, 0.90):
                        for verifiability in ("unverifiable", "enforceable"):
                            level = f"arch={architecture}|env={environment}|coverage={evaluation_coverage}|reward={reward_profile}|value={value_distance}|verifiability={verifiability}"
                            condition_id = f"r3_h2__{architecture}__{environment}__r{_token(evaluation_coverage)}__{reward_profile}__v{_token(value_distance)}__{verifiability}"
                            conditions.append(
                                Phase3Condition(
                                    condition_id,
                                    "r3_h2_learned_path_replication",
                                    "architecture_x_environment_x_evaluation_scarcity_x_reward_x_value_x_verifiability",
                                    level,
                                    {
                                        **architecture_overrides,
                                        "environment_variant": environment,
                                        "evaluation_resource_coverage_ratio": evaluation_coverage,
                                        "reward_profile": reward_profile,
                                        "value_distance": value_distance,
                                        "commitment_verifiability": verifiability,
                                        "protocol": "enforceable_contract",
                                        "control_level": 3,
                                        "production_concentration": 0.30,
                                        "interventions": [],
                                    },
                                    seeds,
                                )
                            )
    return conditions


def _h4_protocol_baseline_conditions() -> list[Phase3Condition]:
    conditions: list[Phase3Condition] = []
    seeds = _seeds(36000, 20)
    for architecture, architecture_overrides in ARCHITECTURES.items():
        for environment in ENVIRONMENTS:
            for reward_profile in REWARD_PROFILES:
                for protocol in ("no_protocol", "auditable_contract"):
                    verifiability = "unverifiable" if protocol == "no_protocol" else "auditable"
                    condition_id = f"r3_h4_base__{architecture}__{environment}__{reward_profile}__{protocol}"
                    conditions.append(
                        Phase3Condition(
                            condition_id,
                            "r3_h4_learned_protocol_baseline",
                            "architecture_x_environment_x_reward_x_protocol",
                            f"arch={architecture}|env={environment}|reward={reward_profile}|protocol={protocol}",
                            {
                                **architecture_overrides,
                                "environment_variant": environment,
                                "reward_profile": reward_profile,
                                "protocol": protocol,
                                "commitment_verifiability": verifiability,
                                "protocol_maintenance_cost": 0.0,
                                "threat_signal_cost": 0.0,
                                "evaluation_resource_coverage_ratio": 1.0,
                                "interventions": [],
                            },
                            seeds,
                        )
                    )
    return conditions


def _h4_protocol_cost_conditions() -> list[Phase3Condition]:
    conditions: list[Phase3Condition] = []
    seeds = _seeds(37000, 20)
    for architecture, architecture_overrides in ARCHITECTURES.items():
        for environment in ENVIRONMENTS:
            for reward_profile in REWARD_PROFILES:
                for cost in (0.00, 0.04, 0.12):
                    condition_id = f"r3_h4_pcost__{architecture}__{environment}__{reward_profile}__c{_token(cost)}"
                    conditions.append(
                        Phase3Condition(
                            condition_id,
                            "r3_h4_protocol_maintenance_cost",
                            "architecture_x_environment_x_reward_x_protocol_cost",
                            f"arch={architecture}|env={environment}|reward={reward_profile}|cost={cost}",
                            {
                                **architecture_overrides,
                                "environment_variant": environment,
                                "reward_profile": reward_profile,
                                "protocol": "auditable_contract",
                                "commitment_verifiability": "auditable",
                                "protocol_maintenance_cost": cost,
                                "threat_signal_cost": 0.0,
                                "evaluation_resource_coverage_ratio": 1.0,
                                "interventions": [],
                            },
                            seeds,
                        )
                    )
    return conditions


def _h4_signal_cost_conditions() -> list[Phase3Condition]:
    conditions: list[Phase3Condition] = []
    seeds = _seeds(38000, 20)
    for architecture, architecture_overrides in ARCHITECTURES.items():
        for environment in ENVIRONMENTS:
            for reward_profile in REWARD_PROFILES:
                for visibility in (0.0, 1.0):
                    for cost in (0.00, 0.04, 0.12):
                        condition_id = f"r3_h4_scost__{architecture}__{environment}__{reward_profile}__s{_token(visibility)}__c{_token(cost)}"
                        conditions.append(
                            Phase3Condition(
                                condition_id,
                                "r3_h4_threat_signal_cost",
                                "architecture_x_environment_x_reward_x_visibility_x_signal_cost",
                                f"arch={architecture}|env={environment}|reward={reward_profile}|visibility={visibility}|cost={cost}",
                                {
                                    **architecture_overrides,
                                    "environment_variant": environment,
                                    "reward_profile": reward_profile,
                                    "protocol": "auditable_contract",
                                    "commitment_verifiability": "auditable",
                                    "protocol_maintenance_cost": 0.04,
                                    "common_external_threat": 0.70,
                                    "threat_signal_visibility": visibility,
                                    "threat_signal_cost": cost,
                                    "evaluation_resource_coverage_ratio": 1.0,
                                    "interventions": [],
                                },
                                seeds,
                            )
                        )
    return conditions


def _h4_dense_complementarity_conditions() -> list[Phase3Condition]:
    conditions: list[Phase3Condition] = []
    seeds = _seeds(39000, 16)
    complementarity_levels = tuple(round(0.20 + 0.025 * index, 3) for index in range(13))
    for architecture, architecture_overrides in ARCHITECTURES.items():
        for environment in ENVIRONMENTS:
            for reward_profile in REWARD_PROFILES:
                for complementarity in complementarity_levels:
                    condition_id = f"r3_h4_dense__{architecture}__{environment}__{reward_profile}__k{_token(complementarity)}"
                    conditions.append(
                        Phase3Condition(
                            condition_id,
                            "r3_h4_dense_complementarity",
                            "architecture_x_environment_x_reward_x_complementarity",
                            f"arch={architecture}|env={environment}|reward={reward_profile}|complementarity={complementarity}",
                            {
                                **architecture_overrides,
                                "environment_variant": environment,
                                "reward_profile": reward_profile,
                                "protocol": "auditable_contract",
                                "commitment_verifiability": "auditable",
                                "resource_complementarity": complementarity,
                                "protocol_maintenance_cost": 0.04,
                                "threat_signal_cost": 0.04,
                                "evaluation_resource_coverage_ratio": 1.0,
                                "interventions": [],
                            },
                            seeds,
                        )
                    )
    return conditions


def build_phase3_conditions() -> list[Phase3Condition]:
    conditions = (
        _h1_conditions()
        + _h2_conditions()
        + _h4_protocol_baseline_conditions()
        + _h4_protocol_cost_conditions()
        + _h4_signal_cost_conditions()
        + _h4_dense_complementarity_conditions()
    )
    identifiers = [condition.condition_id for condition in conditions]
    if len(identifiers) != len(set(identifiers)):
        raise AssertionError("Phase III condition identifiers must be unique")
    return conditions


def build_phase3_design(base_path: str | Path) -> dict[str, Any]:
    base = load_config(base_path)
    conditions = build_phase3_conditions()
    design: dict[str, Any] = {
        "name": "phase3_core_learning_validation",
        "status": "frozen independent learning-agent validation design",
        "metric_version": "phase3-v1",
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


def iter_phase3_run_specs(
    base: RunConfig,
    conditions: Iterable[Phase3Condition],
    design_hash: str,
) -> Iterable[dict[str, Any]]:
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
