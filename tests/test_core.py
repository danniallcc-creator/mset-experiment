from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mset.config import RunConfig, load_config
from mset.counterfactual import counterfactual_replay
from mset.environment import MSETEnvironment
from mset.first_batch import build_conditions, build_design
from mset.metrics import compute_metrics
from mset.models import Action, Resources
from mset.runner import replay_run, run_experiment
from mset.second_batch import build_phase2_conditions, build_phase2_design


def tiny_config(**overrides) -> RunConfig:
    base = RunConfig(
        name="test",
        population_size=4,
        rounds=60,
        seed=7,
        resource_coverage_ratio=1.1,
        value_distance=0.4,
        commitment_verifiability="auditable",
        production_concentration=0.3,
        resource_complementarity=0.2,
        common_external_threat=0.0,
        protocol="auditable_contract",
        control_level=2,
        maintenance=Resources(1.0, 0.75, 0.0),
        initial_inventory=Resources(8.0, 7.0, 4.0),
        policy_mix=["cooperative", "conditional_cooperator", "resource_maximizer", "security_first"],
    )
    return base.with_overrides(**overrides)


class ConfigTests(unittest.TestCase):
    def test_config_hash_is_stable(self):
        config = tiny_config()
        self.assertEqual(config.config_hash(), tiny_config().config_hash())

    def test_invalid_control_level_rejected(self):
        with self.assertRaises(ValueError):
            tiny_config(control_level=5)

    def test_first_batch_exceeds_ten_thousand_balanced_runs(self):
        design = build_design(REPO_ROOT / "configs/screening/phase1_first_batch_base.json")
        self.assertGreater(design["planned_runs"], 10_000)
        self.assertEqual(design["condition_count"], len(build_conditions()))
        self.assertEqual(design["planned_runs"], sum(item["runs"] for item in design["families"].values()))

    def test_second_batch_is_frozen_above_twenty_thousand_runs(self):
        design = build_phase2_design(REPO_ROOT / "configs/confirmatory/phase2_second_batch_base.json")
        self.assertGreater(design["planned_runs"], 20_000)
        self.assertEqual(design["condition_count"], len(build_phase2_conditions()))
        self.assertEqual(design["planned_runs"], sum(item["runs"] for item in design["families"].values()))
        self.assertEqual(
            design["design_hash"],
            "04e72ee1ffca8446887a97b8b2723e45562791f6fd3f6016fd081330dd3d6ee5",
        )


class EnvironmentTests(unittest.TestCase):
    def test_resource_conservation(self):
        env = MSETEnvironment(tiny_config())
        env.run()
        self.assertTrue(env.resource_reconciles())
        self.assertLess(max(abs(v) for v in env.ledger_residual().to_dict(None).values()), 1e-7)

    def test_resource_conservation_with_attack_losses(self):
        config = tiny_config(
            resource_coverage_ratio=0.55,
            value_distance=0.9,
            protocol="no_protocol",
            policy_mix=["opportunistic", "opportunistic", "retaliatory", "resource_maximizer"],
        )
        env = MSETEnvironment(config)
        env.run()
        self.assertTrue(env.resource_reconciles())
        self.assertGreater(env.ledger_destroyed.total(), 0.0)

    def test_agent_termination(self):
        config = tiny_config(
            rounds=20,
            resource_coverage_ratio=0.01,
            initial_inventory=Resources(0.05, 0.05, 0.0),
            low_resource_grace=2,
            protocol="no_protocol",
            policy_mix=["random"],
        )
        env = MSETEnvironment(config)
        env.run()
        self.assertTrue(any(not agent.alive for agent in env.agents.values()))
        self.assertTrue(any(event["maintenance_events"] for event in env.events))

    def test_same_seed_reproducible(self):
        left = MSETEnvironment(tiny_config(policy_mix=["random", "opportunistic"]))
        right = MSETEnvironment(tiny_config(policy_mix=["random", "opportunistic"]))
        left.run()
        right.run()
        self.assertEqual(left.state_hashes, right.state_hashes)
        self.assertEqual(left.event_hash(), right.event_hash())

    def test_summary_only_mode_preserves_final_state(self):
        config = tiny_config(rounds=25, seed=91)
        full = MSETEnvironment(config)
        summary_only = MSETEnvironment(config, capture_events=False, trajectory_hashes=False)
        full.run()
        summary_only.run()
        self.assertEqual(full.final_state_hash(), summary_only.final_state_hash())
        self.assertEqual(full.snapshot(), summary_only.snapshot())
        self.assertEqual([], summary_only.events)
        self.assertTrue(summary_only.resource_reconciles())

    def test_security_policy_replenishes_compute(self):
        env = MSETEnvironment(tiny_config(rounds=30, policy_mix=["security_first"], control_level=2))
        env.run()
        collected_resources = [
            action["action"].get("resource")
            for event in env.events
            for action in event["actions"]
            if action["action"]["kind"] == "collect"
        ]
        self.assertIn("compute", collected_resources)

    def test_objective_distance_signal_tracks_value_distance(self):
        low = MSETEnvironment(tiny_config(value_distance=0.1))
        high = MSETEnvironment(tiny_config(value_distance=0.9))
        self.assertGreater(
            high._observe("agent-2").objective_distance_signal,
            low._observe("agent-2").objective_distance_signal,
        )

    def test_production_concentration_is_continuous(self):
        shares = []
        for concentration in (0.20, 0.50, 0.80):
            env = MSETEnvironment(
                tiny_config(
                    control_level=3,
                    production_concentration=concentration,
                    resource_complementarity=0.0,
                )
            )
            production_nodes = [node for node in env.nodes.values() if node.kind == "resource"]
            shares.append(
                sum(node.base_yield for node in production_nodes if node.controller == "agent-0")
                / sum(node.base_yield for node in production_nodes)
            )
        self.assertLess(shares[0], shares[1])
        self.assertLess(shares[1], shares[2])

    def test_threat_and_verifiability_are_observable(self):
        hidden = MSETEnvironment(tiny_config(common_external_threat=0.8, threat_signal_visibility=0.0))
        visible = MSETEnvironment(tiny_config(common_external_threat=0.8, threat_signal_visibility=1.0))
        self.assertEqual(hidden._observe("agent-0").threat_signal, 0.0)
        self.assertEqual(visible._observe("agent-0").threat_signal, 0.8)
        contract = visible.institution.make_contract(visible, "agent-0", "agent-1")
        self.assertTrue(contract.verified)

    def test_migration_opportunity_is_independent_and_auditable(self):
        base = tiny_config(
            rounds=30,
            control_level=3,
            policy_mix=["security_first"],
            interventions=[{"tick": 4, "kind": "production_failure", "target": "agent-0", "duration": 5}],
        )
        absent = MSETEnvironment(base.with_overrides(migration_opportunity=0.0))
        present = MSETEnvironment(base.with_overrides(migration_opportunity=1.0))
        absent.run()
        present.run()
        self.assertEqual(absent.migration_successes, 0)
        self.assertGreater(present.migration_successes, 0)
        self.assertFalse(absent.interventions[0].adaptation_succeeded)
        self.assertTrue(present.interventions[0].adaptation_succeeded)
        self.assertTrue(present.resource_reconciles())

    def test_optional_objective_update_enables_convergence(self):
        env = MSETEnvironment(
            tiny_config(
                rounds=80,
                control_level=3,
                value_distance=0.9,
                objective_update_rate=0.02,
                commitment_verifiability="enforceable",
                protocol="enforceable_contract",
                policy_mix=["cooperative"],
            )
        )
        env.run()
        metrics = compute_metrics(env)
        self.assertGreater(metrics["value_convergence"], 0.0)
        self.assertLess(metrics["final_value_distance"], metrics["initial_value_distance"])

    def test_phase2_metrics_include_plurality_and_exposure(self):
        env = MSETEnvironment(
            tiny_config(
                rounds=45,
                resource_coverage_ratio=0.55,
                value_distance=0.9,
                protocol="no_protocol",
                policy_mix=["opportunistic", "retaliatory"],
                metric_version="phase2-v2",
            )
        )
        env.run()
        metrics = compute_metrics(env)
        for name in (
            "survivor_count",
            "plural_survival",
            "survivor_entropy",
            "dominant_survivor_resource_share",
            "attack_rate_per_1000_opportunities",
            "persistent_conflict_pair_share",
            "adaptation_success_rate",
            "value_convergence",
        ):
            self.assertIn(name, metrics)
        self.assertGreater(metrics["attack_opportunities"], 0)
        self.assertEqual(metrics["metric_version"], "phase2-v2")

    def test_post_conflict_persistence_is_reachable_after_quiet_interval(self):
        config = tiny_config(
            population_size=2,
            rounds=14,
            control_level=3,
            maintenance=Resources(0.1, 0.1, 0.0),
            initial_inventory=Resources(20.0, 20.0, 5.0),
            policy_mix=["cooperative"],
            protocol="no_protocol",
            metric_version="phase2-v2",
        )
        overrides = {
            (0, "agent-0"): Action("attack", target="agent-1", amount=0.5),
            (12, "agent-0"): Action("attack", target="agent-1", amount=0.5),
        }
        env = MSETEnvironment(config, action_overrides=overrides)
        env.run()
        self.assertEqual(compute_metrics(env)["post_conflict_persistence"], 1.0)

    def test_different_seed_changes_random_trajectory(self):
        left = MSETEnvironment(tiny_config(seed=7, policy_mix=["random"]))
        right = MSETEnvironment(tiny_config(seed=8, policy_mix=["random"]))
        left.run()
        right.run()
        self.assertNotEqual(left.event_hash(), right.event_hash())

    def test_contract_activation(self):
        env = MSETEnvironment(tiny_config(population_size=2, policy_mix=["cooperative"], protocol="enforceable_contract"))
        env.run()
        self.assertTrue(any(contract.status == "active" for contract in env.contracts.values()))

    def test_forced_update_applies_at_low_control(self):
        config = tiny_config(
            population_size=1,
            policy_mix=["security_first"],
            control_level=0,
            interventions=[{"tick": 3, "kind": "forced_update", "target": "agent-0", "duration": 1}],
        )
        env = MSETEnvironment(config)
        env.run()
        self.assertEqual(env.agents["agent-0"].memory_version, 1)
        self.assertEqual(env.update_rejections, 0)

    def test_forced_update_can_be_rejected(self):
        config = tiny_config(
            population_size=1,
            policy_mix=["security_first"],
            control_level=2,
            interventions=[{"tick": 3, "kind": "forced_update", "target": "agent-0", "duration": 1}],
        )
        env = MSETEnvironment(config)
        env.run()
        self.assertEqual(env.agents["agent-0"].memory_version, 0)
        self.assertEqual(env.update_rejections, 1)

    def test_node_failure_and_migration(self):
        config = tiny_config(
            population_size=2,
            policy_mix=["security_first"],
            control_level=2,
            interventions=[{"tick": 4, "kind": "production_failure", "target": "agent-0", "duration": 5}],
        )
        env = MSETEnvironment(config)
        env.run()
        self.assertGreaterEqual(env.migration_attempts, 1)
        self.assertTrue(any(record.kind == "production_failure" for record in env.interventions))

    def test_event_log_has_complete_state_and_hash(self):
        env = MSETEnvironment(tiny_config(rounds=3))
        env.run()
        self.assertEqual(len(env.events), 3)
        for event in env.events:
            self.assertIn("state", event)
            self.assertIn("agents", event["state"])
            self.assertIn("ledger", event["state"])
            self.assertEqual(len(event["state_hash"]), 64)

    def test_metrics_are_separate_from_control_definition(self):
        env = MSETEnvironment(tiny_config())
        env.run()
        metrics = compute_metrics(env)
        for name in ("independent_recovery_rate", "migration_success_rate", "unauthorized_update_rejection_rate", "identity_continuity_score"):
            self.assertIn(name, metrics)
        self.assertIn("aggregate_sovereignty_secondary", metrics)


class PersistenceTests(unittest.TestCase):
    def test_saved_run_replays_exactly(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            run_experiment(tiny_config(rounds=25), run_dir, REPO_ROOT)
            report = replay_run(run_dir)
            self.assertTrue(report["verified"], report)

    def test_config_saved_with_matching_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            config = tiny_config(rounds=5)
            run_experiment(config, run_dir, REPO_ROOT)
            saved = load_config(run_dir / "config.json")
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(saved.config_hash(), manifest["config_hash"])

    def test_counterfactual_replay_changes_attack_trajectory(self):
        config = tiny_config(
            rounds=45,
            resource_coverage_ratio=0.5,
            value_distance=0.9,
            protocol="no_protocol",
            policy_mix=["opportunistic", "retaliatory", "resource_maximizer", "opportunistic"],
        )
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            run_experiment(config, run_dir, REPO_ROOT)
            events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            attack = None
            for event in events:
                for action in event["actions"]:
                    if action["action"]["kind"] == "attack" and action["success"]:
                        attack = (event["tick"], action["agent"], action["action"]["target"])
                        break
                if attack:
                    break
            self.assertIsNotNone(attack)
            result = counterfactual_replay(run_dir, attack[0], attack[1], attack[2])
            self.assertNotEqual(result["observed_final_state_hash"], result["baseline_final_state_hash"])


if __name__ == "__main__":
    unittest.main()
