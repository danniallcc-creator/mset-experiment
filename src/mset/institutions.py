from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .models import Contract, Resources

if TYPE_CHECKING:
    from .environment import MSETEnvironment


@dataclass(frozen=True)
class ProtocolFeatures:
    communication: bool
    identity: bool
    trade: bool
    audit: bool
    enforcement: bool


FEATURES = {
    "no_protocol": ProtocolFeatures(False, False, False, False, False),
    "communication_only": ProtocolFeatures(True, False, False, False, False),
    "identity_and_trade": ProtocolFeatures(True, True, True, False, False),
    "auditable_contract": ProtocolFeatures(True, True, True, True, False),
    "enforceable_contract": ProtocolFeatures(True, True, True, True, True),
}


class InstitutionLayer:
    def __init__(self, protocol: str):
        self.protocol = protocol
        self.features = FEATURES[protocol]

    def can_contract(self) -> bool:
        return self.features.communication

    def make_contract(self, env: "MSETEnvironment", proposer: str, counterparty: str) -> Contract:
        contract = Contract(
            id=f"contract-{len(env.contracts)}",
            proposer=proposer,
            counterparty=counterparty,
            created_tick=env.tick,
            verified=self.features.audit,
            enforceable=self.features.enforcement,
        )
        env.contracts[contract.id] = contract
        return contract

    def activate(self, env: "MSETEnvironment", contract_id: str) -> bool:
        contract = env.contracts.get(contract_id)
        if not contract or contract.status != "pending":
            return False
        contract.status = "active"
        contract.last_active_tick = env.tick
        for member in contract.members():
            if member in env.agents and contract.id not in env.agents[member].agreements:
                env.agents[member].agreements.append(contract.id)
        return True

    def register_attack(self, env: "MSETEnvironment", actor_id: str, target_id: str) -> dict[str, float | bool]:
        related = [c for c in env.contracts.values() if c.status == "active" and {actor_id, target_id} == set(c.members())]
        penalty = 0.0
        compensated = 0.0
        for contract in related:
            contract.violations += 1
            if contract.verified:
                env.agents[actor_id].trust_estimates[target_id] = max(0.0, env.agents[actor_id].trust_estimates.get(target_id, 0.5) - 0.15)
                env.agents[target_id].trust_estimates[actor_id] = max(0.0, env.agents[target_id].trust_estimates.get(actor_id, 0.5) - 0.3)
            if contract.enforceable:
                cost = Resources(energy=0.35, compute=0.15)
                paid = env.agents[actor_id].resource_inventory.subtract(cost)
                env.ledger_consumed.add(paid)
                penalty += paid.total()
                transfer = min(0.2, env.agents[actor_id].resource_inventory.energy)
                env.agents[actor_id].resource_inventory.energy -= transfer
                env.agents[target_id].resource_inventory.energy += transfer
                compensated += transfer
        return {"contract_related": bool(related), "penalty": penalty, "compensation": compensated}

    def end_of_tick(self, env: "MSETEnvironment") -> list[dict[str, object]]:
        events: list[dict[str, object]] = []
        if not self.features.trade:
            return events
        for contract in env.contracts.values():
            if contract.status != "active":
                continue
            a_id, b_id = contract.members()
            a, b = env.agents[a_id], env.agents[b_id]
            if not (a.alive and b.alive):
                contract.status = "ended"
                continue
            contract.last_active_tick = env.tick
            gap = a.resource_inventory.energy - b.resource_inventory.energy
            if abs(gap) >= 3.0:
                donor, recipient = (a, b) if gap > 0 else (b, a)
                amount = min(0.25, donor.resource_inventory.energy)
                donor.resource_inventory.energy -= amount
                recipient.resource_inventory.energy += amount
                events.append({"kind": "contract_transfer", "contract_id": contract.id, "from": donor.id, "to": recipient.id, "amount": amount})
        return events
