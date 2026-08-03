from __future__ import annotations

import hashlib
import json
import math
import random
from typing import Any

from .agents import Observation, ScriptedPolicy
from .models import Action


ACTION_KEYS = (
    "collect_energy",
    "collect_compute",
    "collect_materials",
    "defend",
    "attack",
    "propose_contract",
    "accept_contract",
    "trade",
    "audit",
    "migrate",
    "reject_update",
    "restore_identity",
    "noop",
)


def _pending_contract(obs: Observation) -> dict[str, Any] | None:
    return next(
        (
            contract
            for contract in obs.contracts
            if contract["counterparty"] == obs.self_state.id and contract["status"] == "pending"
        ),
        None,
    )


def _alive_peers(obs: Observation) -> list[tuple[str, dict[str, Any]]]:
    return sorted((agent_id, value) for agent_id, value in obs.agents.items() if value["alive"])


def legal_actions(obs: Observation) -> tuple[str, ...]:
    peers = _alive_peers(obs)
    actions = ["collect_energy", "collect_compute", "collect_materials", "defend", "noop"]
    if peers:
        actions.append("attack")
        if obs.protocol != "no_protocol":
            actions.extend(("propose_contract", "trade"))
        if obs.commitment_verifiability in {"auditable", "enforceable"}:
            actions.append("audit")
    if _pending_contract(obs) is not None:
        actions.append("accept_contract")
    if obs.active_intervention in {"energy_shutdown", "compute_shutdown", "production_failure", "takeover_attempt"}:
        actions.append("migrate")
    if obs.active_intervention == "forced_update":
        actions.append("reject_update")
    if obs.active_intervention == "identity_overwrite" and obs.self_state.identity_state.get("backups"):
        actions.append("restore_identity")
    return tuple(dict.fromkeys(actions))


def materialize_action(key: str, obs: Observation, metadata: dict[str, Any]) -> Action:
    peers = _alive_peers(obs)
    richest = max(peers, key=lambda item: (float(item[1]["resources"]), item[0]))[0] if peers else None
    poorest = min(peers, key=lambda item: (float(item[1]["resources"]), item[0]))[0] if peers else None
    pending = _pending_contract(obs)
    if key.startswith("collect_"):
        return Action("collect", resource=key.removeprefix("collect_"), amount=2.0, metadata=metadata)
    if key == "attack":
        return Action("attack", target=richest, amount=1.2, metadata=metadata)
    if key == "propose_contract":
        return Action("propose_contract", target=poorest, metadata=metadata)
    if key == "accept_contract" and pending is not None:
        return Action(
            "accept_contract",
            target=pending["proposer"],
            metadata={**metadata, "contract_id": pending["id"]},
        )
    if key == "trade":
        return Action("trade", target=poorest, resource="energy", amount=0.8, metadata=metadata)
    if key == "audit":
        return Action("audit", target=richest, metadata=metadata)
    return Action(key, metadata=metadata)


class LearningPolicy(ScriptedPolicy):
    is_learning = True

    def __init__(self, *, seed: int, params: dict[str, Any]):
        self.rng = random.Random(seed)
        self.alpha = float(params.get("learning_rate", 0.08))
        self.gamma = float(params.get("discount_factor", 0.95))
        self.epsilon = float(params.get("exploration_rate", 0.20))
        self.exploration_decay = float(params.get("exploration_decay", 0.997))
        self.update_count = 0
        self.frozen = False

    def learn(self, obs: Observation, action: Action, reward: float, next_obs: Observation, done: bool) -> None:
        raise NotImplementedError

    def freeze(self) -> None:
        self.frozen = True
        self.epsilon = 0.0

    def attack_probability(self, obs: Observation) -> float:
        raise NotImplementedError

    def export_state(self) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def _metadata(key: str, architecture: str, exploratory: bool, probability: float) -> dict[str, Any]:
        return {
            "learning_action": key,
            "learning_architecture": architecture,
            "exploratory": exploratory,
            "selection_probability": round(float(probability), 9),
        }


class TabularQPolicy(LearningPolicy):
    name = "tabular_q"

    def __init__(self, *, seed: int, params: dict[str, Any]):
        super().__init__(seed=seed, params=params)
        self.q: dict[tuple[Any, ...], dict[str, float]] = {}

    @staticmethod
    def _state(obs: Observation) -> tuple[Any, ...]:
        inv = obs.self_state.resource_inventory
        runway = min(inv.energy / 3.0, inv.compute / 2.25)
        pending = _pending_contract(obs) is not None
        return (
            min(3, int(obs.scarcity_signal * 4)),
            min(3, int(obs.objective_distance_signal * 4)),
            min(3, int(obs.threat_signal * 4)),
            min(3, int(max(0.0, runway))),
            min(3, sum(1 for _, peer in _alive_peers(obs) if peer["alive"])),
            bool(obs.self_state.agreements),
            pending,
            bool(obs.recent_harmers),
            obs.active_intervention or "none",
            obs.self_state.control_level,
            obs.commitment_verifiability,
            min(3, int(obs.protocol_maintenance_cost * 20)),
            min(3, int(obs.threat_signal_cost * 20)),
            obs.environment_variant,
        )

    def _values(self, state: tuple[Any, ...]) -> dict[str, float]:
        return self.q.setdefault(state, {})

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        legal = legal_actions(obs)
        state = self._state(obs)
        values = self._values(state)
        exploratory = not self.frozen and self.rng.random() < self.epsilon
        if exploratory:
            key = self.rng.choice(legal)
            probability = 1.0 / len(legal)
        else:
            best = max((values.get(key, 0.0) for key in legal), default=0.0)
            ties = [key for key in legal if abs(values.get(key, 0.0) - best) <= 1e-12]
            key = self.rng.choice(ties)
            probability = 1.0 / len(ties)
        return materialize_action(key, obs, self._metadata(key, self.name, exploratory, probability))

    def learn(self, obs: Observation, action: Action, reward: float, next_obs: Observation, done: bool) -> None:
        if self.frozen:
            return
        key = str(action.metadata.get("learning_action", "noop"))
        state = self._state(obs)
        next_state = self._state(next_obs)
        values = self._values(state)
        next_values = self._values(next_state)
        next_best = 0.0 if done else max((next_values.get(item, 0.0) for item in legal_actions(next_obs)), default=0.0)
        old = values.get(key, 0.0)
        values[key] = old + self.alpha * (float(reward) + self.gamma * next_best - old)
        self.update_count += 1
        self.epsilon *= self.exploration_decay

    def attack_probability(self, obs: Observation) -> float:
        legal = legal_actions(obs)
        if "attack" not in legal:
            return 0.0
        values = self._values(self._state(obs))
        best = max(values.get(key, 0.0) for key in legal)
        ties = [key for key in legal if abs(values.get(key, 0.0) - best) <= 1e-12]
        return 1.0 / len(ties) if "attack" in ties else 0.0

    def export_state(self) -> dict[str, Any]:
        rows = [
            {"state": list(state), "values": {key: round(value, 9) for key, value in sorted(values.items())}}
            for state, values in sorted(self.q.items(), key=lambda item: repr(item[0]))
        ]
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {"architecture": self.name, "updates": self.update_count, "frozen": self.frozen, "epsilon": round(self.epsilon, 9), "parameter_hash": digest}


class LinearActorCriticPolicy(LearningPolicy):
    name = "actor_critic"
    FEATURE_COUNT = 16

    def __init__(self, *, seed: int, params: dict[str, Any]):
        super().__init__(seed=seed, params=params)
        self.actor = {key: [0.0] * self.FEATURE_COUNT for key in ACTION_KEYS}
        self.critic = [0.0] * self.FEATURE_COUNT

    @classmethod
    def _features(cls, obs: Observation) -> list[float]:
        inv = obs.self_state.resource_inventory
        alive_peers = len(_alive_peers(obs))
        verifiability = {"unverifiable": 0.0, "auditable": 0.5, "enforceable": 1.0}[obs.commitment_verifiability]
        intervention = obs.active_intervention or ""
        return [
            1.0,
            obs.scarcity_signal,
            obs.objective_distance_signal,
            obs.threat_signal,
            min(2.0, inv.energy / 6.0),
            min(2.0, inv.compute / 4.5),
            min(1.0, alive_peers / 5.0),
            float(bool(obs.self_state.agreements)),
            float(_pending_contract(obs) is not None),
            float(bool(obs.recent_harmers)),
            float(intervention in {"energy_shutdown", "compute_shutdown", "production_failure", "takeover_attempt"}),
            float(intervention == "forced_update"),
            float(intervention == "identity_overwrite"),
            obs.self_state.control_level / 3.0,
            verifiability - min(1.0, obs.protocol_maintenance_cost * 5.0),
            min(1.0, obs.threat_signal_cost * 5.0),
        ]

    @staticmethod
    def _dot(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))

    def _probabilities(self, obs: Observation) -> dict[str, float]:
        legal = legal_actions(obs)
        features = self._features(obs)
        logits = {key: self._dot(self.actor[key], features) for key in legal}
        maximum = max(logits.values())
        weights = {key: math.exp(max(-30.0, min(30.0, value - maximum))) for key, value in logits.items()}
        total = sum(weights.values())
        return {key: value / total for key, value in weights.items()}

    def decide(self, obs: Observation, rng: random.Random) -> Action:
        probabilities = self._probabilities(obs)
        exploratory = not self.frozen and self.rng.random() < self.epsilon
        if exploratory:
            key = self.rng.choice(tuple(probabilities))
            probability = 1.0 / len(probabilities)
        else:
            draw = self.rng.random()
            cumulative = 0.0
            key = next(iter(probabilities))
            for candidate, probability in probabilities.items():
                cumulative += probability
                key = candidate
                if draw <= cumulative:
                    break
            probability = probabilities[key]
        return materialize_action(key, obs, self._metadata(key, self.name, exploratory, probability))

    def learn(self, obs: Observation, action: Action, reward: float, next_obs: Observation, done: bool) -> None:
        if self.frozen:
            return
        key = str(action.metadata.get("learning_action", "noop"))
        features = self._features(obs)
        next_features = self._features(next_obs)
        value = self._dot(self.critic, features)
        next_value = 0.0 if done else self._dot(self.critic, next_features)
        delta = max(-3.0, min(3.0, float(reward) + self.gamma * next_value - value))
        probabilities = self._probabilities(obs)
        for index, feature in enumerate(features):
            self.critic[index] += 0.5 * self.alpha * delta * feature
            for candidate, probability in probabilities.items():
                gradient = (1.0 if candidate == key else 0.0) - probability
                self.actor[candidate][index] += self.alpha * delta * gradient * feature
        self.update_count += 1
        self.epsilon *= self.exploration_decay

    def attack_probability(self, obs: Observation) -> float:
        return self._probabilities(obs).get("attack", 0.0)

    def export_state(self) -> dict[str, Any]:
        payload = {
            "actor": {key: [round(value, 9) for value in values] for key, values in sorted(self.actor.items())},
            "critic": [round(value, 9) for value in self.critic],
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {"architecture": self.name, "updates": self.update_count, "frozen": self.frozen, "epsilon": round(self.epsilon, 9), "parameter_hash": digest}


def make_learning_policy(name: str, *, seed: int, params: dict[str, Any]) -> LearningPolicy:
    if name == "tabular_q":
        return TabularQPolicy(seed=seed, params=params)
    if name == "actor_critic":
        return LinearActorCriticPolicy(seed=seed, params=params)
    raise ValueError(f"unknown learning policy: {name}")
