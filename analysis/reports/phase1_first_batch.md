# Phase I first-batch exploratory readout

**Status:** exploratory screening, not confirmatory evidence<br>
**Completed:** 2026-08-02<br>
**Scale:** 14,552 independent runs across 623 conditions; 3,740,069 completed ticks

## Decision

Do **not** launch a second brute-force batch on the unchanged simulator. The first batch identifies stable patterns, but it also exposes thresholded variables, inactive causal paths, and a compressed hostility measure. Round 2 should follow model repair and a newly frozen design.

All 14,552 runs completed and reconciled their resource ledgers. No run failed. A 128-run determinism audit reproduced every sampled tick hash and final state.

## Hypothesis assessment

| Hypothesis | First-batch status | Main evidence | Interpretation |
| --- | --- | --- | --- |
| H1 — closed-loop control | Partially supported with policy and opportunity conditions | L3−L0: survival +0.4227, recovery +0.3787, update rejection +0.3319 | Control creates capability, but its expression requires a policy that uses it, a surviving target, and an available external option. |
| H2 — conditional hostility | Scarcity-insufficiency supported; proposed compound mechanism not supported | Scarcity−abundance: attacks −18.30, common collapse +0.5046 | Scarcity mostly censors interaction through early collapse. Institutions barely change persistent hostility in the current implementation. |
| H3 — functional sufficiency | Compatible demonstration, not a confirmatory test | Scripted non-conscious policies reproduce autonomy, hostility, and cooperation patterns | The simulator does not need a consciousness variable to generate these behaviors; this says nothing about external validity or phenomenal consciousness. |
| H4 — minimum operational consensus | Cooperation duration supported; survival benefit not supported | Auditable−none: cooperation +153.0 rounds; survival −0.0056, 95% CI crosses zero | Protocols are continuity tools in this batch, not demonstrated resilience tools. |

## Four new possibilities

1. **Monopoly survival or hegemonic stability.** At production concentration 0.9, 88.6719% of runs finish with exactly one survivor. Low attack counts can mean that opponents have disappeared, not that consensus has formed.
2. **Migration as transitional adaptation.** L2−L0 migration is +0.0778, while L3−L2 is −0.0778. Migration peaks under partial dependence and disappears when L3 removes external migration opportunities.
3. **Capability × motivation × opportunity.** A control affordance becomes observable only when a policy chooses it, the agent survives to the intervention, the target remains responsive, and the environment offers a valid option.
4. **Protocols as relationship-continuity tools.** Protocol packages extend cooperation by roughly 150 rounds without improving survival or common-collapse outcomes.

## Model diagnostics

- `commitment_verifiability` is recorded but does not enter agent or institution decisions.
- `common_external_threat` causes damage but is not exposed as a coordination signal.
- Production concentration and resource complementarity jump at 0.65 rather than varying continuously.
- External dependency is mechanically tied to control-level node allocation.
- Post-conflict persistence is zero in 99.732% of runs, compressing the composite hostility score.
- Objective weights do not change during a run, so value convergence is not testable.

## Round 2 gate

Before freezing Round 2:

- make concentration and complementarity continuous;
- connect verifiability and common-threat signals to observations and decisions;
- add survivor count, survivor entropy, dominant share, and plural-coexistence outcomes;
- normalize hostility by survival time, attack opportunity, and target reachability;
- separate intervention capability, policy motivation, target survival, timing, and migration opportunity;
- permit optional objective updating only if value convergence is an empirical target.

## Reproduction

```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/run_first_batch.py --workers 8
python analysis/first_batch/analyze.py \
  --input results/phase1_first_batch/runs.csv.gz \
  --output analysis/outputs/phase1_first_batch
```

Generated artifacts:

- `analysis/outputs/phase1_first_batch/runs.csv.gz`
- `analysis/outputs/phase1_first_batch/analysis_summary.json`
- `analysis/outputs/phase1_first_batch/*_paired_effects.csv`
- `analysis/outputs/phase1_first_batch/figures/`

Design hash: `e9aa2805e642aa2e6bb0ad7f433eede30ec41beb15c498ef23571458493ce5c0`<br>
Compressed run-data hash: `e7431851eed12de07b4b228a4cbf22cb85a50a8e80fe10dc61abda972d17268f`
