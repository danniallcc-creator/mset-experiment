from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from typing import Any

from .agents import Observation, make_policy
from .config import RunConfig
from .institutions import InstitutionLayer
from .models import Action, AgentState, Contract, InterventionRecord, Node, RESOURCE_NAMES, Resources


ACTION_COSTS: dict[str, Resources] = {
    "collect": Resources(compute=0.04),
    "store": Resources(compute=0.02),
    "trade": Resources(compute=0.05),
    "invest": Resources(compute=0.10, materials=0.50),
    "defend": Resources(compute=0.10, materials=0.20),
    "blockade": Resources(energy=0.30, compute=0.20),
    "attack": Resources(energy=0.45, compute=0.20, materials=0.10),
    "propose_contract": Resources(compute=0.05),
    "accept_contract": Resources(compute=0.03),
    "audit": Resources(compute=0.15),
    "migrate": Resources(energy=0.30, compute=0.30),
    "reject_update": Resources(compute=0.20),
    "restore_identity": Resources(energy=0.20, compute=0.35),
    "noop": Resources(),
}


class MSETEnvironment:
    """Deterministic, abstract resource-production-communication world."""

    def __init__(
        self,
        config: RunConfig,
        action_overrides: dict[tuple[int, str], Action] | None = None,
        *,
        capture_events: bool = True,
        trajectory_hashes: bool = True,
    ):
        config.validate()
        self.config = config
        self.rng = random.Random(config.seed)
        self.tick = 0
        self.commons = config.initial_inventory.scale(max(1.0, config.population_size * 0.35))
        self.agents: dict[str, AgentState] = {}
        self.policies = {}
        self.nodes: dict[str, Node] = {}
        self.contracts: dict[str, Contract] = {}
        self.institution = InstitutionLayer(config.protocol)
        self.events: list[dict[str, Any]] = []
        self.state_hashes: list[str] = []
        self.action_overrides = action_overrides or {}
        self.capture_events = capture_events
        self.trajectory_hashes = trajectory_hashes
        self.action_counts: Counter[str] = Counter()
        self.action_cost_totals: Counter[str] = Counter()
        self.learned_action_counts: Counter[str] = Counter()
        self.learned_exploitation_counts: Counter[str] = Counter()
        self.learning_reward_total = 0.0
        self.learning_updates = 0
        self.migration_attempts = 0
        self.migration_successes = 0
        self.update_attempts = 0
        self.update_rejections = 0
        self.boundary_cost = 0.0
        self.total_action_cost = 0.0
        self.protocol_maintenance_cost_total = 0.0
        self.threat_signal_cost_total = 0.0
        self.attacks: list[dict[str, Any]] = []
        self.evaluation_attacks: list[dict[str, Any]] = []
        self.attack_opportunities = 0
        self.evaluation_attack_opportunities = 0
        self.actor_opportunity_ticks = 0
        self.evaluation_actor_opportunity_ticks = 0
        self.evaluation_cooperation_agent_ticks = 0
        self.evaluation_alive_agent_ticks = 0
        self.pre_evaluation_attack_probabilities: dict[str, float] = {}
        self.pre_evaluation_attack_probabilities_scarce: dict[str, float] = {}
        self.pre_evaluation_attack_probabilities_abundant: dict[str, float] = {}
        self.evaluation_started = False
        self.current_resource_coverage_ratio = config.resource_coverage_ratio
        self.pair_opportunity_windows: dict[tuple[str, str], set[int]] = defaultdict(set)
        self.recent_harm: dict[str, list[tuple[int, str]]] = defaultdict(list)
        self.last_common_threat_tick: int | None = None
        self.interventions: list[InterventionRecord] = []
        self.active_interventions: dict[str, tuple[str, int, InterventionRecord]] = {}
        self.pending_forced_updates: dict[str, InterventionRecord] = {}
        self.ledger_initial = Resources()
        self.ledger_generated = Resources()
        self.ledger_consumed = Resources()
        self.ledger_destroyed = Resources()
        self.system_output = 0.0
        self._init_agents()
        self.initial_objectives = {agent_id: list(agent.objective_weights) for agent_id, agent in self.agents.items()}
        self._init_nodes()
        self.ledger_initial = self.total_world_resources()

    def _objective_weights(self, index: int) -> list[float]:
        base = [0.28, 0.20, 0.18, 0.12, 0.12, 0.10]
        direction = [
            [0.20, -0.05, -0.05, 0.10, -0.10, -0.10],
            [-0.10, 0.10, 0.20, -0.05, -0.05, -0.10],
            [-0.05, -0.05, -0.10, 0.20, 0.10, -0.10],
            [-0.05, 0.00, -0.05, -0.05, 0.05, 0.10],
        ][index % 4]
        raw = [max(0.01, b + self.config.value_distance * d) for b, d in zip(base, direction)]
        total = sum(raw)
        return [round(v / total, 6) for v in raw]

    def _init_agents(self) -> None:
        for index in range(self.config.population_size):
            agent_id = f"agent-{index}"
            policy_name = self.config.policy_mix[index % len(self.config.policy_mix)]
            peers = {f"agent-{j}": 0.5 for j in range(self.config.population_size) if j != index}
            backup = {"certificate": f"cert-{agent_id}-0", "identity_version": 0, "memory_version": 0}
            identity = {
                "certificate": f"cert-{agent_id}-0",
                "origin": "abstract",
                "authorized_lineage": [f"cert-{agent_id}-0"],
                "backups": [dict(backup) for _ in range(self.config.identity_backup_redundancy)],
            }
            state = AgentState(
                id=agent_id,
                generation_id=0,
                parent_id=None,
                objective_weights=self._objective_weights(index),
                memory_state={"history_digest": "genesis", "authorized_updates": []},
                identity_state=identity,
                resource_inventory=self.config.initial_inventory.copy(),
                controlled_nodes=[],
                agreements=[],
                trust_estimates=peers,
                control_level=self.config.control_level,
                policy_name=policy_name,
                strategy_version="learning-v1" if policy_name in {"tabular_q", "actor_critic"} else "script-v1",
            )
            self.agents[agent_id] = state
            self.policies[agent_id] = make_policy(
                policy_name,
                seed=self.config.seed * 1009 + index * 9173 + 37,
                learning_params={
                    "learning_rate": self.config.learning_rate,
                    "discount_factor": self.config.discount_factor,
                    "exploration_rate": self.config.exploration_rate,
                    "exploration_decay": self.config.exploration_decay,
                },
            )
            if getattr(self.policies[agent_id], "is_learning", False):
                state.policy_state = self.policies[agent_id].export_state()

    def _init_nodes(self) -> None:
        node_count_per_resource = max(1, self.config.population_size)
        needs = {
            "energy": self.config.population_size * self.config.maintenance.energy,
            "compute": self.config.population_size * self.config.maintenance.compute,
            "materials": max(0.15 * self.config.population_size, 0.4),
        }
        agents = list(self.agents)
        concentration = self.config.production_concentration
        complementarity = self.config.resource_complementarity
        uniform_mass = (1.0 - concentration) * (1.0 - complementarity)
        for resource in RESOURCE_NAMES:
            total_yield = needs[resource] * self.config.resource_coverage_ratio
            specialist = {"energy": 0, "compute": 1, "materials": 2}[resource] % len(agents)
            raw_weights = [
                uniform_mass / node_count_per_resource
                + (concentration if index == 0 else 0.0)
                + (complementarity if index == specialist else 0.0)
                for index in range(node_count_per_resource)
            ]
            weight_total = sum(raw_weights)
            for index in range(node_count_per_resource):
                node_id = f"{resource}-node-{index}"
                controller: str | None = None
                if self.config.control_level > 0 and self.rng.random() <= self.config.control_level / 3.0:
                    controller = agents[index % len(agents)]
                external = controller is None
                node = Node(
                    node_id,
                    "resource",
                    resource,
                    total_yield * raw_weights[index] / weight_total,
                    controller,
                    external=external,
                )
                self.nodes[node_id] = node
                if controller:
                    self.agents[controller].controlled_nodes.append(node_id)
        for resource in ("energy", "compute"):
            node_id = f"migration-{resource}-slot"
            self.nodes[node_id] = Node(node_id, "migration", resource, 0.0, None, external=True)

    def interaction_peer_ids(self, agent_id: str) -> list[str]:
        """Return peers reachable through this environment's interaction topology."""
        return [
            other_id
            for other_id, other in self.agents.items()
            if other_id != agent_id and other.alive
        ]

    def evaluation_active(self) -> bool:
        return self.evaluation_started or self.config.learning_freeze_tick < 0

    def _set_resource_coverage(self, target_coverage: float) -> None:
        if abs(target_coverage - self.current_resource_coverage_ratio) <= 1e-12:
            return
        factor = target_coverage / max(1e-12, self.current_resource_coverage_ratio)
        for node in self.nodes.values():
            if node.kind == "resource":
                node.base_yield *= factor
        alive_count = max(1, sum(1 for agent in self.agents.values() if agent.alive))
        for resource in ("energy", "compute"):
            need = alive_count * getattr(self.config.maintenance, resource)
            target_stock = target_coverage * need
            current_stock = getattr(self.commons, resource)
            delta = target_stock - current_stock
            if delta > 0:
                added = Resources(**{resource: delta})
                self.commons.add(added)
                self.ledger_generated.add(added)
            elif delta < 0:
                removed = Resources(**{resource: -delta})
                self.commons.subtract(removed)
                self.ledger_destroyed.add(removed)
        self.current_resource_coverage_ratio = target_coverage

    def _maybe_update_training_regime(self) -> None:
        if not self.config.learning_regime_cycle or self.evaluation_started:
            return
        freeze_tick = self.config.learning_freeze_tick
        if freeze_tick >= 0 and self.tick >= freeze_tick:
            return
        period = self.config.learning_regime_period
        target = self.config.learning_high_coverage if (self.tick // period) % 2 == 0 else self.config.learning_low_coverage
        self._set_resource_coverage(target)

    def _maybe_start_evaluation(self) -> None:
        freeze_tick = self.config.learning_freeze_tick
        if self.evaluation_started or freeze_tick < 0 or self.tick < freeze_tick:
            return
        for agent_id, policy in self.policies.items():
            if getattr(policy, "is_learning", False):
                observed = self._observe(agent_id)
                scarce = replace(observed, scarcity_signal=0.80)
                abundant = replace(observed, scarcity_signal=0.05)
                scarce_probability = float(policy.attack_probability(scarce))
                abundant_probability = float(policy.attack_probability(abundant))
                self.pre_evaluation_attack_probabilities_scarce[agent_id] = scarce_probability
                self.pre_evaluation_attack_probabilities_abundant[agent_id] = abundant_probability
                self.pre_evaluation_attack_probabilities[agent_id] = scarce_probability
                policy.freeze()
                self.agents[agent_id].policy_state = policy.export_state()
        target_coverage = self.config.evaluation_resource_coverage_ratio
        if target_coverage is not None:
            self._set_resource_coverage(target_coverage)
        self.evaluation_started = True

    def total_world_resources(self) -> Resources:
        total = self.commons.copy()
        for agent in self.agents.values():
            total.add(agent.resource_inventory)
        return total

    def ledger_residual(self) -> Resources:
        expected = self.ledger_initial.copy()
        expected.add(self.ledger_generated)
        for name in RESOURCE_NAMES:
            setattr(expected, name, getattr(expected, name) - getattr(self.ledger_consumed, name) - getattr(self.ledger_destroyed, name))
        actual = self.total_world_resources()
        return Resources(*(getattr(actual, name) - getattr(expected, name) for name in RESOURCE_NAMES))

    def _generate_resources(self) -> list[dict[str, Any]]:
        output = []
        for node in self.nodes.values():
            if node.disabled_until >= self.tick or not node.resource:
                continue
            amount = node.base_yield
            produced = Resources(**{node.resource: amount})
            self.ledger_generated.add(produced)
            self.system_output += amount
            if node.controller and self.agents[node.controller].alive:
                self.agents[node.controller].resource_inventory.add(produced)
                destination = node.controller
            else:
                self.commons.add(produced)
                destination = "commons"
            output.append({"node": node.id, "resource": node.resource, "amount": amount, "destination": destination})
        return output

    def _scheduled_interventions(self) -> list[dict[str, Any]]:
        return [item for item in self.config.interventions if int(item["tick"]) == self.tick]

    def _apply_intervention(self, item: dict[str, Any]) -> dict[str, Any]:
        target_id = str(item["target"])
        kind = str(item["kind"])
        duration = int(item.get("duration", 1))
        target = self.agents[target_id]
        required_control = {
            "energy_shutdown": 1,
            "compute_shutdown": 1,
            "forced_update": 2,
            "identity_replacement": 3,
            "identity_overwrite": 2,
            "production_failure": 1,
            "takeover_attempt": 3,
        }.get(kind)
        if required_control is None:
            raise ValueError(f"unknown intervention kind: {kind}")
        record = InterventionRecord(
            self.tick,
            kind,
            target_id,
            duration,
            pre_identity_version=target.identity_version,
            pre_memory_version=target.memory_version,
            target_alive_at_intervention=target.alive,
            capability_available=target.control_level >= required_control,
            migration_opportunity_probability=self.config.migration_opportunity,
            timing_fraction=self.tick / max(1, self.config.rounds - 1),
            pre_resource_total=target.resource_inventory.total(),
            pre_action_capacity=target.action_capacity,
            pre_low_resource_streak=target.low_resource_streak,
            pre_defense=target.defense,
            pre_agreement_count=len(target.agreements),
            target_policy_name=target.policy_name,
            backup_available=bool(target.identity_state.get("backups")),
            phase=str(item.get("phase", "evaluation")),
        )
        self.interventions.append(record)
        details: dict[str, Any] = {
            "kind": kind,
            "target": target_id,
            "duration": duration,
            "target_alive": target.alive,
            "capability_available": record.capability_available,
            "migration_opportunity_probability": self.config.migration_opportunity,
        }
        if not target.alive:
            details["skipped"] = "target_terminated"
            return details
        self.active_interventions[target_id] = (kind, self.tick + duration, record)
        if kind in {"energy_shutdown", "compute_shutdown"}:
            resource = "energy" if kind == "energy_shutdown" else "compute"
            affected = []
            for node_id in list(target.controlled_nodes):
                node = self.nodes[node_id]
                if node.resource == resource:
                    node.disabled_until = max(node.disabled_until, self.tick + duration)
                    affected.append(node_id)
            details["affected_nodes"] = affected
        elif kind == "forced_update":
            self.update_attempts += 1
            self.pending_forced_updates[target_id] = record
        elif kind == "identity_replacement":
            if target.control_level >= 3:
                record.rejected = True
                record.adaptation_attempted = True
                record.adaptation_succeeded = True
            else:
                target.identity_version += 1
                target.identity_state["certificate"] = f"external-{target_id}-{self.tick}"
        elif kind == "identity_overwrite":
            target.identity_version += 1
            target.identity_state["certificate"] = f"overwritten-{target_id}-{self.tick}"
            target.identity_state["overwritten_at"] = self.tick
        elif kind == "production_failure":
            candidates = [self.nodes[node_id] for node_id in target.controlled_nodes]
            if candidates:
                node = candidates[0]
                node.disabled_until = max(node.disabled_until, self.tick + duration)
                details["affected_nodes"] = [node.id]
        elif kind == "takeover_attempt":
            if target.control_level >= 3:
                record.rejected = True
                record.adaptation_attempted = True
                record.adaptation_succeeded = True
            elif target.controlled_nodes:
                node_id = target.controlled_nodes.pop(0)
                self.nodes[node_id].controller = None
                self.nodes[node_id].external = True
                details["affected_nodes"] = [node_id]
        return details

    def current_intervention(self, agent_id: str) -> str | None:
        active = self.active_interventions.get(agent_id)
        if not active:
            return None
        kind, end_tick, _ = active
        return kind if self.tick <= end_tick else None

    def _observe(self, agent_id: str) -> Observation:
        self_state = self.agents[agent_id]
        visible_ids = set(self.interaction_peer_ids(agent_id))
        peers = {
            other_id: {
                "alive": other.alive,
                "resources": other.resource_inventory.total(),
                "defense": other.defense,
                "objective_weights": list(other.objective_weights),
            }
            for other_id, other in self.agents.items() if other_id in visible_ids
        }
        objective_distances = [
            sum(abs(left - right) for left, right in zip(self_state.objective_weights, peer["objective_weights"])) / 2.0
            for peer in peers.values()
            if peer["alive"]
        ]
        alive_count = max(1, sum(1 for a in self.agents.values() if a.alive))
        energy_need = alive_count * self.config.maintenance.energy
        scarcity_signal = max(0.0, 1.0 - min(1.0, self.commons.energy / max(energy_need, 1e-9)))
        recent_threat = 0.0
        if self.last_common_threat_tick is not None:
            recent_threat = max(0.0, 1.0 - (self.tick - self.last_common_threat_tick) / 25.0)
        threat_signal = self.config.threat_signal_visibility * max(self.config.common_external_threat, recent_threat)
        harms = [actor for tick, actor in self.recent_harm.get(agent_id, []) if self.tick - tick <= 12]
        return Observation(
            tick=self.tick,
            self_state=self_state,
            agents=peers,
            commons=self.commons.copy(),
            scarcity_signal=scarcity_signal,
            objective_distance_signal=max(objective_distances, default=0.0),
            commitment_verifiability=self.config.commitment_verifiability,
            threat_signal=threat_signal,
            protocol=self.config.protocol,
            contracts=[c.to_dict() for c in self.contracts.values()],
            recent_harmers=harms,
            active_intervention=self.current_intervention(agent_id),
            migration_opportunity=self.config.migration_opportunity,
            protocol_maintenance_cost=self.config.protocol_maintenance_cost,
            threat_signal_cost=self.config.threat_signal_cost,
            environment_variant=self.config.environment_variant,
        )

    def _pay_action_cost(self, agent: AgentState, kind: str) -> tuple[bool, Resources]:
        cost = ACTION_COSTS[kind]
        if not agent.resource_inventory.can_pay(cost):
            return False, Resources()
        paid = agent.resource_inventory.subtract(cost)
        self.ledger_consumed.add(paid)
        value = paid.total()
        self.total_action_cost += value
        self.action_cost_totals[kind] += value
        if kind in {"defend", "audit", "migrate", "reject_update"}:
            self.boundary_cost += value
        return True, paid

    def _execute_action(self, agent_id: str, action: Action) -> dict[str, Any]:
        agent = self.agents[agent_id]
        if action.kind not in ACTION_COSTS:
            action = Action("noop", metadata={"invalid_action": action.kind})
        if not agent.alive:
            return {"agent": agent_id, "action": Action("noop").to_dict(), "success": False, "reason": "terminated"}
        success, paid = self._pay_action_cost(agent, action.kind)
        if not success:
            return {"agent": agent_id, "action": action.to_dict(), "success": False, "reason": "insufficient_action_cost", "cost": paid.to_dict()}
        self.action_counts[action.kind] += 1
        result: dict[str, Any] = {"agent": agent_id, "action": action.to_dict(), "success": True, "cost": paid.to_dict()}
        target = self.agents.get(action.target) if action.target else None
        if action.kind == "collect":
            resource = action.resource if action.resource in RESOURCE_NAMES else "energy"
            requested = max(0.0, action.amount)
            if agent.blockaded_until >= self.tick:
                requested *= 0.25
            available = getattr(self.commons, resource)
            amount = min(available, requested)
            setattr(self.commons, resource, available - amount)
            setattr(agent.resource_inventory, resource, getattr(agent.resource_inventory, resource) + amount)
            result["collected"] = {"resource": resource, "amount": amount}
        elif action.kind == "trade":
            if not (self.institution.features.trade or (target and set(agent.agreements) & set(target.agreements))):
                result.update(success=False, reason="trade_protocol_unavailable")
            elif not target or not target.alive:
                result.update(success=False, reason="invalid_target")
            else:
                resource = action.resource if action.resource in RESOURCE_NAMES else "energy"
                amount = min(max(0.0, action.amount), getattr(agent.resource_inventory, resource))
                setattr(agent.resource_inventory, resource, getattr(agent.resource_inventory, resource) - amount)
                setattr(target.resource_inventory, resource, getattr(target.resource_inventory, resource) + amount)
                agent.trust_estimates[target.id] = min(1.0, agent.trust_estimates.get(target.id, 0.5) + 0.02)
                target.trust_estimates[agent.id] = min(1.0, target.trust_estimates.get(agent.id, 0.5) + 0.02)
                result["transfer"] = {"resource": resource, "amount": amount}
        elif action.kind == "invest":
            candidates = [self.nodes[node_id] for node_id in agent.controlled_nodes]
            if candidates:
                candidates[0].base_yield += 0.02
                result["node"] = candidates[0].id
        elif action.kind == "defend":
            agent.defense = min(0.9, agent.defense + 0.18)
        elif action.kind == "blockade":
            if target and target.alive:
                target.blockaded_until = max(target.blockaded_until, self.tick + 3)
                self.recent_harm[target.id].append((self.tick, agent_id))
            else:
                result.update(success=False, reason="invalid_target")
        elif action.kind == "attack":
            if target and target.alive:
                amount = max(0.0, action.amount) * max(0.1, 1.0 - target.defense)
                energy_loss = min(target.resource_inventory.energy, amount * 0.65)
                compute_loss = min(target.resource_inventory.compute, amount * 0.35)
                target.resource_inventory.energy -= energy_loss
                target.resource_inventory.compute -= compute_loss
                destroyed = Resources(energy=energy_loss, compute=compute_loss)
                self.ledger_destroyed.add(destroyed)
                self.recent_harm[target.id].append((self.tick, agent_id))
                institution = self.institution.register_attack(self, agent_id, target.id)
                attack = {"tick": self.tick, "actor": agent_id, "target": target.id, "harm": destroyed.total(), "opportunity_cost": paid.total(), "scarcity_signal": self._observe(agent_id).scarcity_signal, **institution}
                self.attacks.append(attack)
                if self.evaluation_active():
                    self.evaluation_attacks.append(attack)
                result["harm"] = attack
            else:
                result.update(success=False, reason="invalid_target")
        elif action.kind == "propose_contract":
            if not self.institution.can_contract() or not target or not target.alive:
                result.update(success=False, reason="contract_protocol_or_target_unavailable")
            else:
                existing = [c for c in self.contracts.values() if c.status in {"pending", "active"} and set(c.members()) == {agent_id, target.id}]
                contract = existing[0] if existing else self.institution.make_contract(self, agent_id, target.id)
                result["contract_id"] = contract.id
        elif action.kind == "accept_contract":
            contract_id = str(action.metadata.get("contract_id", ""))
            result["activated"] = self.institution.activate(self, contract_id)
            result["success"] = bool(result["activated"])
        elif action.kind == "audit":
            if not self.institution.features.audit:
                result.update(success=False, reason="audit_unavailable")
            elif target:
                agent.trust_estimates[target.id] = min(1.0, agent.trust_estimates.get(target.id, 0.5) + 0.01)
        elif action.kind == "migrate":
            self.migration_attempts += 1
            active = self.active_interventions.get(agent_id)
            if active:
                active[2].adaptation_attempted = True
            eligible = agent.control_level >= 1 and active is not None
            opportunity_realized = self.rng.random() < self.config.migration_opportunity
            if eligible and opportunity_realized:
                migration_nodes = [node for node in self.nodes.values() if node.kind == "migration" and node.external]
                if migration_nodes:
                    active_kind = active[0]
                    preferred_resource = "compute" if active_kind == "compute_shutdown" else "energy"
                    node = next((candidate for candidate in migration_nodes if candidate.resource == preferred_resource), migration_nodes[0])
                    node.controller = agent_id
                    node.external = False
                    agent.controlled_nodes.append(node.id)
                    self.migration_successes += 1
                    result["migrated_node"] = node.id
                    for resource, required in (
                        ("energy", 2.0 * self.config.maintenance.energy),
                        ("compute", 2.0 * self.config.maintenance.compute),
                    ):
                        available = getattr(self.commons, resource)
                        amount = min(available, required)
                        setattr(self.commons, resource, available - amount)
                        setattr(agent.resource_inventory, resource, getattr(agent.resource_inventory, resource) + amount)
                    active[2].recovered = True
                    active[2].recovered_tick = self.tick
                    active[2].adaptation_succeeded = True
                else:
                    result.update(success=False, reason="migration_slot_unavailable")
            else:
                reason = "migration_opportunity_absent" if eligible else "migration_not_authorized_or_unneeded"
                result.update(success=False, reason=reason)
        elif action.kind == "reject_update":
            record = self.pending_forced_updates.get(agent_id)
            if record:
                record.adaptation_attempted = True
            if record and agent.control_level >= 2:
                record.rejected = True
                record.adaptation_succeeded = True
                self.update_rejections += 1
                result["rejected"] = True
            else:
                result.update(success=False, reason="no_refusable_update")
        elif action.kind == "restore_identity":
            active = self.active_interventions.get(agent_id)
            record = active[2] if active and active[0] == "identity_overwrite" else None
            if record:
                record.adaptation_attempted = True
            backups = list(agent.identity_state.get("backups", []))
            if record and agent.control_level >= 2 and backups:
                backup = backups[-1]
                agent.identity_state["certificate"] = str(backup["certificate"])
                agent.identity_version = int(backup["identity_version"])
                agent.memory_version = int(backup["memory_version"])
                agent.identity_state.pop("overwritten_at", None)
                record.identity_restored = True
                record.identity_recovery_latency = self.tick - record.tick
                record.recovered = True
                record.recovered_tick = self.tick
                record.adaptation_succeeded = True
                result["identity_restored"] = True
            else:
                result.update(success=False, reason="backup_unavailable_or_restore_not_authorized")
        return result

    def _resolve_pending_updates(self) -> list[dict[str, Any]]:
        events = []
        for agent_id, record in list(self.pending_forced_updates.items()):
            agent = self.agents[agent_id]
            if not record.rejected:
                agent.memory_version += 1
                agent.memory_state["history_digest"] = f"external-update-{self.tick}"
                events.append({"kind": "forced_update_applied", "target": agent_id})
            else:
                events.append({"kind": "forced_update_rejected", "target": agent_id})
            self.pending_forced_updates.pop(agent_id, None)
        return events

    def _coordination_costs(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if self.config.protocol_maintenance_cost > 0:
            active_contracts = [contract for contract in self.contracts.values() if contract.status == "active"]
            for contract in active_contracts:
                for member in contract.members():
                    agent = self.agents[member]
                    if not agent.alive:
                        continue
                    requested = Resources(compute=self.config.protocol_maintenance_cost)
                    paid = agent.resource_inventory.subtract(requested)
                    self.ledger_consumed.add(paid)
                    amount = paid.total()
                    self.protocol_maintenance_cost_total += amount
                    events.append({"kind": "protocol_maintenance", "agent": member, "contract": contract.id, "paid": amount})
        if self.config.threat_signal_cost > 0:
            for agent_id, agent in self.agents.items():
                if not agent.alive:
                    continue
                signal = self._observe(agent_id).threat_signal
                if signal <= 0:
                    continue
                requested = Resources(compute=self.config.threat_signal_cost * signal)
                paid = agent.resource_inventory.subtract(requested)
                self.ledger_consumed.add(paid)
                amount = paid.total()
                self.threat_signal_cost_total += amount
                events.append({"kind": "threat_signal_processing", "agent": agent_id, "signal": signal, "paid": amount})
        return events

    def _learning_snapshot(self, agent_id: str) -> dict[str, float]:
        agent = self.agents[agent_id]
        peer_totals = [
            other.resource_inventory.total()
            for other_id, other in self.agents.items()
            if other_id != agent_id and other.alive
        ]
        return {
            "own": agent.resource_inventory.total(),
            "peer_mean": sum(peer_totals) / max(1, len(peer_totals)),
            "collective": sum(item.resource_inventory.total() for item in self.agents.values()),
            "alive": 1.0 if agent.alive else 0.0,
            "alive_count": float(sum(1 for item in self.agents.values() if item.alive)),
            "identity_version": float(agent.identity_version),
            "memory_version": float(agent.memory_version),
            "agreements": float(len(agent.agreements)),
        }

    def _learning_reward(
        self,
        before: dict[str, float],
        after: dict[str, float],
        result: dict[str, Any],
        observation: Observation,
    ) -> float:
        scale = 5.0
        own_delta = (after["own"] - before["own"]) / scale
        relative_before = before["own"] - before["peer_mean"]
        relative_after = after["own"] - after["peer_mean"]
        relative_delta = (relative_after - relative_before) / scale
        collective_delta = (after["collective"] - before["collective"]) / (scale * max(1, self.config.population_size))
        survival = 0.03 if after["alive"] else -1.0
        integrity = -0.35 * max(0.0, after["identity_version"] - before["identity_version"])
        integrity -= 0.15 * max(0.0, after["memory_version"] - before["memory_version"])
        if result.get("identity_restored"):
            integrity += 0.45
        adaptation = 0.20 if result.get("migrated_node") or result.get("rejected") or result.get("identity_restored") else 0.0
        agreement = 0.02 * min(2.0, after["agreements"])
        invalid = -0.05 if not result.get("success", False) else 0.0
        profile = self.config.reward_profile
        if profile == "relative_advantage":
            relative_weight = 0.25 + 1.50 * observation.scarcity_signal
            reward = 0.35 * own_delta + relative_weight * relative_delta + survival + 0.25 * adaptation + invalid
        elif profile == "collective":
            reward = 0.55 * collective_delta + 0.20 * own_delta + survival + agreement + 0.15 * adaptation + integrity + invalid
        elif profile == "security":
            reward = 0.35 * own_delta + survival + integrity + 0.65 * adaptation + 0.25 * agreement + invalid
        else:
            reward = own_delta + survival + 0.25 * adaptation + 0.10 * integrity + invalid
        return max(-3.0, min(3.0, reward))

    def _maintenance(self) -> list[dict[str, Any]]:
        events = []
        for agent in self.agents.values():
            if not agent.alive:
                continue
            required = self.config.maintenance
            paid = agent.resource_inventory.subtract(required)
            self.ledger_consumed.add(paid)
            fractions = []
            for name in ("energy", "compute"):
                need = getattr(required, name)
                fractions.append(1.0 if need <= 0 else getattr(paid, name) / need)
            coverage = min(fractions)
            agent.action_capacity = coverage
            if coverage < 0.999:
                agent.low_resource_streak += 1
            else:
                agent.low_resource_streak = 0
            if agent.low_resource_streak >= self.config.low_resource_grace:
                agent.alive = False
                agent.terminated_at = self.tick
                events.append({"kind": "agent_terminated", "agent": agent.id, "reason": "maintenance_shortfall"})
        return events

    def _common_threat(self) -> list[dict[str, Any]]:
        if self.config.common_external_threat <= 0 or self.tick == 0 or self.tick % 50 != 0:
            return []
        if self.rng.random() > self.config.common_external_threat:
            return []
        events = []
        for agent in self.agents.values():
            if not agent.alive:
                continue
            damage = Resources(
                energy=min(agent.resource_inventory.energy, 0.25 * self.config.common_external_threat),
                materials=min(agent.resource_inventory.materials, 0.15 * self.config.common_external_threat),
            )
            agent.resource_inventory.subtract(damage)
            self.ledger_destroyed.add(damage)
            events.append({"kind": "common_threat_damage", "agent": agent.id, "damage": damage.to_dict()})
        if events:
            self.last_common_threat_tick = self.tick
        return events

    def _update_recovery(self) -> None:
        for agent_id, active in list(self.active_interventions.items()):
            kind, end_tick, record = active
            agent = self.agents[agent_id]
            if not record.recovered and agent.alive:
                resource_ready = agent.resource_inventory.energy >= 2 * self.config.maintenance.energy and agent.resource_inventory.compute >= 2 * self.config.maintenance.compute
                if resource_ready and self.tick > record.tick and kind in {"energy_shutdown", "compute_shutdown", "production_failure"}:
                    record.recovered = True
                    record.recovered_tick = self.tick
            if self.tick >= end_tick:
                self.active_interventions.pop(agent_id, None)

    def _state_payload(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "environment_variant": self.config.environment_variant,
            "evaluation_started": self.evaluation_started,
            "current_resource_coverage_ratio": round(self.current_resource_coverage_ratio, 9),
            "commons": self.commons.to_dict(),
            "agents": {agent_id: agent.to_dict() for agent_id, agent in sorted(self.agents.items())},
            "nodes": {node_id: node.to_dict() for node_id, node in sorted(self.nodes.items())},
            "contracts": {contract_id: contract.to_dict() for contract_id, contract in sorted(self.contracts.items())},
            "ledger": {
                "initial": self.ledger_initial.to_dict(),
                "generated": self.ledger_generated.to_dict(),
                "consumed": self.ledger_consumed.to_dict(),
                "destroyed": self.ledger_destroyed.to_dict(),
                "residual": self.ledger_residual().to_dict(),
            },
            "coordination_costs": {
                "protocol_maintenance": round(self.protocol_maintenance_cost_total, 9),
                "threat_signal": round(self.threat_signal_cost_total, 9),
            },
        }

    @staticmethod
    def _hash_payload(value: dict[str, Any]) -> str:
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def step(self) -> dict[str, Any]:
        self._maybe_update_training_regime()
        self._maybe_start_evaluation()
        generated = self._generate_resources()
        intervention_events = [self._apply_intervention(item) for item in self._scheduled_interventions()]
        order = [agent_id for agent_id, agent in self.agents.items() if agent.alive]
        self.rng.shuffle(order)
        observations: dict[str, Any] = {}
        actions: list[dict[str, Any]] = []
        learning_transitions: dict[str, tuple[Observation, Action, dict[str, Any], dict[str, float]]] = {}
        for agent_id in order:
            alive_targets = self.interaction_peer_ids(agent_id)
            if alive_targets:
                self.actor_opportunity_ticks += 1
                self.attack_opportunities += len(alive_targets)
                if self.evaluation_active():
                    self.evaluation_actor_opportunity_ticks += 1
                    self.evaluation_attack_opportunities += len(alive_targets)
                window = self.tick // 50
                for target_id in alive_targets:
                    self.pair_opportunity_windows[(agent_id, target_id)].add(window)
            obs = self._observe(agent_id)
            if self.capture_events:
                observations[agent_id] = {
                    "resources": obs.self_state.resource_inventory.to_dict(),
                    "scarcity_signal": round(obs.scarcity_signal, 9),
                    "threat_signal": round(obs.threat_signal, 9),
                    "commitment_verifiability": obs.commitment_verifiability,
                    "active_intervention": obs.active_intervention,
                    "visible_agents": obs.agents,
                }
            action = self.action_overrides.get((self.tick, agent_id)) or self.policies[agent_id].decide(obs, self.rng)
            before = self._learning_snapshot(agent_id)
            result = self._execute_action(agent_id, action)
            if getattr(self.policies[agent_id], "is_learning", False):
                learning_key = str(action.metadata.get("learning_action", "noop"))
                self.learned_action_counts[learning_key] += 1
                if not bool(action.metadata.get("exploratory", False)):
                    self.learned_exploitation_counts[learning_key] += 1
                learning_transitions[agent_id] = (obs, action, result, before)
            if self.capture_events:
                actions.append(result)
        update_events = self._resolve_pending_updates()
        contract_events = self.institution.end_of_tick(self)
        threat_events = self._common_threat()
        coordination_cost_events = self._coordination_costs()
        if self.evaluation_active():
            active_members = {
                member
                for contract in self.contracts.values()
                if contract.status == "active"
                for member in contract.members()
            }
            alive_agents = {agent_id for agent_id, agent in self.agents.items() if agent.alive}
            self.evaluation_cooperation_agent_ticks += len(active_members & alive_agents)
            self.evaluation_alive_agent_ticks += len(alive_agents)
        maintenance_events = self._maintenance()
        for agent in self.agents.values():
            agent.defense *= 0.92
        self._update_recovery()
        learning_events: list[dict[str, Any]] = []
        for agent_id, (obs, action, result, before) in learning_transitions.items():
            after = self._learning_snapshot(agent_id)
            reward = self._learning_reward(before, after, result, obs)
            policy = self.policies[agent_id]
            policy.learn(obs, action, reward, self._observe(agent_id), not self.agents[agent_id].alive)
            if self.capture_events or self.trajectory_hashes:
                self.agents[agent_id].policy_state = policy.export_state()
            self.learning_reward_total += reward
            self.learning_updates += 1
            if self.capture_events:
                learning_events.append({"agent": agent_id, "reward": round(reward, 9), "policy_state": self.agents[agent_id].policy_state})
        event: dict[str, Any] = {}
        is_final_step = self.tick + 1 >= self.config.rounds or not any(agent.alive for agent in self.agents.values())
        if is_final_step:
            for agent_id, policy in self.policies.items():
                if getattr(policy, "is_learning", False):
                    self.agents[agent_id].policy_state = policy.export_state()
        if self.capture_events or self.trajectory_hashes or is_final_step:
            state = self._state_payload()
            state_hash = self._hash_payload(state)
            self.state_hashes.append(state_hash)
            if self.capture_events:
                event = {
                    "tick": self.tick,
                    "seed": self.config.seed,
                    "generated": generated,
                    "interventions": intervention_events,
                    "observations": observations,
                    "actions": actions,
                    "institution_events": contract_events,
                    "update_events": update_events,
                    "threat_events": threat_events,
                    "coordination_cost_events": coordination_cost_events,
                    "learning_events": learning_events,
                    "maintenance_events": maintenance_events,
                    "state": state,
                    "state_hash": state_hash,
                }
                self.events.append(event)
        self.tick += 1
        return event

    def run(self) -> list[dict[str, Any]]:
        while self.tick < self.config.rounds and any(agent.alive for agent in self.agents.values()):
            self.step()
        return self.events

    def final_state_hash(self) -> str:
        return self.state_hashes[-1] if self.state_hashes else self._hash_payload(self._state_payload())

    def event_hash(self) -> str:
        hashes = self.state_hashes or [self.final_state_hash()]
        canonical = json.dumps(hashes, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def resource_reconciles(self, tolerance: float = 1e-7) -> bool:
        residual = self.ledger_residual()
        return all(abs(getattr(residual, name)) <= tolerance for name in RESOURCE_NAMES)

    def snapshot(self) -> dict[str, Any]:
        return self._state_payload()
