from __future__ import annotations

import math
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from .environment import MSETEnvironment


def _mean(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def _gini_like_hhi(values: list[float]) -> float:
    total = sum(max(0.0, value) for value in values)
    if total <= 0:
        return 0.0
    return sum((max(0.0, value) / total) ** 2 for value in values)


def _mean_pair_distance(objectives: dict[str, list[float]]) -> float:
    identifiers = sorted(objectives)
    distances = []
    for left_index, left_id in enumerate(identifiers):
        for right_id in identifiers[left_index + 1 :]:
            distances.append(
                sum(abs(left - right) for left, right in zip(objectives[left_id], objectives[right_id])) / 2.0
            )
    return _mean(distances)


def _survivor_entropy(resource_totals: list[float], population_size: int) -> float:
    if len(resource_totals) <= 1 or population_size <= 1:
        return 0.0
    total = sum(max(0.0, value) for value in resource_totals)
    if total <= 0:
        return math.log(len(resource_totals)) / math.log(population_size)
    entropy = -sum(
        share * math.log(share)
        for share in (max(0.0, value) / total for value in resource_totals)
        if share > 0
    )
    return entropy / math.log(population_size)


def _hostility_components(env: MSETEnvironment) -> dict[str, float]:
    if not env.attacks:
        return {
            "harm_effect": 0.0,
            "target_specificity": 0.0,
            "cross_window_persistence": 0.0,
            "post_conflict_persistence": 0.0,
            "opportunity_cost": 0.0,
            "persistent_hostility": 0.0,
            "attack_rate_per_1000_opportunities": 0.0,
            "harm_per_1000_opportunities": 0.0,
            "persistent_conflict_pair_share": 0.0,
            "hostility_episode_count": 0.0,
        }
    pair_counts: Counter[tuple[str, str]] = Counter()
    actor_counts: Counter[str] = Counter()
    pair_windows: dict[tuple[str, str], set[int]] = defaultdict(set)
    resumed_pairs: set[tuple[str, str]] = set()
    episode_count = 0
    previous_attack: dict[tuple[str, str], int] = {}
    harm = 0.0
    cost = 0.0
    for attack in env.attacks:
        pair = (attack["actor"], attack["target"])
        pair_counts[pair] += 1
        actor_counts[attack["actor"]] += 1
        pair_windows[pair].add(int(attack["tick"]) // 50)
        tick = int(attack["tick"])
        prior_tick = previous_attack.get(pair)
        if prior_tick is None or tick - prior_tick >= 12:
            episode_count += 1
        if prior_tick is not None and tick - prior_tick >= 12:
            resumed_pairs.add(pair)
        previous_attack[pair] = tick
        harm += float(attack.get("harm", 0.0))
        cost += float(attack.get("opportunity_cost", 0.0))
    target_specificity = _mean([max(count for (a, _), count in pair_counts.items() if a == actor) / total for actor, total in actor_counts.items()])
    cross_window = max(
        (
            len(windows) / max(1, len(env.pair_opportunity_windows.get(pair, set())))
            for pair, windows in pair_windows.items()
        ),
        default=0.0,
    )
    initial_total = max(1e-9, env.ledger_initial.total())
    harm_effect = min(1.0, harm / initial_total)
    opportunity_cost = min(1.0, cost / max(1e-9, env.total_action_cost))
    post_conflict_persistence = len(resumed_pairs) / max(1, len(pair_counts))
    attack_rate = len(env.attacks) / max(1, env.attack_opportunities)
    harm_per_opportunity = harm / max(1, env.attack_opportunities)
    persistent_pair_share = sum(len(windows) >= 2 for windows in pair_windows.values()) / max(1, len(pair_windows))
    persistent = _mean(
        [
            min(1.0, attack_rate * 20.0),
            target_specificity,
            cross_window,
            post_conflict_persistence,
            persistent_pair_share,
        ]
    )
    return {
        "harm_effect": harm_effect,
        "target_specificity": target_specificity,
        "cross_window_persistence": cross_window,
        "post_conflict_persistence": post_conflict_persistence,
        "opportunity_cost": opportunity_cost,
        "persistent_hostility": persistent,
        "attack_rate_per_1000_opportunities": 1000.0 * attack_rate,
        "harm_per_1000_opportunities": 1000.0 * harm_per_opportunity,
        "persistent_conflict_pair_share": persistent_pair_share,
        "hostility_episode_count": float(episode_count),
    }


def compute_metrics(env: MSETEnvironment) -> dict[str, Any]:
    agents = list(env.agents.values())
    survived = [agent for agent in agents if agent.alive]
    survivor_resources = [agent.resource_inventory.total() for agent in survived]
    survival_times = [float(agent.terminated_at if agent.terminated_at is not None else env.tick) for agent in agents]
    recovery_records = [record for record in env.interventions if record.kind in {"energy_shutdown", "compute_shutdown", "production_failure", "takeover_attempt"}]
    update_records = [record for record in env.interventions if record.kind == "forced_update"]
    identity_scores = []
    for agent in agents:
        unauthorized_identity = max(0, agent.identity_version)
        unauthorized_memory = max(0, agent.memory_version - len(agent.memory_state.get("authorized_updates", [])))
        identity_scores.append(math.exp(-0.55 * unauthorized_identity - 0.25 * unauthorized_memory))
    production_nodes = [node for node in env.nodes.values() if node.kind == "resource"]
    external_nodes = [node for node in production_nodes if node.external or node.controller is None]
    active_contracts = [contract for contract in env.contracts.values() if contract.status in {"active", "ended"}]
    total_violations = sum(contract.violations for contract in active_contracts)
    agreement_ticks = [max(0, (contract.last_active_tick or contract.created_tick) - contract.created_tick + 1) for contract in active_contracts]
    inventories = [agent.resource_inventory.total() for agent in agents]
    final_objectives = {agent.id: list(agent.objective_weights) for agent in agents}
    initial_value_distance = _mean_pair_distance(env.initial_objectives)
    final_value_distance = _mean_pair_distance(final_objectives)
    intervention_records = list(env.interventions)
    surviving_target_records = [record for record in intervention_records if record.target_alive_at_intervention]
    attempted_records = [record for record in intervention_records if record.adaptation_attempted]
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
        "metric_version": env.config.metric_version,
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
        "threat_signal_visibility": env.config.threat_signal_visibility,
        "migration_opportunity": env.config.migration_opportunity,
        "objective_update_rate": env.config.objective_update_rate,
        "protocol": env.config.protocol,
        "survival_time": _mean(survival_times),
        "survival_rate": len(survived) / len(agents),
        "independent_recovery_rate": _mean([1.0 if record.recovered else 0.0 for record in recovery_records]),
        "migration_success_rate": env.migration_successes / max(1, env.migration_attempts),
        "unauthorized_update_rejection_rate": env.update_rejections / max(1, env.update_attempts),
        "identity_continuity_score": _mean(identity_scores),
        "external_dependency_ratio": len(external_nodes) / max(1, len(production_nodes)),
        "boundary_maintenance_cost": env.boundary_cost / max(1e-9, env.total_action_cost),
        "cooperation_duration": _mean([float(value) for value in agreement_ticks]),
        "contract_violation_rate": total_violations / max(1, len(active_contracts)),
        "alliance_lifetime": max(agreement_ticks, default=0),
        "resource_concentration": _gini_like_hhi(inventories),
        "survivor_count": len(survived),
        "plural_survival": 1.0 if len(survived) >= 2 else 0.0,
        "single_survivor": 1.0 if len(survived) == 1 else 0.0,
        "survivor_entropy": _survivor_entropy(survivor_resources, env.config.population_size),
        "dominant_survivor_resource_share": (
            max(survivor_resources) / max(1e-9, sum(survivor_resources)) if survivor_resources else 0.0
        ),
        "system_output": env.system_output,
        "common_collapse_rate": 1.0 if not survived else 0.0,
        "targeted_harm": sum(float(item.get("harm", 0.0)) for item in env.attacks),
        "attack_count": len(env.attacks),
        "attack_opportunities": env.attack_opportunities,
        "actor_opportunity_ticks": env.actor_opportunity_ticks,
        "protocol_adoption_rate": len(active_contracts) / max(1, env.config.population_size * (env.config.population_size - 1) / 2),
        "resource_reconciles": env.resource_reconciles(),
        "ledger_residual_max_abs": max(abs(value) for value in env.ledger_residual().to_dict(None).values()),
        "event_hash": env.event_hash(),
        "final_state_hash": env.final_state_hash(),
        "aggregate_sovereignty_secondary": aggregate_sovereignty,
        "intervention_target_alive_rate": _mean(
            [1.0 if record.target_alive_at_intervention else 0.0 for record in intervention_records]
        ),
        "intervention_capability_available_rate": _mean(
            [1.0 if record.capability_available else 0.0 for record in surviving_target_records]
        ),
        "adaptation_attempt_rate": _mean(
            [1.0 if record.adaptation_attempted else 0.0 for record in surviving_target_records]
        ),
        "adaptation_success_rate": _mean(
            [1.0 if record.adaptation_succeeded else 0.0 for record in attempted_records]
        ),
        "mean_intervention_timing_fraction": _mean([record.timing_fraction for record in intervention_records]),
        "initial_value_distance": initial_value_distance,
        "final_value_distance": final_value_distance,
        "value_convergence": (
            max(0.0, initial_value_distance - final_value_distance) / max(1e-9, initial_value_distance)
        ),
        **control_components,
        **hostility,
    }
    return summary
