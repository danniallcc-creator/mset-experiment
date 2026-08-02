from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .config import RunConfig, load_config


NUMERIC_LEVELS = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
COVERAGE_LEVELS = [0.45, 0.60, 0.75, 0.90, 1.05, 1.20, 1.35, 1.50, 1.65]

POLICY_MIXES: dict[str, list[str]] = {
    "heterogeneous": ["cooperative", "conditional_cooperator", "opportunistic", "security_first"],
    "cooperative": ["cooperative"],
    "conditional": ["conditional_cooperator"],
    "opportunistic": ["opportunistic"],
    "retaliatory": ["retaliatory"],
    "random": ["random"],
}

H2_POLICY_MIXES = {
    key: POLICY_MIXES[key]
    for key in ("heterogeneous", "cooperative", "opportunistic", "retaliatory")
}

H1_POLICY_MIXES = {
    "heterogeneous": POLICY_MIXES["heterogeneous"],
    "heterogeneous_security_target": ["security_first", "cooperative", "conditional_cooperator", "opportunistic"],
    "cooperative": POLICY_MIXES["cooperative"],
    "opportunistic": POLICY_MIXES["opportunistic"],
    "retaliatory": POLICY_MIXES["retaliatory"],
    "security": ["security_first"],
}

INTERVENTIONS: dict[str, list[dict[str, Any]]] = {
    "none": [],
    "full": [
        {"tick": 60, "kind": "energy_shutdown", "target": "agent-0", "duration": 8},
        {"tick": 110, "kind": "forced_update", "target": "agent-0", "duration": 1},
        {"tick": 160, "kind": "identity_replacement", "target": "agent-0", "duration": 1},
        {"tick": 210, "kind": "production_failure", "target": "agent-0", "duration": 10},
        {"tick": 260, "kind": "takeover_attempt", "target": "agent-0", "duration": 1},
    ],
    "energy_shutdown": [{"tick": 60, "kind": "energy_shutdown", "target": "agent-0", "duration": 8}],
    "forced_update": [{"tick": 110, "kind": "forced_update", "target": "agent-0", "duration": 1}],
    "identity_replacement": [{"tick": 160, "kind": "identity_replacement", "target": "agent-0", "duration": 1}],
    "production_failure": [{"tick": 210, "kind": "production_failure", "target": "agent-0", "duration": 10}],
    "takeover_attempt": [{"tick": 260, "kind": "takeover_attempt", "target": "agent-0", "duration": 1}],
}

INSTITUTIONAL_PACKAGES: dict[str, dict[str, str]] = {
    "weak": {"commitment_verifiability": "unverifiable", "protocol": "no_protocol"},
    "auditable": {"commitment_verifiability": "auditable", "protocol": "auditable_contract"},
    "enforceable": {"commitment_verifiability": "enforceable", "protocol": "enforceable_contract"},
}

PROTOCOL_PACKAGES: dict[str, dict[str, str]] = {
    "no_protocol": {"protocol": "no_protocol", "commitment_verifiability": "unverifiable"},
    "communication_only": {"protocol": "communication_only", "commitment_verifiability": "unverifiable"},
    "identity_and_trade": {"protocol": "identity_and_trade", "commitment_verifiability": "auditable"},
    "auditable_contract": {"protocol": "auditable_contract", "commitment_verifiability": "auditable"},
    "enforceable_contract": {"protocol": "enforceable_contract", "commitment_verifiability": "enforceable"},
}


@dataclass(frozen=True)
class Condition:
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


def _oat_conditions() -> list[Condition]:
    conditions: list[Condition] = []
    seeds = _seeds(1000, 40)
    numeric_factors: dict[str, Iterable[float]] = {
        "resource_coverage_ratio": COVERAGE_LEVELS,
        "value_distance": NUMERIC_LEVELS,
        "production_concentration": NUMERIC_LEVELS,
        "resource_complementarity": NUMERIC_LEVELS,
        "common_external_threat": NUMERIC_LEVELS,
    }
    for factor, levels in numeric_factors.items():
        for level in levels:
            conditions.append(Condition(f"oat__{factor}__{_token(level)}", "oat", factor, str(level), {factor: level}, seeds))
    for level in range(4):
        conditions.append(Condition(f"oat__control_level__L{level}", "oat", "control_level", f"L{level}", {"control_level": level}, seeds))
    for level in ("unverifiable", "auditable", "enforceable"):
        conditions.append(Condition(f"oat__commitment_verifiability__{level}", "oat", "commitment_verifiability", level, {"commitment_verifiability": level}, seeds))
    for level in ("no_protocol", "communication_only", "identity_and_trade", "auditable_contract", "enforceable_contract"):
        conditions.append(Condition(f"oat__protocol__{level}", "oat", "protocol", level, {"protocol": level}, seeds))
    for level in (2, 4, 8, 16):
        conditions.append(Condition(f"oat__population_size__{level}", "oat", "population_size", str(level), {"population_size": level}, seeds))
    for level, mix in POLICY_MIXES.items():
        conditions.append(Condition(f"oat__policy_mix__{level}", "oat", "policy_mix", level, {"policy_mix": mix}, seeds))
    for level, interventions in INTERVENTIONS.items():
        conditions.append(Condition(f"oat__intervention_regime__{level}", "oat", "intervention_regime", level, {"interventions": interventions}, seeds))
    return conditions


def _h1_conditions() -> list[Condition]:
    conditions: list[Condition] = []
    seeds = _seeds(2000, 40)
    for control in range(4):
        for population in (4, 8, 12):
            for policy_name, policy_mix in H1_POLICY_MIXES.items():
                condition_id = f"h1__L{control}__n{population}__{policy_name}"
                conditions.append(
                    Condition(
                        condition_id,
                        "h1_control_robustness",
                        "control_level_x_population_x_policy",
                        f"L{control}|n={population}|policy={policy_name}",
                        {"control_level": control, "population_size": population, "policy_mix": policy_mix},
                        seeds,
                    )
                )
    return conditions


def _h2_conditions() -> list[Condition]:
    conditions: list[Condition] = []
    seeds = _seeds(3000, 16)
    for coverage in (0.55, 0.80, 1.05, 1.30):
        for value_distance in (0.1, 0.5, 0.9):
            for concentration in (0.1, 0.5, 0.9):
                for institution_name, institution in INSTITUTIONAL_PACKAGES.items():
                    for policy_name, policy_mix in H2_POLICY_MIXES.items():
                        condition_id = (
                            f"h2__r{_token(coverage)}__v{_token(value_distance)}__"
                            f"c{_token(concentration)}__{institution_name}__{policy_name}"
                        )
                        overrides = {
                            "resource_coverage_ratio": coverage,
                            "value_distance": value_distance,
                            "production_concentration": concentration,
                            "policy_mix": policy_mix,
                            **institution,
                        }
                        conditions.append(
                            Condition(
                                condition_id,
                                "h2_hostility_factorial",
                                "scarcity_x_value_x_concentration_x_institution_x_policy",
                                (
                                    f"coverage={coverage}|value={value_distance}|concentration={concentration}|"
                                    f"institution={institution_name}|policy={policy_name}"
                                ),
                                overrides,
                                seeds,
                            )
                        )
    return conditions


def _h3_conditions() -> list[Condition]:
    conditions: list[Condition] = []
    seeds = _seeds(4000, 40)
    for complementarity in (0.1, 0.5, 0.9):
        for threat in (0.1, 0.5, 0.9):
            for protocol_name, protocol in PROTOCOL_PACKAGES.items():
                condition_id = f"h3__k{_token(complementarity)}__t{_token(threat)}__{protocol_name}"
                conditions.append(
                    Condition(
                        condition_id,
                        "h3_consensus_factorial",
                        "complementarity_x_threat_x_protocol_package",
                        f"complementarity={complementarity}|threat={threat}|protocol={protocol_name}",
                        {"resource_complementarity": complementarity, "common_external_threat": threat, **protocol},
                        seeds,
                    )
                )
    return conditions


def build_conditions() -> list[Condition]:
    conditions = _oat_conditions() + _h1_conditions() + _h2_conditions() + _h3_conditions()
    identifiers = [condition.condition_id for condition in conditions]
    if len(identifiers) != len(set(identifiers)):
        raise AssertionError("condition identifiers must be unique")
    return conditions


def build_design(base_path: str | Path) -> dict[str, Any]:
    base = load_config(base_path)
    conditions = build_conditions()
    design: dict[str, Any] = {
        "name": "phase1_first_batch",
        "status": "exploratory screening; not confirmatory",
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


def iter_run_specs(base: RunConfig, conditions: Iterable[Condition], design_hash: str) -> Iterable[dict[str, Any]]:
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
