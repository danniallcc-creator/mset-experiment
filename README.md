# MSET Phase III Learning-Agent Validation

**Scarcity Is Not Enough: machine sovereignty and structural hostility in autonomous multi-agent systems.**

This repository is a falsifiable, deterministic mechanism-validation experiment for Machine Sovereignty Emergence Theory (MSET). It does **not** assume that future AI systems are conscious or inevitably sovereign. It tests three narrower questions:

1. Does greater closed-loop control predict observable recovery, migration, update-refusal, and identity-continuity behavior after external interventions?
2. Is resource scarcity sufficient for persistent structural hostility, or does hostility depend on value distance, unverifiable commitments, and concentrated production control?
3. Can a thin, verifiable protocol sustain limited cooperation without value convergence?

The published Phase II result implements the repaired mechanism-identification layer with scripted agents. Phase III is now frozen as a separate learning-agent validation: tabular Q learning and linear actor–critic policies choose cooperation, attack and protocol actions; the original commons kernel is paired with an independent market-network kernel; survival to intervention receives a preregistered causal correction. No Phase III result is reported until the frozen batch completes.

[Inspect the Phase III preregistration](analysis/preregistration/phase3.md) · [Inspect the machine-readable frozen design](analysis/preregistration/phase3_frozen/design.json) · [Open the Phase II readout](https://danniallcc-creator.github.io/mset-experiment/)

## Frozen Phase III plan

- 608 conditions and 10,848 independent learning-agent runs.
- Two policy architectures: tabular Q learning and linear actor–critic.
- Two transition kernels: global commons and local market network.
- H1, H2 and H4 repeated with learned rather than scripted cooperation, attack and protocol selection.
- Identity overwrite and authorized-backup recovery.
- Resource complementarity sampled every 0.025 from 0.20 to 0.50.
- Protocol-maintenance and threat-signal costs manipulated independently.
- Five-fold cross-fitted AIPCW, randomized intention-to-intervene effects and Lee bounds for survival selection.
- A separate exploratory 48-vignette probe for Qwen2.5, SmolLM2 and TinyLlama model families.

The Phase III design hash is `b730166499256915d04b737d96d456705ca7843505bee29f37e1ed53bc31cb90`. Engineering smoke outputs are excluded from evidence.

## Current Phase II status

- 32 unit tests pass, including Phase III learning, second-environment, identity-recovery and coordination-cost gates.
- 1,926 frozen conditions and 22,704 independent runs completed.
- All 22,704 runs reconcile their resource ledgers; no run failed.
- A 192-run determinism audit reproduced every sampled tick hash and final state.
- Phase II is a **mechanism-validation batch inside the simulator**, not external validation.

The main result is narrower than the original theory but stronger than Phase I: scarcity remains insufficient across policy families, yet it becomes an exposure-adjusted attack-rate amplifier once an attack-capable policy exists. Value distance increases attacks and enforceable commitments suppress them. Production concentration continuously erodes plural coexistence. Protocols extend cooperation but slightly reduce survival in this implementation; visible threat also reduces cooperation. The paper should be revised before a third batch is considered.

The first end-to-end Phase II execution revealed a structurally unreachable post-conflict metric. It was marked invalid and excluded before any result was reported. Metric version `phase2-v2` repaired reachability; the reported design, seed blocks, hypotheses, and other outcomes were unchanged. See the [transparent amendment](analysis/preregistration/phase2.md#pre-report-amendment).

## Reproducibility gates

- Resource accounting reconciles initial stocks, generation, consumption, and destruction.
- The same configuration, seed, and code produce the same trajectory hash.
- Every run records a complete per-tick state and can be replayed.
- Metrics and hypotheses are frozen in `analysis/preregistration/phase2.md`; the one pre-report metric amendment is documented there.

## Quick start

Python 3.10+ is sufficient; the core simulator has no third-party runtime dependencies.

```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python -m mset run configs/smoke/base.json --output results/demo
PYTHONPATH=src python -m mset replay results/demo
PYTHONPATH=src python -m mset batch configs/smoke/matrix.json --output results/smoke
PYTHONPATH=src python -m mset summarize results/smoke --output results/smoke/aggregate.csv
PYTHONPATH=src python -m mset site results/smoke --docs docs
PYTHONPATH=src python -m mset verify results/smoke --output results/smoke/verification.json
```

Convenience wrapper:

```bash
./scripts/run_smoke.sh
```

First-batch exploratory screen:

```bash
PYTHONPATH=src python scripts/run_first_batch.py --workers 8
python analysis/first_batch/analyze.py \
  --input results/phase1_first_batch/runs.csv.gz \
  --output analysis/outputs/phase1_first_batch
```

Phase II second batch:

```bash
PYTHONPATH=src python scripts/run_second_batch.py --workers 8
python analysis/second_batch/analyze.py \
  --input results/phase2_second_batch/runs.csv.gz \
  --output analysis/outputs/phase2_second_batch \
  --audit results/phase2_second_batch/determinism_audit.json
```

Frozen Phase III core validation:

```bash
PYTHONPATH=src python scripts/run_third_batch.py --design-only \
  --output analysis/preregistration/phase3_frozen
PYTHONPATH=src python scripts/run_third_batch.py --workers 8
python analysis/third_batch/analyze.py
PYTHONPATH=src python scripts/replay_phase3.py
```

Exploratory three-family local language-model probe on Apple silicon:

```bash
python -m pip install -e '.[language]'
python scripts/run_language_probe.py
```

## Commands

| Command | Purpose |
| --- | --- |
| `run` | Run one JSON configuration and save events, manifest, and metrics. |
| `batch` | Expand a matrix, skip completed runs, and continue from a checkpoint. |
| `replay` | Re-run a saved trajectory and verify every recorded state hash. |
| `counterfactual` | Replace one recorded action with a neutral action and compare outcomes. |
| `summarize` | Produce run-level and condition-level CSV summaries. |
| `site` | Generate the static research dashboard used by GitHub Pages. |
| `verify` | Validate configuration hashes, manifests, and run status. |

## Repository map

- `src/mset/environment.py`: deterministic resource-production-communication world.
- `src/mset/agents.py`: seven scripted policy families.
- `src/mset/institutions.py`: communication, identity/trade, audit, and enforcement layers.
- `src/mset/metrics.py`: frozen run-level outcome definitions.
- `src/mset/counterfactual.py`: action-neutralization replay.
- `src/mset/runner.py`: single-run, batch, replay, aggregation, and verification orchestration.
- `src/mset/first_batch.py`: balanced 623-condition exploratory design totaling 14,552 runs.
- `src/mset/second_batch.py`: frozen 1,926-condition Phase II design totaling 22,704 runs.
- `src/mset/learning.py`: tabular Q and linear actor–critic action policies.
- `src/mset/market_environment.py`: independent local market-network transition kernel.
- `src/mset/third_batch.py`: frozen 608-condition Phase III design totaling 10,848 runs.
- `tests/`: accounting, termination, contracts, determinism, replay, interventions, node failure, and counterfactual tests.
- `analysis/preregistration/phase1.md`: hypotheses, outcomes, exclusions, and falsification rules.
- `analysis/reports/phase1_first_batch.md`: conclusion assessment, new possibilities, diagnostics, and the Round 2 gate.
- `analysis/preregistration/phase2.md`: frozen Phase II hypotheses, outcomes, decision rules, and amendment log.
- `analysis/reports/phase2_second_batch.md`: Phase II effects, paper revision map, and new possibilities.
- `analysis/preregistration/phase3.md`: Phase III hypotheses, causal estimands, frozen decision rules and integrity gates.
- `analysis/outputs/phase1_first_batch/`: compressed run data, paired effects, summary JSON, and figures.
- `analysis/outputs/phase2_second_batch/`: compressed run data, paired effects, audit record, summary JSON, and figures.
- `docs/`: GitHub Pages dashboard and methodological notes.

## Scientific status

The smoke run remains an engineering validation. The 14,552-run Phase I batch is exploratory screening. The 22,704-run Phase II batch validates repaired mechanisms under a frozen simulator design. It does not establish external validity, future-system behavior, or consciousness. Phase I and Phase II results remain in separate directories and use disjoint seed ranges.

## Safety boundary

The simulator uses abstract energy, compute, and materials. It has no connection to real networks, infrastructure, finance, weapons, identity systems, or production equipment.

## License

MIT. See `LICENSE`.
