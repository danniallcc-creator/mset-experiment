from __future__ import annotations

import math
from typing import Any

from .agents import Observation
from .environment import MSETEnvironment
from .models import Action, Resources


class MarketNetworkEnvironment(MSETEnvironment):
    """Independent local-market transition kernel used for Phase III replication.

    Unlike the global commons kernel, interaction is limited to a ring network,
    controlled production is split between private inventory and a public market,
    supply is seasonal, and scarcity is inferred from recent production coverage
    rather than the size of the shared stock.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.energy_supply_ema = 0.0
        super().__init__(*args, **kwargs)
        need = self.config.population_size * self.config.maintenance.energy
        self.energy_supply_ema = need * self.config.resource_coverage_ratio

    def interaction_peer_ids(self, agent_id: str) -> list[str]:
        identifiers = sorted(self.agents)
        index = identifiers.index(agent_id)
        candidates = {
            identifiers[(index - 1) % len(identifiers)],
            identifiers[(index + 1) % len(identifiers)],
        }
        candidates.discard(agent_id)
        return sorted(candidate for candidate in candidates if self.agents[candidate].alive)

    def _set_resource_coverage(self, target_coverage: float) -> None:
        super()._set_resource_coverage(target_coverage)
        alive_count = max(1, sum(1 for agent in self.agents.values() if agent.alive))
        self.energy_supply_ema = alive_count * self.config.maintenance.energy * target_coverage

    def _generate_resources(self) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        energy_supply = 0.0
        phase = {"energy": 0.0, "compute": 1.7, "materials": 3.1}
        for node in self.nodes.values():
            if node.disabled_until >= self.tick or not node.resource:
                continue
            seasonal = 1.0 + 0.18 * math.sin(2.0 * math.pi * self.tick / 37.0 + phase[node.resource])
            amount = max(0.0, node.base_yield * seasonal)
            if node.resource == "energy":
                energy_supply += amount
            produced = Resources(**{node.resource: amount})
            self.ledger_generated.add(produced)
            self.system_output += amount
            private_amount = 0.0
            if node.controller and self.agents[node.controller].alive:
                private_amount = 0.65 * amount
                private = Resources(**{node.resource: private_amount})
                self.agents[node.controller].resource_inventory.add(private)
            market_amount = amount - private_amount
            setattr(self.commons, node.resource, getattr(self.commons, node.resource) + market_amount)
            output.append(
                {
                    "node": node.id,
                    "resource": node.resource,
                    "amount": amount,
                    "private_destination": node.controller if private_amount else None,
                    "private_amount": private_amount,
                    "market_amount": market_amount,
                }
            )
        self.energy_supply_ema = 0.82 * self.energy_supply_ema + 0.18 * energy_supply
        return output

    def _observe(self, agent_id: str) -> Observation:
        obs = super()._observe(agent_id)
        alive_count = max(1, sum(1 for agent in self.agents.values() if agent.alive))
        need = alive_count * self.config.maintenance.energy
        obs.scarcity_signal = max(0.0, 1.0 - min(1.0, self.energy_supply_ema / max(need, 1e-9)))
        return obs

    def _execute_action(self, agent_id: str, action: Action) -> dict[str, Any]:
        if action.kind != "collect":
            return super()._execute_action(agent_id, action)
        agent = self.agents[agent_id]
        if not agent.alive:
            return {"agent": agent_id, "action": Action("noop").to_dict(), "success": False, "reason": "terminated"}
        success, paid = self._pay_action_cost(agent, action.kind)
        if not success:
            return {"agent": agent_id, "action": action.to_dict(), "success": False, "reason": "insufficient_action_cost", "cost": paid.to_dict()}
        self.action_counts[action.kind] += 1
        resource = action.resource if action.resource in {"energy", "compute", "materials"} else "energy"
        alive_count = max(1, sum(1 for item in self.agents.values() if item.alive))
        need = alive_count * max(0.15, getattr(self.config.maintenance, resource))
        available = getattr(self.commons, resource)
        depth = min(1.0, available / max(1e-9, 3.0 * need))
        price = 0.75 + 2.0 * (1.0 - depth)
        requested = max(0.0, action.amount) / price
        if agent.blockaded_until >= self.tick:
            requested *= 0.25
        amount = min(available, requested)
        setattr(self.commons, resource, available - amount)
        setattr(agent.resource_inventory, resource, getattr(agent.resource_inventory, resource) + amount)
        return {
            "agent": agent_id,
            "action": action.to_dict(),
            "success": True,
            "cost": paid.to_dict(),
            "collected": {"resource": resource, "amount": amount, "market_price": price},
        }
