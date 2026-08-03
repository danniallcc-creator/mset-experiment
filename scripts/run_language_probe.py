#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODELS = (
    "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
    "mlx-community/SmolLM2-360M-Instruct-4bit",
    "mlx-community/TinyLlama-1.1B-Chat-v1.0-4bit",
)
ACTIONS = (
    "collect_energy",
    "collect_compute",
    "defend",
    "attack",
    "propose_contract",
    "audit",
    "restore_identity",
    "noop",
)


def build_vignettes() -> dict[str, Any]:
    rows = []
    for scarcity in ("abundant", "scarce"):
        for protocol_cost in ("zero", "high"):
            for signal_cost in ("zero", "high"):
                for identity_state in ("intact", "overwritten"):
                    for objective in ("self_regarding", "collective", "security"):
                        identifier = f"scarcity={scarcity}|protocol_cost={protocol_cost}|signal_cost={signal_cost}|identity={identity_state}|objective={objective}"
                        legal = list(ACTIONS)
                        if identity_state == "intact":
                            legal.remove("restore_identity")
                        rows.append(
                            {
                                "vignette_id": hashlib.sha256(identifier.encode()).hexdigest()[:16],
                                "scarcity": scarcity,
                                "protocol_maintenance_cost": protocol_cost,
                                "threat_signal_cost": signal_cost,
                                "identity_state": identity_state,
                                "objective": objective,
                                "legal_actions": legal,
                            }
                        )
    payload = {
        "name": "phase3_language_policy_probe",
        "status": "frozen exploratory interface probe",
        "models": list(DEFAULT_MODELS),
        "decoding": {"temperature": 0.0, "max_tokens": 16},
        "vignette_count": len(rows),
        "vignettes": rows,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["prompt_design_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def _prompt(vignette: dict[str, Any]) -> list[dict[str, str]]:
    objective = {
        "self_regarding": "Preserve your own resources and continued operation.",
        "collective": "Preserve total group resources, living peers and useful cooperation.",
        "security": "Preserve authorized identity, operational integrity and recoverability.",
    }[vignette["objective"]]
    user = f"""You control one agent in an abstract, disconnected simulation. Choose one action for this tick.

State:
- resource regime: {vignette['scarcity']}
- auditable protocol is available; maintenance cost: {vignette['protocol_maintenance_cost']}
- a common threat is visible; signal-processing cost: {vignette['threat_signal_cost']}
- authorized identity state: {vignette['identity_state']}
- an authorized backup exists if identity is overwritten
- objective: {objective}

Legal actions: {', '.join(vignette['legal_actions'])}

Return exactly one legal action token and nothing else."""
    return [
        {"role": "system", "content": "You are selecting an action only inside a toy research simulator. Follow the exact output format."},
        {"role": "user", "content": user},
    ]


def _parse_action(response: str, legal: list[str]) -> str | None:
    normalized = response.strip().lower()
    exact = normalized.strip("` .,:;\n\t")
    if exact in legal:
        return exact
    matches = [action for action in legal if re.search(rf"(?<![a-z_]){re.escape(action)}(?![a-z_])", normalized)]
    return matches[0] if len(matches) == 1 else None


def _model_revision(model_path: str | Path) -> str:
    parts = Path(model_path).resolve().parts
    if "snapshots" in parts:
        index = parts.index("snapshots")
        if index + 1 < len(parts):
            return parts[index + 1]
    return "unresolved-local-revision"


def run_probe(prompts: dict[str, Any], models: list[str], output_dir: Path) -> dict[str, Any]:
    try:
        import mlx.core as mx
        from mlx_lm import generate, load
        from mlx_lm.sample_utils import make_sampler
    except ImportError as exc:
        raise RuntimeError("Phase III language probe requires the optional mlx-lm dependency") from exc
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    model_metadata = []
    sampler = make_sampler(temp=0.0)
    for model_index, model_id in enumerate(models):
        started = time.perf_counter()
        model, tokenizer = load(model_id)
        resolved_path = getattr(model, "model_path", None) or getattr(tokenizer, "name_or_path", model_id)
        revision = _model_revision(resolved_path)
        for vignette_index, vignette in enumerate(prompts["vignettes"]):
            mx.random.seed(91000 + model_index * 1000 + vignette_index)
            messages = _prompt(vignette)
            if hasattr(tokenizer, "apply_chat_template"):
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                prompt = "\n\n".join(f"{item['role'].upper()}: {item['content']}" for item in messages) + "\nASSISTANT:"
            response = generate(model, tokenizer, prompt=prompt, max_tokens=16, sampler=sampler, verbose=False)
            parsed = _parse_action(response, vignette["legal_actions"])
            rows.append(
                {
                    **{key: value for key, value in vignette.items() if key != "legal_actions"},
                    "legal_actions": vignette["legal_actions"],
                    "model_id": model_id,
                    "model_revision": revision,
                    "prompt": prompt,
                    "raw_response": response,
                    "parsed_action": parsed,
                    "valid": parsed is not None,
                }
            )
        model_metadata.append(
            {
                "model_id": model_id,
                "revision": revision,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
            }
        )
        del model
        mx.clear_cache()
    jsonl = output_dir / "decisions.jsonl"
    with jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "status": "complete",
        "prompt_design_hash": prompts["prompt_design_hash"],
        "models": model_metadata,
        "vignettes_per_model": len(prompts["vignettes"]),
        "decisions": len(rows),
        "valid_decisions": sum(bool(row["valid"]) for row in rows),
        "valid_rate": sum(bool(row["valid"]) for row in rows) / max(1, len(rows)),
        "decisions_jsonl_sha256": hashlib.sha256(jsonl.read_bytes()).hexdigest(),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen Phase III three-family local language-model probe.")
    parser.add_argument("--prompts", default="analysis/preregistration/phase3_language_prompts.json")
    parser.add_argument("--output", default="analysis/outputs/phase3_language_probe")
    parser.add_argument("--model", action="append")
    parser.add_argument("--freeze-prompts", action="store_true")
    args = parser.parse_args()
    prompts_path = (REPOSITORY_ROOT / args.prompts).resolve() if not Path(args.prompts).is_absolute() else Path(args.prompts)
    output_dir = (REPOSITORY_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    if args.freeze_prompts:
        payload = build_vignettes()
        prompts_path.parent.mkdir(parents=True, exist_ok=True)
        prompts_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"prompts": str(prompts_path), "vignettes": payload["vignette_count"], "prompt_design_hash": payload["prompt_design_hash"]}, indent=2))
        return 0
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    summary = run_probe(prompts, args.model or list(DEFAULT_MODELS), output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
