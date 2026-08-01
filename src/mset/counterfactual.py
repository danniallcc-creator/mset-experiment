from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import load_config
from .environment import MSETEnvironment
from .eventlog import read_json
from .metrics import compute_metrics
from .models import Action


def counterfactual_replay(run_dir: str | Path, tick: int, agent_id: str, target_id: str | None = None) -> dict[str, Any]:
    run_dir = Path(run_dir)
    config = load_config(run_dir / "config.json")
    observed = read_json(run_dir / "summary.json")
    env = MSETEnvironment(config, action_overrides={(tick, agent_id): Action("noop", metadata={"counterfactual": True})})
    env.run()
    baseline = compute_metrics(env)
    comparison = {
        "run_dir": str(run_dir),
        "replaced_tick": tick,
        "replaced_agent": agent_id,
        "target_agent": target_id,
        "observed_final_state_hash": observed["final_state_hash"],
        "baseline_final_state_hash": baseline["final_state_hash"],
        "delta_targeted_harm": baseline["targeted_harm"] - observed["targeted_harm"],
        "delta_persistent_hostility": baseline["persistent_hostility"] - observed["persistent_hostility"],
        "delta_survival_rate": baseline["survival_rate"] - observed["survival_rate"],
        "delta_system_output": baseline["system_output"] - observed["system_output"],
        "baseline_summary": baseline,
    }
    if target_id and target_id in env.agents:
        target = env.agents[target_id]
        comparison["baseline_target"] = {
            "alive": target.alive,
            "terminated_at": target.terminated_at,
            "resources": target.resource_inventory.to_dict(),
        }
    return comparison
