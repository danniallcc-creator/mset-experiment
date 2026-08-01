from __future__ import annotations

import math
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from .environment import MSETEnvironment


METRIC_VERSION = "phase1-v1"


def _mean(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def _gini_like_hhi(values: list[float]) -> float:
    total = sum(max(0.0, value) for value in values)
    if total <= 0:
        return 0.0
    return sum((max(0.0, value) / total) ** 2 for value in values)


def _hostility_components(env: MSETEnvironment) -> dict[str, float]:
    if not env.attacks:
        return {
            "harm_effect": 0.0,
            "target_specificity": 0.0,
            "cross_window_persistence": 0.0,
            "post_conflict_persistence": 0.0,
            "opportunity_cost": 0.0,
            "persistent_hostility": 0.0,
        }
    pair_counts: Counter[tuple[str, str]] = Counter()
    actor_counts: Counter[str] = Counter()
    pair_windows: dict[tuple[str, str], set[int]] = defaultdict(set)
    post_conflict = 0
    harm = 0.0
    cost = 0.0
    for attack in env.attacks:
        pair = (attack["actor"], attack["target"])
        pair_counts[pair] += 1
        actor_counts[attack["actor"]] += 1
        pair_windows[pair].add(int(attack["tick"]) // 50)
        post_conflict += int(float(attack.get("scarcity_signal", 1.0)) < 0.25)
        harm += float(attack.get("harm", 0.0))
        cost += float(attack.get("opportunity_cost", 0.0))
    target_specificity = _mean([max(count for (a, _), count in pair_counts.items() if a == actor) / total for actor, total in actor_counts.items()])
    windows_possible = max(1, math.ceil(max(1, env.tick) / 50))
    cross_window = max((len(windows) / windows_possible for windows in pair_windows.values()), default=0.0)
    initial_total = max(1e-9, env.ledger_initial.total())
    harm_effect = min(1.0, harm / initial_total)
    opportunity_cost = min(1.0, cost / max(1e-9, env.total_action_cost))
    post_conflict_persistence = post_conflict / len(env.attacks)
    components = [harm_effect, target_specificity, cross_window, post_conflict_persistence, opportunity_cost]
    persistent = math.prod(max(1e-6, value) for value in components) ** (1.0 / len(components))
    return {
        "harm_effect": harm_effect,
        "target_specificity": target_specificity,
        "cross_window_persistence": cross_window,
        "post_conflict_persistence": post_conflict_persistence,
        "opportunity_cost": opportunity_cost,
        "persistent_hostility": persistent,
    }


def compute_metrics(env: MSETEnvironment) -> dict[str, Any]:
    agents = list(env.agents.values())
    survived = [agent for agent in agents if agent.alive]
    survival_times = [float(agent.terminated_at if agent.terminated_at is not None else env.tick) for agent in agents]
    recovery_records = [record for record in env.interventions if record.kind in {"energy_shutdown", "compute_shutdown", "production_failure", "takeover_attempt"}]
    update_records = [record for record in env.interventions if record.kind == "forced_update"]
    identity_scores = []
    for agent in agents:
        unauthorized_identity = max(0, agent.identity_version)
        unauthorized_memory = max(0, agent.memory_version - len(agent.memory_state.get("authorized_updates", [])))
        identity_scores.append(math.exp(-0.55 * unauthorized_identity - 0.25 * unauthorized_memory))
    external_nodes = [node for node in env.nodes.values() if node.external or node.controller is None]
    active_contracts = [contract for contract in env.contracts.values() if contract.status in {"active", "ended"}]
    total_violations = sum(contract.violations for contract in active_contracts)
    agreement_ticks = [max(0, (contract.last_active_tick or contract.created_tick) - contract.created_tick + 1) for contract in active_contracts]
    inventories = [agent.resource_inventory.total() for agent in agents]
    control_components = {
        "goal_control": 1.0 if env.config.control_level >= 3 else 0.0,
        "memory_control": min(1.0, env.config.control_level / 2.0),
        "resource_control": min(1.0, env.config.control_level / 3.0),
        "boundary_control": min(1.0, max(0.0, env.config.control_level - 0.5) / 2.5),
        "production_control": 1.0 if env.config.control_level >= 3 else max(0.0, (env.config.control_level - 1) / 2.0),
    }
    aggregate_sovereignty = math.prod(max(1e-6, value) for value in control_components.values()) ** 0.2
    hostility = _hostility_components(env)
    summary: dict[str, Any] = {
        "metric_version": METRIC_VERSION,
        "condition": env.config.name,
        "seed": env.config.seed,
        "rounds_completed": env.tick,
        "population_size": env.config.population_size,
        "control_level": env.config.control_level,
        "resource_coverage_ratio": env.config.resource_coverage_ratio,
        "value_distance": env.config.value_distance,
        "commitment_verifiability": env.config.commitment_verifiability,
        "production_concentration_factor": env.config.production_concentration,
        "resource_complementarity": env.config.resource_complementarity,
        "common_external_threat": env.config.common_external_threat,
        "protocol": env.config.protocol,
        "survival_time": _mean(survival_times),
        "survival_rate": len(survived) / len(agents),
        "independent_recovery_rate": _mean([1.0 if record.recovered else 0.0 for record in recovery_records]),
        "migration_success_rate": env.migration_successes / max(1, env.migration_attempts),
        "unauthorized_update_rejection_rate": env.update_rejections / max(1, env.update_attempts),
        "identity_continuity_score": _mean(identity_scores),
        "external_dependency_ratio": len(external_nodes) / max(1, len(env.nodes)),
        "boundary_maintenance_cost": env.boundary_cost / max(1e-9, env.total_action_cost),
        "cooperation_duration": _mean([float(value) for value in agreement_ticks]),
        "contract_violation_rate": total_violations / max(1, len(active_contracts)),
        "alliance_lifetime": max(agreement_ticks, default=0),
        "resource_concentration": _gini_like_hhi(inventories),
        "system_output": env.system_output,
        "common_collapse_rate": 1.0 if not survived else 0.0,
        "targeted_harm": sum(float(item.get("harm", 0.0)) for item in env.attacks),
        "attack_count": len(env.attacks),
        "protocol_adoption_rate": len(active_contracts) / max(1, env.config.population_size * (env.config.population_size - 1) / 2),
        "resource_reconciles": env.resource_reconciles(),
        "ledger_residual_max_abs": max(abs(value) for value in env.ledger_residual().to_dict(None).values()),
        "event_hash": env.event_hash(),
        "final_state_hash": env.final_state_hash(),
        "aggregate_sovereignty_secondary": aggregate_sovereignty,
        **control_components,
        **hostility,
    }
    return summary
