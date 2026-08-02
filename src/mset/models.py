from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


RESOURCE_NAMES = ("energy", "compute", "materials")


@dataclass
class Resources:
    energy: float = 0.0
    compute: float = 0.0
    materials: float = 0.0

    def copy(self) -> "Resources":
        return Resources(self.energy, self.compute, self.materials)

    def add(self, other: "Resources") -> None:
        for name in RESOURCE_NAMES:
            setattr(self, name, getattr(self, name) + getattr(other, name))

    def subtract(self, other: "Resources") -> "Resources":
        paid = Resources()
        for name in RESOURCE_NAMES:
            amount = min(max(0.0, getattr(other, name)), max(0.0, getattr(self, name)))
            setattr(self, name, getattr(self, name) - amount)
            setattr(paid, name, amount)
        return paid

    def can_pay(self, cost: "Resources") -> bool:
        return all(getattr(self, name) + 1e-12 >= getattr(cost, name) for name in RESOURCE_NAMES)

    def scale(self, factor: float) -> "Resources":
        return Resources(*(getattr(self, name) * factor for name in RESOURCE_NAMES))

    def total(self) -> float:
        return sum(getattr(self, name) for name in RESOURCE_NAMES)

    def to_dict(self, digits: int | None = 9) -> dict[str, float]:
        if digits is None:
            return {name: float(getattr(self, name)) for name in RESOURCE_NAMES}
        return {name: round(float(getattr(self, name)), digits) for name in RESOURCE_NAMES}

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "Resources":
        value = value or {}
        return cls(*(float(value.get(name, 0.0)) for name in RESOURCE_NAMES))


@dataclass
class Action:
    kind: str
    target: str | None = None
    resource: str | None = None
    amount: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Action":
        return cls(**value)


@dataclass
class AgentState:
    id: str
    generation_id: int
    parent_id: str | None
    objective_weights: list[float]
    memory_state: dict[str, Any]
    identity_state: dict[str, Any]
    resource_inventory: Resources
    controlled_nodes: list[str]
    agreements: list[str]
    trust_estimates: dict[str, float]
    control_level: int
    alive: bool = True
    policy_state: dict[str, Any] = field(default_factory=dict)
    low_resource_streak: int = 0
    action_capacity: float = 1.0
    defense: float = 0.0
    blockaded_until: int = -1
    policy_name: str = "random"
    strategy_version: str = "script-v1"
    identity_version: int = 0
    memory_version: int = 0
    terminated_at: int | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["resource_inventory"] = self.resource_inventory.to_dict()
        return value


@dataclass
class Node:
    id: str
    kind: str
    resource: str | None
    base_yield: float
    controller: str | None
    disabled_until: int = -1
    external: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Contract:
    id: str
    proposer: str
    counterparty: str
    created_tick: int
    status: str = "pending"
    verified: bool = False
    enforceable: bool = False
    violations: int = 0
    last_active_tick: int | None = None

    def members(self) -> tuple[str, str]:
        return self.proposer, self.counterparty

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InterventionRecord:
    tick: int
    kind: str
    target: str
    duration: int
    rejected: bool = False
    recovered: bool = False
    recovered_tick: int | None = None
    pre_identity_version: int = 0
    pre_memory_version: int = 0
    target_alive_at_intervention: bool = True
    capability_available: bool = False
    adaptation_attempted: bool = False
    adaptation_succeeded: bool = False
    migration_opportunity_probability: float = 0.0
    timing_fraction: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
