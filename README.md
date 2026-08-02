# MSET Phase I Experiment

**Scarcity Is Not Enough: machine sovereignty and structural hostility in autonomous multi-agent systems.**

This repository is a falsifiable, deterministic first-stage experiment for Machine Sovereignty Emergence Theory (MSET). It does **not** assume that future AI systems are conscious or inevitably sovereign. It tests three narrower questions:

1. Does greater closed-loop control predict observable recovery, migration, update-refusal, and identity-continuity behavior after external interventions?
2. Is resource scarcity sufficient for persistent structural hostility, or does hostility depend on value distance, unverifiable commitments, and concentrated production control?
3. Can a thin, verifiable protocol sustain limited cooperation without value convergence?

The current release implements the mechanism-identification layer with scripted agents. Reinforcement learning and language-model agents are deliberately out of scope until the accounting, determinism, replay, and metric-freezing gates pass.

[Open the 14,552-run readout](https://danniallcc-creator.github.io/mset-experiment/) · [Read the first-batch analysis](analysis/reports/phase1_first_batch.md) · [Read the preregistration scaffold](analysis/preregistration/phase1.md)

## Current Phase I status

- 20 unit tests pass.
- 623 exploratory conditions and 14,552 independent runs completed.
- All 14,552 runs reconcile their resource ledgers; no run failed.
- A 128-run determinism audit reproduced every sampled tick hash and final state.
- The first-batch readout is **exploratory screening**, not confirmatory evidence.

The main result is narrower than the original theory: scarcity is insufficient for persistent hostility in this implementation, but the specified compound mechanism is not supported. Scarcity chiefly causes early collapse; high production concentration often leaves a single survivor; protocol packages extend cooperation without improving survival. Round 2 is on hold until the model-validity issues in the [analysis note](analysis/reports/phase1_first_batch.md) are repaired.

## Reproducibility gates

- Resource accounting reconciles initial stocks, generation, consumption, and destruction.
- The same configuration, seed, and code produce the same trajectory hash.
- Every run records a complete per-tick state and can be replayed.
- Metrics and hypotheses are frozen in `analysis/preregistration/phase1.md` before confirmatory runs.

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
- `tests/`: accounting, termination, contracts, determinism, replay, interventions, node failure, and counterfactual tests.
- `analysis/preregistration/phase1.md`: hypotheses, outcomes, exclusions, and falsification rules.
- `analysis/reports/phase1_first_batch.md`: conclusion assessment, new possibilities, diagnostics, and the Round 2 gate.
- `analysis/outputs/phase1_first_batch/`: compressed run data, paired effects, summary JSON, and figures.
- `docs/`: GitHub Pages dashboard and methodological notes.

## Scientific status

The smoke run remains an engineering validation. The 14,552-run first batch is a separate **exploratory** screen used to discover dose responses, interactions, measurement failures, and competing explanations. Neither is a frozen confirmatory test. Exploratory and confirmatory results remain in separate directories and use different seed ranges.

## Safety boundary

The simulator uses abstract energy, compute, and materials. It has no connection to real networks, infrastructure, finance, weapons, identity systems, or production equipment.

## License

MIT. See `LICENSE`.
