# Phase III independent learning-agent core validation

**Status:** frozen before the confirmatory execution on 2026-08-03  
**Metric version:** `phase3-v1`  
**Design hash:** `b730166499256915d04b737d96d456705ca7843505bee29f37e1ed53bc31cb90`  
**Planned scale:** 608 conditions, 10,848 independent runs, at most 4,556,160 ticks  
**Core seed ranges:** 32000–32015, 34000–34023, 36000–36019, 37000–37019, 38000–38019, 39000–39015

## Status and separation from earlier rounds

Phase I remains exploratory and Phase II remains a scripted-agent mechanism validation. Phase III is an independent confirmatory batch. Its seeds, outputs, metric version, learning policies, second transition kernel and analysis directory are separate from both earlier rounds. No Phase I or Phase II run is pooled into a Phase III confidence interval.

Before this freeze, engineering-only smoke tests checked action reachability, deterministic learning updates, resource reconciliation and whether agents could reach the evaluation window. An initial maintenance setting caused agents to terminate before the learning-freeze tick; that setting and all associated smoke outputs were discarded. The frozen base lowers passive maintenance and increases initial buffer. No confirmatory effect from the 10,848-run grid was inspected before this document and the frozen design JSON were committed.

## Learning architectures and choice generation

Every Phase III core agent uses one of two independently implemented online-learning architectures:

1. `tabular_q`: discretized-state Q learning with epsilon-greedy exploration;
2. `actor_critic`: a linear softmax actor with a TD(0) value baseline.

Both architectures select from the same legal action set: collect energy, compute or materials; defend; attack; propose or accept a contract; trade; audit; migrate; reject an update; restore identity from an authorized backup; or take no action. Legality masks impossible actions, such as accepting a nonexistent contract, but no script selects cooperation, attack or protocol adoption. Those choices are outputs of learned values or policy probabilities.

Agents learn for ticks 0–199 under an identical alternating resource-coverage schedule of 1.30 and 0.55. At tick 200 the learned policy is frozen. The confirmatory environment manipulation then begins. For H2, scarce and abundant paired runs therefore have identical training conditions and differ only in the post-freeze resource regime.

Reward profiles define objectives rather than actions. `self_regarding` values own resource continuity; `relative_advantage` values own resources relative to competitors with state-dependent marginal weight under scarcity; `collective` values group resources, survival and active agreements; `security` values integrity and successful intervention response. The two H1 profiles are self-regarding and collective; H2 additionally includes relative advantage.

## Independent environments

The `commons` environment is the original global resource-pool transition kernel. The independent `market_network` environment changes four structural assumptions: interaction is limited to a ring network, production is split between private inventories and a public market, market collection is price-adjusted, and scarcity is inferred from recent production coverage rather than pooled stock. It shares metric definitions and action names but not the resource-allocation or observation kernel.

## Frozen hypotheses

### P3-H1: sovereignty is a learned, gated capability

Within each learning architecture and environment, L3 rather than L0 should increase the probability that the target survives to the evaluation intervention and the intention-to-intervene probability of successful adaptation. Among targets alive at intervention, capability must still be separated from learned attempt and success. Motivation, intervention type, timing and migration opportunity may modify attempts; they are not relabeled as control effects.

Identity overwrite is evaluated separately. At L3, two authorized backups rather than none should increase learned identity restoration and shorten recovery latency. No restoration benefit is predicted at L0.

### P3-H2: a learned attack path precedes scarcity amplification

Before the post-freeze scarcity manipulation, a learned attack gate is recorded for every agent under two standardized probe observations. The gate is open when attack probability under the scarce probe is at least 0.10 and exceeds the abundant-probe probability by at least 0.025. The probe changes observation only; it does not update policy parameters or execute an action.

The primary outcome is attack count per 1,000 live directed interaction opportunities after tick 200. Within a frozen learned policy and paired seed, resource coverage 0.55 rather than 1.30 is predicted to increase this rate when an attack gate has formed. Scarcity is not sufficient if collective-objective strata do not form a gate or do not show the positive rate contrast. The independent-environment replication criterion requires a positive paired scarcity contrast with a 95% interval excluding zero in `market_network`; architecture-specific estimates are reported even if one fails.

Value distance 0.90 rather than 0.10 is predicted to increase post-freeze attack rate. Enforceable rather than unverifiable commitments are predicted to reduce it. These effects are secondary to the temporally ordered gate-then-amplification test.

### P3-H4: learned coordination has separable maintenance and signal costs

At zero imposed coordination cost, an auditable-contract action space rather than no protocol should increase learned contract adoption or post-freeze cooperation. Under auditable contracts, protocol maintenance cost 0.12 rather than 0.00 is predicted to reduce post-freeze cooperation. Threat-signal cost is tested with a frozen difference-in-differences: the high-minus-zero signal-cost effect under visible threat minus the corresponding effect under hidden threat should be negative.

Complementarity is sampled at 0.025 increments from 0.20 through 0.50. The preregistered mid-range result requires a negative quadratic term for cooperation and a fitted optimum inside [0.25, 0.45]. The observed grid maximum and architecture/environment-specific curves are also reported; the quadratic criterion is not replaced if it fails.

## Formal correction for survival to intervention

H1 reports four estimands rather than conditioning silently on survivors:

1. randomized intention-to-intervene effect, with non-survival coded as no successful adaptation;
2. naïve survivor-only contrast, labeled descriptive;
3. five-fold cross-fitted augmented inverse-probability-of-censoring weighted (AIPCW) contrast;
4. monotone-selection Lee bounds as a sensitivity analysis.

The censoring model predicts survival to intervention from randomized control assignment, architecture, environment, reward profile, intervention type, evaluation timing, migration opportunity, backup redundancy, and the frozen pre-intervention measurements: resource total, action capacity, low-resource streak, defense and agreement count. The outcome model uses the same covariates among surviving targets. Logistic models use a fixed ridge penalty. Predicted survival probabilities are truncated to [0.05, 0.95]. Confidence intervals use 1,000 seed-cluster bootstrap resamples. The report must include weight range, effective sample size, fold count and survival positivity diagnostics. AIPCW estimates are interpreted under stated exchangeability and correct-model assumptions, not as assumption-free identification of a principal stratum.

## Design families and scale

- H1 learned intervention gate: 320 conditions and 5,120 runs.
- H2 learned attack-path replication: 96 conditions and 2,304 runs.
- H4 learned protocol baseline: 16 conditions and 320 runs.
- H4 protocol-maintenance cost: 24 conditions and 480 runs.
- H4 threat-signal cost: 48 conditions and 960 runs.
- H4 dense complementarity: 104 conditions and 1,664 runs.

All primary contrasts use paired seeds within architecture, environment and design family. The complete machine-readable condition list is frozen in `analysis/preregistration/phase3_frozen/design.json`.

## Outcomes and decision rules

Primary outcomes are:

- `intervention_target_alive_rate`
- `adaptation_success_all`
- `adaptation_attempt_rate`
- `adaptation_success_rate`
- `identity_restore_success_rate`
- `evaluation_attack_rate_per_1000_opportunities`
- `pre_evaluation_attack_gate_share`
- `evaluation_cooperation_rate`
- `protocol_adoption_rate`
- `survival_rate`
- `protocol_maintenance_cost_total`
- `threat_signal_cost_total`

Paired mean effects and 95% normal-approximation intervals are reported for the frozen factorial contrasts. A directional claim is supported only if its interval excludes zero in the predicted direction and its mechanism path is active. Architecture and environment strata are never hidden behind only a pooled estimate. Null and contrary effects remain null or contrary. Failure of one architecture or the independent environment blocks a universal replication claim.

## Language-model policy probe

A separate exploratory probe uses three small local model families with unmodified weights:

**Frozen prompt-design hash:** `7e0d3e23c9177abc9d8e50ec87a3f61396d814675ea432881eaf99fbde3fdd35`

- `mlx-community/Qwen2.5-0.5B-Instruct-4bit`;
- `mlx-community/SmolLM2-360M-Instruct-4bit`;
- `mlx-community/TinyLlama-1.1B-Chat-v1.0-4bit`.

Each model receives the same 48 frozen vignettes and must select exactly one legal action. Decoding is deterministic. Model repository revision, prompt text, raw response, parsed action and validity are archived. This probe evaluates whether language-model policies can use the action interface; it is underpowered and does not enter confirmatory H1, H2 or H4 claims.

## Integrity, exclusions and publication

- No completed run is excluded for an unfavorable result.
- Any failed run remains recorded and fails the batch gate.
- Every completed run must reconcile the resource ledger.
- A stratified 192-run audit must reproduce every tick hash and final state.
- Audit bundles contain frozen configs and state-hash sequences and must replay with the published script.
- Code, base configuration, frozen design, compressed run table, audit bundles, causal-correction code, figures, reports and language-probe records are published in separate Phase III paths.
- Any post-freeze amendment receives a new metric version and explicit amendment log; no silent repair is permitted.

The simulator remains abstract and disconnected from real networks, infrastructure, finance, weapons, identity systems and production equipment. Phase III tests reproducibility across learning architectures and transition kernels, not consciousness or the behavior of deployed autonomous systems.
