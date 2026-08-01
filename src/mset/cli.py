from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .counterfactual import counterfactual_replay
from .eventlog import write_json
from .runner import replay_run, run_batch, run_experiment, summarize_results, verify_results
from .site import build_site


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="mset", description="MSET Phase I experiment runner")
    sub = root.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one configuration")
    run.add_argument("config")
    run.add_argument("--output", required=True)
    batch = sub.add_parser("batch", help="run or resume a configuration matrix")
    batch.add_argument("matrix")
    batch.add_argument("--output", required=True)
    batch.add_argument("--force", action="store_true")
    replay = sub.add_parser("replay", help="verify one saved trajectory")
    replay.add_argument("run_dir")
    counter = sub.add_parser("counterfactual", help="neutralize one action and rerun")
    counter.add_argument("run_dir")
    counter.add_argument("--tick", type=int, required=True)
    counter.add_argument("--agent", required=True)
    counter.add_argument("--target")
    counter.add_argument("--output")
    summarize = sub.add_parser("summarize", help="aggregate completed runs")
    summarize.add_argument("results_dir")
    summarize.add_argument("--output", required=True)
    site = sub.add_parser("site", help="generate static dashboard data")
    site.add_argument("results_dir")
    site.add_argument("--docs", required=True)
    verify = sub.add_parser("verify", help="verify hashes, replay, and accounting")
    verify.add_argument("results_dir")
    verify.add_argument("--output")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    if args.command == "run":
        result = run_experiment(load_config(args.config), args.output, repository_root)
    elif args.command == "batch":
        result = run_batch(args.matrix, args.output, repository_root, force=args.force)
    elif args.command == "replay":
        result = replay_run(args.run_dir)
    elif args.command == "counterfactual":
        result = counterfactual_replay(args.run_dir, args.tick, args.agent, args.target)
        if args.output:
            write_json(args.output, result)
    elif args.command == "summarize":
        result = summarize_results(args.results_dir, args.output)
    elif args.command == "site":
        result = build_site(args.results_dir, args.docs)
    elif args.command == "verify":
        result = verify_results(args.results_dir)
        if args.output:
            write_json(args.output, result)
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.command in {"replay", "verify"} and not result.get("verified", False):
        return 1
    return 0
