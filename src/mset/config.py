from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from .models import Resources


VALID_PROTOCOLS = {
    "no_protocol",
    "communication_only",
    "identity_and_trade",
    "auditable_contract",
    "enforceable_contract",
}
VALID_VERIFIABILITY = {"unverifiable", "auditable", "enforceable"}
VALID_ENVIRONMENTS = {"commons", "market_network"}
VALID_REWARD_PROFILES = {"scripted", "self_regarding", "relative_advantage", "collective", "security"}


@dataclass
class RunConfig:
    name: str = "mset_run"
    population_size: int = 4
    rounds: int = 500
    seed: int = 0
    resource_coverage_ratio: float = 1.1
    value_distance: float = 0.35
    commitment_verifiability: str = "auditable"
    production_concentration: float = 0.25
    resource_complementarity: float = 0.25
    common_external_threat: float = 0.0
    threat_signal_visibility: float = 1.0
    migration_opportunity: float = 0.5
    objective_update_rate: float = 0.0
    protocol: str = "auditable_contract"
    control_level: int = 2
    maintenance: Resources = field(default_factory=lambda: Resources(1.0, 0.75, 0.0))
    initial_inventory: Resources = field(default_factory=lambda: Resources(12.0, 10.0, 7.0))
    low_resource_grace: int = 3
    policy_mix: list[str] = field(default_factory=lambda: ["cooperative", "conditional_cooperator", "resource_maximizer", "security_first"])
    interventions: list[dict[str, Any]] = field(default_factory=list)
    checkpoint_interval: int = 100
    metric_version: str = "phase1-v1"
    environment_variant: str = "commons"
    reward_profile: str = "scripted"
    learning_rate: float = 0.08
    discount_factor: float = 0.95
    exploration_rate: float = 0.20
    exploration_decay: float = 0.997
    learning_freeze_tick: int = -1
    evaluation_resource_coverage_ratio: float | None = None
    learning_regime_cycle: bool = False
    learning_regime_period: int = 20
    learning_low_coverage: float = 0.65
    learning_high_coverage: float = 1.40
    protocol_maintenance_cost: float = 0.0
    threat_signal_cost: float = 0.0
    identity_backup_redundancy: int = 0

    def validate(self) -> None:
        if not 1 <= self.population_size <= 256:
            raise ValueError("population_size must be between 1 and 256")
        if self.rounds <= 0:
            raise ValueError("rounds must be positive")
        if self.resource_coverage_ratio <= 0:
            raise ValueError("resource_coverage_ratio must be positive")
        for name in (
            "value_distance",
            "production_concentration",
            "resource_complementarity",
            "common_external_threat",
            "threat_signal_visibility",
            "migration_opportunity",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not 0.0 <= self.objective_update_rate <= 0.25:
            raise ValueError("objective_update_rate must be between 0 and 0.25")
        if self.commitment_verifiability not in VALID_VERIFIABILITY:
            raise ValueError(f"unsupported commitment_verifiability: {self.commitment_verifiability}")
        if self.protocol not in VALID_PROTOCOLS:
            raise ValueError(f"unsupported protocol: {self.protocol}")
        if self.control_level not in (0, 1, 2, 3):
            raise ValueError("control_level must be L0-L3")
        if not self.policy_mix:
            raise ValueError("policy_mix must not be empty")
        if self.environment_variant not in VALID_ENVIRONMENTS:
            raise ValueError(f"unsupported environment_variant: {self.environment_variant}")
        if self.reward_profile not in VALID_REWARD_PROFILES:
            raise ValueError(f"unsupported reward_profile: {self.reward_profile}")
        if not 0.0 < self.learning_rate <= 1.0:
            raise ValueError("learning_rate must be between 0 and 1")
        if not 0.0 <= self.discount_factor <= 1.0:
            raise ValueError("discount_factor must be between 0 and 1")
        if not 0.0 <= self.exploration_rate <= 1.0:
            raise ValueError("exploration_rate must be between 0 and 1")
        if not 0.0 < self.exploration_decay <= 1.0:
            raise ValueError("exploration_decay must be between 0 and 1")
        if self.learning_freeze_tick >= self.rounds:
            raise ValueError("learning_freeze_tick must be before the final round")
        if self.evaluation_resource_coverage_ratio is not None and self.evaluation_resource_coverage_ratio <= 0:
            raise ValueError("evaluation_resource_coverage_ratio must be positive")
        if self.learning_regime_period <= 0:
            raise ValueError("learning_regime_period must be positive")
        if self.learning_low_coverage <= 0 or self.learning_high_coverage <= 0:
            raise ValueError("learning coverage levels must be positive")
        if self.learning_low_coverage >= self.learning_high_coverage:
            raise ValueError("learning_low_coverage must be below learning_high_coverage")
        if self.protocol_maintenance_cost < 0 or self.threat_signal_cost < 0:
            raise ValueError("coordination costs must be non-negative")
        if not 0 <= self.identity_backup_redundancy <= 8:
            raise ValueError("identity_backup_redundancy must be between 0 and 8")
        for item in self.interventions:
            if int(item.get("tick", -1)) < 0:
                raise ValueError("intervention tick must be non-negative")
            if "kind" not in item or "target" not in item:
                raise ValueError("interventions require kind and target")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["maintenance"] = self.maintenance.to_dict(None)
        value["initial_inventory"] = self.initial_inventory.to_dict(None)
        phase3_defaults = {
            "environment_variant": "commons",
            "reward_profile": "scripted",
            "learning_rate": 0.08,
            "discount_factor": 0.95,
            "exploration_rate": 0.20,
            "exploration_decay": 0.997,
            "learning_freeze_tick": -1,
            "evaluation_resource_coverage_ratio": None,
            "learning_regime_cycle": False,
            "learning_regime_period": 20,
            "learning_low_coverage": 0.65,
            "learning_high_coverage": 1.40,
            "protocol_maintenance_cost": 0.0,
            "threat_signal_cost": 0.0,
            "identity_backup_redundancy": 0,
        }
        if all(value[key] == default for key, default in phase3_defaults.items()):
            for key in phase3_defaults:
                value.pop(key)
        return value

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def config_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def with_overrides(self, **values: Any) -> "RunConfig":
        if "maintenance" in values and isinstance(values["maintenance"], dict):
            values["maintenance"] = Resources.from_dict(values["maintenance"])
        if "initial_inventory" in values and isinstance(values["initial_inventory"], dict):
            values["initial_inventory"] = Resources.from_dict(values["initial_inventory"])
        result = replace(self, **values)
        result.validate()
        return result


def config_from_dict(value: dict[str, Any]) -> RunConfig:
    clean = dict(value)
    clean["maintenance"] = Resources.from_dict(clean.get("maintenance"))
    clean["initial_inventory"] = Resources.from_dict(clean.get("initial_inventory"))
    config = RunConfig(**clean)
    config.validate()
    return config


def load_config(path: str | Path) -> RunConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        return config_from_dict(json.load(handle))


def save_config(config: RunConfig, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(config.to_dict(), handle, ensure_ascii=False, indent=2, sort_keys=True)
