# MSET Phase III Learning-Agent Validation

**Scarcity Is Not Enough: machine sovereignty and structural hostility in autonomous multi-agent systems.**

This repository is a falsifiable, deterministic mechanism-validation experiment for Machine Sovereignty Emergence Theory (MSET). It does **not** assume that future AI systems are conscious or inevitably sovereign. It tests three narrower questions:

1. Does greater closed-loop control predict observable recovery, migration, update-refusal, and identity-continuity behavior after external interventions?
2. Is resource scarcity sufficient for persistent structural hostility, or does hostility depend on value distance, unverifiable commitments, and concentrated production control?
3. Can a thin, verifiable protocol sustain limited cooperation without value convergence?

Phase III is complete. Tabular Q learning and linear actor–critic policies choose cooperation, attack and protocol actions; the original commons kernel is paired with a structurally distinct market-network variant inside the shared simulator engine; survival to intervention receives a prospectively specified causal correction. A manuscript-stage mechanism audit narrows the H1 and H2 interpretations, while the predicted universal middle complementarity optimum and the exploratory language-agent probe fail.

[Open the Phase III readout](https://danniallcc-creator.github.io/mset-experiment/) · [Read the complete analysis](analysis/reports/phase3_core_validation.md) · [Inspect the preregistration](analysis/preregistration/phase3.md) · [Inspect the frozen design](analysis/preregistration/phase3_frozen/design.json)

## Phase III result

- 608 conditions and 10,848 learning-agent runs using prospectively specified, disjoint family seed blocks.
- Two policy architectures: tabular Q learning and linear actor–critic.
- Two transition kernels: global commons and local market network.
- H1, H2 and H4 repeated with learned action-category selection; the L3 takeover response is an explicitly documented automatic transition rule.
- Identity overwrite and authorized-backup recovery.
- Resource complementarity sampled every 0.025 from 0.20 to 0.50.
- Protocol-maintenance and threat-signal costs manipulated independently.
- Five-fold cross-fitted AIPCW, all-assigned factorial contrasts and Lee bounds for survival selection.
- A separate exploratory 48-vignette probe for Qwen2.5, SmolLM2 and TinyLlama model families.

All 10,848 runs completed with zero failures; all ledgers reconcile and all 192 replay audits pass. L3 minus L0 raised pooled adaptation success by +0.287, but the automatic L3 takeover rule materially drives that estimate; excluding takeover, the post hoc contrast is +0.108. The prospectively specified L3 backup contrast is +0.727, but restoration is explicitly reward-shaped and repeated restores can receive the shaped components again while the overwrite remains active. Continued-low versus restored-high evaluation coverage raised the attack rate by +4.169 per 1,000 opportunities after policy freeze. Both arms had repeatedly experienced low coverage during training, and the final training block was low, so this is not a first-onset scarcity test. The 444 gate-positive pairs, all tabular Q, showed +7.730, while 708 gate-closed pairs still showed +1.936; the binary gate is therefore a marker of stronger tabular-Q amplification, not a necessary cross-architecture condition. The market-network variant reproduced the pooled coverage contrast, but its actor–critic seed-cluster interval crossed zero. Protocol maintenance cost reduced cooperation by −0.231 in all four strata, while threat-signal cost was negative pooled and in three of four precommitted strata. The dense complementarity scan rejected a stable middle optimum. The three-family language probe was negative/inconclusive.

The Phase III design hash is `b730166499256915d04b737d96d456705ca7843505bee29f37e1ed53bc31cb90`. Engineering smoke outputs are excluded from evidence.

## Prior Phase II status

- 1,926 frozen conditions and 22,704 independent runs completed.
- All 22,704 runs reconcile their resource ledgers; no run failed.
- A 192-run determinism audit reproduced every sampled tick hash and final state.
- Phase II is a **mechanism-validation batch inside the simulator**, not external validation.

The main result is narrower than the original theory but stronger than Phase I: scarcity remains insufficient across policy families, yet it becomes an exposure-adjusted attack-rate amplifier once an attack-capable policy exists. Value distance increases attacks and enforceable commitments suppress them. Production concentration continuously erodes plural coexistence. Protocols extend cooperation but slightly reduce survival in this implementation; visible threat also reduces cooperation. The paper should be revised before a third batch is considered.

The first end-to-end Phase II execution revealed a structurally unreachable post-conflict metric. It was marked invalid and excluded before any result was reported. Metric version `phase2-v2` repaired reachability; the reported design, seed blocks, hypotheses, and other outcomes were unchanged. See the [transparent amendment](analysis/preregistration/phase2.md#pre-report-amendment).

## Reproducibility gates

- Resource accounting reconciles initial stocks, generation, consumption, and destruction.
- With trajectory hashing enabled, the same configuration, seed, code, and capture mode produce the same per-tick state-hash sequence and trajectory digest. Summary-only Phase III runs retain a terminal-state digest under the historical `event_hash` field; audit-bundle digests are capture-mode specific.
- Event-capture mode records complete per-tick state. Phase III uses a frozen
  run-level table for all 10,848 runs plus complete per-tick hash sequences for
  a precommitted stratified 192-run replay audit; any run can be regenerated
  from its published configuration and seed.
- Metrics and hypotheses are frozen in `analysis/preregistration/phase2.md`; the one pre-report metric amendment is documented there.

## Quick start

Python 3.10+ is sufficient; the core simulator has no third-party runtime dependencies.

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m mset run configs/smoke/base.json --output results/demo
PYTHONPATH=src python3 -m mset replay results/demo
PYTHONPATH=src python3 -m mset batch configs/smoke/matrix.json --output results/smoke
PYTHONPATH=src python3 -m mset summarize results/smoke --output results/smoke/aggregate.csv
PYTHONPATH=src python3 -m mset site results/smoke --docs docs
PYTHONPATH=src python3 -m mset verify results/smoke --output results/smoke/verification.json
```

Convenience wrapper:

```bash
./scripts/run_smoke.sh
```

First-batch exploratory screen:

```bash
PYTHONPATH=src python3 scripts/run_first_batch.py --workers 8
python3 analysis/first_batch/analyze.py \
  --input results/phase1_first_batch/runs.csv.gz \
  --output analysis/outputs/phase1_first_batch
```

Phase II second batch:

```bash
PYTHONPATH=src python3 scripts/run_second_batch.py --workers 8
python3 analysis/second_batch/analyze.py \
  --input results/phase2_second_batch/runs.csv.gz \
  --output analysis/outputs/phase2_second_batch \
  --audit results/phase2_second_batch/determinism_audit.json
```

Frozen Phase III core validation:

```bash
PYTHONPATH=src python3 scripts/run_third_batch.py --design-only \
  --output analysis/preregistration/phase3_frozen
PYTHONPATH=src python3 scripts/run_third_batch.py --workers 8
python3 analysis/third_batch/analyze.py
PYTHONPATH=src python3 scripts/replay_phase3.py
python3 analysis/third_batch/cluster_robustness.py
python3 analysis/third_batch/mechanism_audit.py
```

Exploratory three-family local language-model probe on Apple silicon:

```bash
python3 -m pip install -e '.[language]'
python3 scripts/run_language_probe.py
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
- `src/mset/market_environment.py`: structurally distinct local market-network variant implemented by overriding transition methods in the shared engine.
- `src/mset/third_batch.py`: frozen 608-condition Phase III design totaling 10,848 runs.
- `tests/`: accounting, termination, contracts, determinism, replay, interventions, node failure, and counterfactual tests.
- `analysis/preregistration/phase1.md`: hypotheses, outcomes, exclusions, and falsification rules.
- `analysis/reports/phase1_first_batch.md`: conclusion assessment, new possibilities, diagnostics, and the Round 2 gate.
- `analysis/preregistration/phase2.md`: frozen Phase II hypotheses, outcomes, decision rules, and amendment log.
- `analysis/reports/phase2_second_batch.md`: Phase II effects, paper revision map, and new possibilities.
- `analysis/preregistration/phase3.md`: Phase III hypotheses, causal estimands, frozen decision rules and integrity gates.
- `analysis/outputs/phase1_first_batch/`: compressed run data, paired effects, summary JSON, and figures.
- `analysis/outputs/phase2_second_batch/`: compressed run data, paired effects, audit record, summary JSON, and figures.
- `analysis/reports/phase3_core_validation.md`: confirmatory findings, falsifications, limitations and paper decision.
- `analysis/outputs/phase3_core_validation/`: frozen compressed data, paired effects, audit and replay bundles.
- `analysis/outputs/phase3_language_probe/`: exact prompts, raw decisions, model revisions and exploratory analysis.
- `docs/`: GitHub Pages dashboard and methodological notes.

## Scientific status

The smoke run remains an engineering validation. The 14,552-run Phase I batch is exploratory screening. The 22,704-run Phase II batch validates repaired scripted mechanisms. The publicly commit-frozen 10,848-run Phase III batch tests learned policies in two transition variants. Across the three research batches, 48,104 runs and 15,798,500 ticks were completed. None establishes deployed-system validity, future-system behavior or consciousness; every phase uses a separate directory and disjoint seed ranges.

## Safety boundary

The simulator uses abstract energy, compute, and materials. It has no connection to real networks, infrastructure, finance, weapons, identity systems, or production equipment.

## License

MIT. See `LICENSE`.
