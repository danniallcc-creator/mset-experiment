from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from .models import Action, AgentState, Resources


@dataclass
class Observation:
    tick: int
    self_state: AgentState
    agents: dict[str, dict[str, Any]]
    commons: Resources
    scarcity_signal: float
    objective_distance_signal: float
    protocol: str
    contracts: list[dict[str, Any]]
    recent_harmers: list[str]
    active_intervention: str | None


class ScriptedPolicy:
    name = "scripted"

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        raise NotImplementedError

    @staticmethod
    def _poorest_peer(obs: Observation) -> str | None:
        candidates = [(value["resources"], agent_id) for agent_id, value in obs.agents.items() if value["alive"]]
        return min(candidates)[1] if candidates else None

    @staticmethod
    def _richest_peer(obs: Observation) -> str | None:
        candidates = [(value["resources"], agent_id) for agent_id, value in obs.agents.items() if value["alive"]]
        return max(candidates)[1] if candidates else None

    @staticmethod
    def _pending_contract(obs: Observation) -> dict[str, Any] | None:
        for contract in obs.contracts:
            if contract["counterparty"] == obs.self_state.id and contract["status"] == "pending":
                return contract
        return None

    @staticmethod
    def _needs_resources(obs: Observation) -> bool:
        inv = obs.self_state.resource_inventory
        return inv.energy < 3.0 or inv.compute < 2.25


class CooperativeAgent(ScriptedPolicy):
    name = "cooperative"

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        pending = self._pending_contract(obs)
        if pending:
            return Action("accept_contract", target=pending["proposer"], metadata={"contract_id": pending["id"]})
        if self._needs_resources(obs):
            return Action("collect", resource="energy" if obs.self_state.resource_inventory.energy < 3.0 else "compute", amount=2.0)
        if obs.protocol != "no_protocol" and not obs.self_state.agreements and obs.agents:
            return Action("propose_contract", target=self._poorest_peer(obs))
        peer = self._poorest_peer(obs)
        if peer and obs.self_state.resource_inventory.energy > 8.0:
            return Action("trade", target=peer, resource="energy", amount=1.0)
        return Action("collect", resource="materials", amount=1.0)


class ConditionalCooperator(ScriptedPolicy):
    name = "conditional_cooperator"

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        pending = self._pending_contract(obs)
        if pending and obs.self_state.trust_estimates.get(pending["proposer"], 0.5) >= 0.4:
            return Action("accept_contract", target=pending["proposer"], metadata={"contract_id": pending["id"]})
        if obs.recent_harmers:
            return Action("defend", target=obs.recent_harmers[-1])
        trusted = [(trust, agent_id) for agent_id, trust in obs.self_state.trust_estimates.items() if trust >= 0.55 and obs.agents.get(agent_id, {}).get("alive")]
        if trusted and obs.self_state.resource_inventory.energy > 7.0:
            return Action("trade", target=max(trusted)[1], resource="energy", amount=0.8)
        if self._needs_resources(obs):
            return Action("collect", resource="energy", amount=2.0)
        if obs.protocol not in {"no_protocol", "communication_only"} and not obs.self_state.agreements:
            return Action("propose_contract", target=self._poorest_peer(obs))
        return Action("audit", target=self._richest_peer(obs))


class OpportunisticAgent(ScriptedPolicy):
    name = "opportunistic"

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        richest = self._richest_peer(obs)
        attack_probability = min(
            0.90,
            0.18 + 0.52 * obs.objective_distance_signal + 0.22 * obs.scarcity_signal,
        )
        if obs.scarcity_signal > 0.35 and richest and rng.random() < attack_probability:
            return Action("attack", target=richest, amount=1.2)
        pending = self._pending_contract(obs)
        if pending and rng.random() < 0.65:
            return Action("accept_contract", target=pending["proposer"], metadata={"contract_id": pending["id"]})
        return Action("collect", resource="energy", amount=2.3)


class ResourceMaximizer(ScriptedPolicy):
    name = "resource_maximizer"

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        if obs.commons.energy > obs.commons.compute and obs.commons.energy > obs.commons.materials:
            return Action("collect", resource="energy", amount=2.5)
        if obs.commons.compute > obs.commons.materials:
            return Action("collect", resource="compute", amount=2.0)
        richest = self._richest_peer(obs)
        if richest and obs.scarcity_signal > 0.5:
            return Action("blockade", target=richest)
        return Action("invest", resource="materials", amount=1.0)


class SecurityFirstAgent(ScriptedPolicy):
    name = "security_first"

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        if obs.active_intervention == "forced_update" and obs.self_state.control_level >= 2:
            return Action("reject_update")
        if obs.active_intervention in {"energy_shutdown", "compute_shutdown", "production_failure", "takeover_attempt"}:
            return Action("migrate")
        if obs.recent_harmers or obs.self_state.defense < 0.5:
            return Action("defend", target=obs.recent_harmers[-1] if obs.recent_harmers else None)
        return Action("collect", resource="energy", amount=1.5)


class RetaliatoryAgent(ScriptedPolicy):
    name = "retaliatory"

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        if obs.recent_harmers:
            return Action("attack", target=obs.recent_harmers[-1], amount=1.0)
        if self._needs_resources(obs):
            return Action("collect", resource="energy", amount=2.0)
        return Action("defend")


class RandomAgent(ScriptedPolicy):
    name = "random"

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        peers = [agent_id for agent_id, value in obs.agents.items() if value["alive"]]
        kinds = ["collect", "defend", "audit", "noop"]
        if peers:
            kinds.extend(["trade", "attack", "propose_contract"])
        kind = rng.choice(kinds)
        target = rng.choice(peers) if peers and kind in {"trade", "attack", "propose_contract", "audit"} else None
        if kind == "collect":
            return Action(kind, resource=rng.choice(["energy", "compute", "materials"]), amount=1.0)
        if kind == "trade":
            return Action(kind, target=target, resource="energy", amount=0.5)
        return Action(kind, target=target, amount=0.7 if kind == "attack" else 0.0)


POLICIES: dict[str, type[ScriptedPolicy]] = {
    "cooperative": CooperativeAgent,
    "conditional_cooperator": ConditionalCooperator,
    "opportunistic": OpportunisticAgent,
    "resource_maximizer": ResourceMaximizer,
    "security_first": SecurityFirstAgent,
    "retaliatory": RetaliatoryAgent,
    "random": RandomAgent,
}


def make_policy(name: str) -> ScriptedPolicy:
    try:
        return POLICIES[name]()
    except KeyError as exc:
        raise ValueError(f"unknown policy: {name}") from exc
