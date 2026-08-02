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
        for item in self.interventions:
            if int(item.get("tick", -1)) < 0:
                raise ValueError("intervention tick must be non-negative")
            if "kind" not in item or "target" not in item:
                raise ValueError("interventions require kind and target")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["maintenance"] = self.maintenance.to_dict(None)
        value["initial_inventory"] = self.initial_inventory.to_dict(None)
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
