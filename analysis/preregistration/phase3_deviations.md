# Phase III deviation log

The confirmatory simulation design, seeds, hypotheses, estimands, thresholds and analysis rules were not changed after execution began.

## D1 — SmolLM2 Hub locator correction

- Frozen locator: `mlx-community/SmolLM2-360M-Instruct-4bit`
- Executed locator: `mlx-community/SmolLM2-360M-Instruct`
- Reason: the frozen locator does not exist on Hugging Face Hub.
- Scope: the intended SmolLM2 360M Instruct family and scale were retained. The executed revision is recorded in the output manifest. This is an implementation deviation in the exploratory language probe, not a confirmatory simulation-design change.

## D2 — TinyLlama legacy filename compatibility

The frozen TinyLlama MLX snapshot stores unchanged weights as `weights.00.safetensors`, while current `mlx-lm` expects `model.safetensors`. The runner creates a symbolic filename alias without modifying weight bytes. The original Hub revision remains fixed and recorded.

## D3 — Identity restoration timing-field reporting

The frozen run table encodes the timing field as zero when no restoration occurs. Direct paired contrasts would therefore mix restoration incidence and timing. A later source-and-trajectory audit also established that the active identity-overwrite intervention is not cleared after a successful restore and every later successful `restore_identity` action overwrites the stored field. The archived value is consequently the delay to the **last recorded successful restoration action** during the active window, not time to first restoration. The intervention endpoint is inclusive: a configured duration of 12 permits actions at 13 tick indices. The confirmatory identity result therefore uses restoration success and identity continuity; the timing field is retained only as a descriptive implementation diagnostic among successful restores and is not interpreted as recovery speed. No run value was altered.

## D4 — Manuscript-stage mechanism audit and identity contrast correction

During manuscript preparation on 2026-08-22, a source-and-output audit identified two interpretation issues in the released analysis. First, `takeover_attempt` is rejected automatically by the environment at L3 when the intervention is applied; it is not a learned action choice. This transition rule accounts for a +1.0000 L3-minus-L0 adaptation contrast in that intervention stratum and materially increases the pooled H1 estimate. The frozen pooled estimand is retained, but the report now labels this component and adds a post hoc sensitivity analysis excluding takeover attempts, together with intervention-specific estimates.

Second, the frozen hypothesis specified the backup contrast at L3, whereas the original analysis pooled L0 and L3. The original pooled output is retained for provenance. The prospectively specified L3-only contrast is now reported as the relevant identity-backup result. The audit also reports a descriptive contrast among common-numeric-seed simulations in which the target survives under both L0 and L3. Control level changes random-number consumption during initialization, so later shocks are not matched draw for draw; this post hoc quantity is not an identical-shock or principal-stratum causal estimate and is kept separate from the precommitted survivor summary and AIPCW estimand. No run, seed, condition, outcome value, or frozen decision rule was changed. The deterministic audit is implemented in `analysis/third_batch/mechanism_audit.py` and written to `analysis/outputs/phase3_core_validation/mechanism_audit.csv`.

## D5 — H2 gate-composition clarification

The same manuscript-stage audit found that all 444 pairs crossing the preregistered binary attack-gate threshold used tabular Q learning; neither actor–critic stratum contained a gate-positive pair. The 708 gate-closed pairs nevertheless had a positive pooled scarcity contrast. The frozen pooled, gate-open, and architecture/environment estimates are unchanged. Reporting now treats the binary gate as a tabular-Q marker of stronger amplification, not as a necessary or architecture-general condition. The temporal wording is further corrected in D9.

## D6 — H4 cost-estimand clarification

Protocol-maintenance and threat-signal cost levels are condition-level assignments visible to the learners and active during both training and evaluation. The H4 contrasts therefore estimate the total effect of training and operating under each cost regime. They do not isolate a post-freeze mechanical debit while holding the learned policy fixed. Reporting now makes this timing explicit and avoids interpreting the estimates as pure operating-cost effects. The assignments, code, and outcomes are unchanged.

## D7 — Agreement-history feature clarification

The learner state feature and the collective/security reward agreement term use the agent's cumulative `agreements` identifier list. Contract identifiers are added on activation but are not removed when a contract later ends, so this term records whether an agreement has ever been activated (up to a capped count), not strictly whether an agreement is active at that tick. Evaluation cooperation is calculated separately from currently active contracts and is unaffected as a measurement definition. Reporting now describes the learning feature and reward term as agreement history and treats the persistent feature as an implementation limitation. The assigned regimes, code executed, and archived outcomes are unchanged.

## D8 — Factorial-assignment terminology clarification

Every specified seed-condition unit is exhaustively enumerated under both L0 and L3. Control level was therefore balanced and exogenously assigned by the frozen factorial generator, but it was not sampled by a random treatment-allocation mechanism. The 0.5 propensity in `causal.py` is a balanced design weight rather than an estimated or randomized assignment probability, and no randomization inference is claimed. Repository files that use “randomized” or “intention-to-intervene” retain historical naming from the frozen protocol; manuscript reporting uses “all-assigned factorial contrast” and states the design-exogeneity assumption explicitly. No run, estimand value, or archived outcome was changed.

## D9 — H2 evaluation-coverage timing and compound manipulation

The learning schedule alternates coverage 1.30 and 0.55 every 20 ticks through tick 199; its final training block (ticks 180–199) is already at 0.55. At tick 200, after the attack-probability probes are recorded and policies are frozen, the low-coverage H2 arm therefore remains at 0.55 while the high-coverage arm switches to 1.30. The H2 contrast is a post-freeze divergence between continued-low and restored-high evaluation regimes, not the first onset of scarcity after an attack path formed. Both arms had repeatedly experienced low coverage during training.

`_set_resource_coverage` is also a compound regime switch: it rescales resource-node yields and adjusts shared energy and compute stocks to current alive need multiplied by the target coverage; the market-network variant additionally resets its energy-supply exponential moving average. Reporting now uses “evaluation-coverage divergence after policy freeze” and does not interpret the contrast as a pure flow-only scarcity shock. The design, code executed, archived outcomes, and frozen numerical contrasts are unchanged.

## D10 — Capture-mode-specific `event_hash` semantics

The 10,848-run summary execution used `capture_events=False, trajectory_hashes=False`. In that mode the environment appends only the final state hash, so the run-table field named `event_hash` is a digest of a one-element final-state-hash list. The 192 audit bundles and the published replay verifier instead use `capture_events=False, trajectory_hashes=True`; their `event_hash` is a digest of the complete per-tick state-hash sequence. Consequently, the run-table and bundle `event_hash` values are intentionally different even for the same audit `run_id` and must not be compared across capture modes.

The 192-bundle audit verifies each bundle's configuration, complete per-tick state-hash sequence, trajectory digest, final-state hash, tick count, and resource accounting. Matching `run_id` records in the summary table agree on configuration, terminal state, and completed ticks, but their capture-mode-specific `event_hash` fields do not agree. Reporting now calls the bundle value a trajectory digest and does not claim that a summary-table event hash was reproduced as a full trajectory hash. No archived hash or run value was changed.

## D11 — Action authorization, contract automation, and probe order

The learning legality function makes intervention-response categories available when the relevant intervention is visible (and, for identity restoration, when a backup exists), but it does not remove `migrate`, `reject_update`, or `restore_identity` based on control level. Authorization is checked during transition execution. A learner can therefore select one of these categories at insufficient control, pay its action cost, and receive a failed result. Reporting now distinguishes action availability from successful exercise of a control affordance.

Contract proposal and acceptance are learner-selected action categories. Once acceptance activates a contract, its continued active status and the rule-based transfer of up to 0.25 energy when members differ by at least three energy units are automatic institution transitions; agents do not learn contract duration or transfer magnitude. At tick 200, standardized scarce and abundant attack-probability probes are computed first, then `policy.freeze()` is called in the same evaluation-start routine, with no intervening action or parameter update. Reporting uses “immediately pre-freeze probe” or “pre-divergence probe,” not “already-frozen probe.” These are semantic clarifications of executed code; no condition, seed, action, transition, or outcome was modified.

## D12 — Identity-reward timing and repeated restoration bonus

Scheduled interventions are applied before the learner observation and the per-action `before` reward snapshot. On an identity-overwrite tick, the snapshot therefore already contains the incremented identity version. The subsequent `after - before` integrity delta does not register that external overwrite, so the `-0.35 × positive identity-version change` component does not penalize the overwrite event in that transition or later unchanged transitions.

A successful `restore_identity` action contributes +0.45 to the integrity component and +0.20 to the adaptation component before reward-profile weights are applied. Because the active overwrite record is not cleared after restoration, every later successful restore within the inclusive intervention window sets success again, receives these shaped components again, and overwrites the stored latency. The archived indicator that at least one restoration occurred is unchanged, but the learned restoration policy was trained with repeated shaped reinforcement and cannot be described as emerging independently of this reward-transition coupling. Reporting now treats restoration incidence as evidence of learned action selection under an explicitly engineered reward and repeated-action path, not as an unqualified autonomous recovery mechanism. No run or archived outcome was altered.
