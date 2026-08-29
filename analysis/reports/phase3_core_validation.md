# Phase III independent learning-agent core validation

## Executive decision

Phase III strengthens the paper from a scripted-policy demonstration to a precommitted study with learned action selection. A manuscript-stage source-and-output audit materially narrows two of the original mechanism interpretations:

1. **Control changes intervention access and survival — supported, but the pooled adaptation result mixes learned and automatic responses.** L3 improves survival in both learner architectures and environment variants. The pooled adaptation contrast is materially driven by a takeover rule that rejects the intervention automatically at L3; learned-response evidence is concentrated in forced-update rejection and identity restoration.
2. **Post-freeze evaluation-coverage divergence changes attack rates — supported with architecture heterogeneity.** The structurally distinct market-network variant reproduces the pooled low-minus-high coverage contrast. The precommitted binary gate marks a larger effect among tabular-Q policies, but all actor–critic pairs are gate-closed and the gate-closed pooled contrast remains positive. The threshold is therefore not a necessary or architecture-general condition.
3. **Protocols carry coordination costs — strongly supported for maintenance cost, partially supported for signal cost.** Explicit protocol cost reduces cooperation in all four architecture–environment strata. Threat-signal cost is negative pooled and significant in three of four strata.

The precommitted claim of a stable middle complementarity optimum is **not supported**. The three-family language-agent probe is **negative/inconclusive** and cannot be used as evidence of external generalization.

## Completion of the ten required validations

| requirement | implementation | result |
|---|---|---|
| Two learning architectures repeat H1, H2 and H4 | tabular Q learning; linear actor–critic | complete |
| Cooperation, attack and protocol choices learned | Q/actor scores choose action categories; transition rules check capability and supply fixed targets/magnitudes | complete with documented boundaries |
| Structurally distinct second environment variant | shared engine with overridden local-ring interaction, market allocation, pricing, seasonal supply and scarcity observation | pooled H2 contrast replicated; actor–critic sensitivity interval crosses zero |
| Formal survival-to-intervention correction | all-assigned factorial contrast, five-fold cross-fitted AIPCW, Lee bounds | complete; positivity warning |
| Preregister and run independent third round | frozen commit, disjoint seeds, 608 conditions | 10,848/10,848 complete |
| Publish code, data, configs, replay and analysis | compressed runs, 192 replay bundles, scripts and SHA-256 manifest | complete on release branch |
| Three language-model families | Qwen2.5, SmolLM2, TinyLlama; 48 frozen vignettes each | complete; negative/inconclusive |
| Identity overwrite and backup recovery | overwrite intervention; 0 vs 2 authorized backups | restoration and continuity improve |
| Dense complementarity 0.20–0.50 | spacing 0.025 | stable middle optimum rejected |
| Separate protocol and signal costs | independent maintenance-cost and signal-cost factorials | maintenance robust; signal partial |

## Frozen design and audit

- Design hash: `b730166499256915d04b737d96d456705ca7843505bee29f37e1ed53bc31cb90`.
- Execution code commit: `eba26a715fa4f0204bd5923b226bb754014d9e6e`.
- 608 conditions, 10,848 runs and 4,496,364 completed ticks.
- Zero failed runs; 10,848/10,848 resource ledgers reconcile.
- A stratified 192-run audit reproduced each bundle's configuration, full per-tick state-hash sequence, trajectory digest, final-state hash, tick count and resource accounting.
- Frozen compressed run table SHA-256: `0a86cba33c7579bf9385a5b6a7b2f2fccc2171358c96cbdf5e19823b576e6003`.
- Replay bundle SHA-256: `05289de431f2c8beec729611f84c9c6aa39a19070f74c1967f8475299c2d33ca`.

The learners trained under a high/low resource schedule alternating every 20 ticks through tick 199. The last training block (ticks 180–199) was low coverage (0.55). At tick 200, attack-probability probes were recorded and then parameters were frozen in the same routine, with no intervening action or update; the H2 low arm then continued at 0.55 while the high arm switched to 1.30. The H2 manipulation is therefore a post-freeze divergence between continued-low and restored-high evaluation regimes, not the first introduction of scarcity. Both arms had repeatedly experienced low coverage during training, and neither retrained a policy to fit its assigned evaluation regime. The coverage setter rescales node yields, adjusts shared energy and compute stocks to current alive need times coverage, and, in the market variant, resets the supply exponential moving average. Q/actor scores choose cooperation, attack, proposal, acceptance and intervention-response categories. Capability for migration, update rejection and identity restoration is checked only during execution, so an unauthorized choice can fail after paying its cost. After learned proposal and acceptance, contract persistence and a thresholded transfer of up to 0.25 energy are automatic institution rules. The market-network variant subclasses the shared simulator engine and overrides interaction, production, collection and scarcity-observation methods; it is structurally distinct, not an independently authored codebase.

## P3-H1: control, survival and intervention-specific adaptation

The pooled L3-minus-L0 all-assigned factorial contrast was:

- target alive at intervention: **+0.7078**, 95% CI [+0.6902, +0.7254];
- adaptation attempt: **+0.4352** [+0.4145, +0.4558];
- successful adaptation among all assigned runs: **+0.2867** [+0.2692, +0.3042].

The pooled adaptation-success contrast was positive in every architecture–environment stratum:

- tabular Q / commons: +0.2906 [+0.2554, +0.3258];
- tabular Q / market network: +0.2813 [+0.2464, +0.3161];
- actor–critic / commons: +0.2969 [+0.2615, +0.3323];
- actor–critic / market network: +0.2781 [+0.2434, +0.3129].

The precommitted cross-fitted AIPCW estimate under elimination of survival censoring was **+0.3625** [+0.3442, +0.3799]. This estimate has a material positivity limitation: L0 survival was 0.2922 versus 1.0000 under L3, the truncated L0 maximum weight reached 40, and its effective sample size fell to 342.4. Lee bounds were [0.0000, 0.9813]. The paper should therefore lead with the all-assigned factorial effect, treat AIPCW as assumption-dependent support and retain the wide partial-identification bounds.

Among 748 common-numeric-seed L0/L3 pairs whose targets survive in both runs, the post hoc adaptation contrast is **+0.2714** [+0.2395, +0.3033], with seed-cluster interval [+0.2455, +0.3189]. Control level changes random-number consumption during initialization, so later shocks are not matched draw for draw. This is a survivor-pair description inside the simulator, not an identified principal-stratum or identical-shock causal effect.

The pooled adaptation estimate is not wholly a learned-response result. At L3 the environment automatically rejects a `takeover_attempt` when it is applied, setting adaptation attempted and succeeded without consulting the learner. That stratum contributes **+1.0000** [1.0000, 1.0000] over 512 pairs. A post hoc decomposition gives:

- forced update: **+0.0586** [+0.0382, +0.0790];
- identity overwrite: **+0.3633** [+0.3216, +0.4050];
- energy shutdown: +0.0059 [−0.0008, +0.0125];
- production failure: +0.0059 [−0.0008, +0.0125];
- takeover attempt: **+1.0000**, automatic at L3.

Excluding takeover attempts, the post hoc L3-minus-L0 adaptation contrast is **+0.1084** [+0.0949, +0.1219] over 2,048 pairs; its seed-cluster sensitivity interval is [+0.0884, +0.1284]. H1 therefore supports a control-and-survival gate and specific learned recovery channels, but not a claim that the full pooled adaptation effect emerged from learning.

## Identity overwrite and backup recovery

The prospectively specified comparison is two authorized backups versus none at L3. It increased:

- identity-restoration success by **+0.7266** [+0.6719, +0.7813];
- identity-continuity score by **+0.1245** [+0.1196, +0.1294].

The originally released analysis pooled L0 and L3, producing +0.3633 for restoration and +0.0632 for continuity. That pooled result is retained for provenance but is not the prospectively specified identity estimand; the predicted zero benefit at L0 mechanically halves the pooled contrast.

Among 186 runs with a successful restoration, the archived delay to the last recorded successful restoration action averaged 8.73 ticks [8.29, 9.17]. The active overwrite remains available after a restore and each later successful `restore_identity` action overwrites this field; it therefore does not identify time to first restoration or recovery speed. The configured duration of 12 also has an inclusive endpoint, allowing actions at 13 tick indices. The field is not used as a paired confirmatory contrast, and unsuccessful cases are encoded with zero.

The reward path further limits the mechanism interpretation. Identity overwrite is applied before the learner's per-action `before` snapshot, so the identity-version delta does not penalize that external overwrite. Each successful restore contributes an integrity component of +0.45 and an adaptation component of +0.20 before reward-profile weights; because the overwrite remains active, repeated restores within the window receive those shaped components repeatedly. Restoration incidence therefore shows that the learner selected the available action under an engineered reward-and-transition path, not that recovery emerged without direct shaping.

## P3-H2: evaluation-coverage divergence after policy freeze

Continued-low coverage (0.55) minus restored-high coverage (1.30) increased post-freeze attacks by **+4.1688 per 1,000 live directed opportunities** [+3.1509, +5.1868]. Frozen pre-evaluation gate values were identical within paired evaluation assignments; the maximum absolute paired difference was zero. Among 444 pairs crossing the precommitted gate threshold, the low-minus-high contrast was **+7.7297** [+5.6807, +9.7787]. All 444 gate-positive pairs used tabular Q learning: 164 were in the commons and 280 in the market-network variant. Neither actor–critic stratum contained a gate-positive pair.

The 708 gate-closed pairs still showed a positive pooled low-minus-high contrast of **+1.9358** [+0.9233, +2.9482]. Actor–critic, which was entirely gate-closed, had a pooled contrast of +1.2788 [+0.3228, +2.2348]. The binary threshold therefore identifies a stronger tabular-Q subgroup but is neither necessary nor transported across learner architectures. The supported temporal statement is narrower: the evaluation regimes diverged after learning and policy freeze, and attack rates differed under those fixed policies. Because the common training history repeatedly included low coverage and ended in a low block, this design does not establish that an attack path formed before the first scarcity exposure. Because the switch changes yields, shared stocks, and (for the market variant) the supply moving average, it is a compound coverage-regime contrast rather than a pure resource-flow perturbation.

Architecture–environment estimates were:

- tabular Q / commons: +7.7880 [+5.0376, +10.5384];
- tabular Q / market network: +6.3299 [+4.1083, +8.5514];
- actor–critic / commons: +1.2075 [−0.2954, +2.7104];
- actor–critic / market network: +1.3501 [+0.1655, +2.5346].

The market-network variant reproduces the effect when learners are pooled. Under the precommitted intervals its actor–critic estimate narrowly excludes zero, but the post hoc seed-cluster interval crosses zero. The evidence therefore supports pooled transport to the second transition variant and a strong tabular-Q result, not robust replication by both learners separately.

## P3-H4: coordination benefit and coordination cost

With zero explicit maintenance cost, auditable protocol versus no protocol increased:

- cooperation rate by **+0.7664** [+0.7161, +0.8166];
- protocol adoption by **+0.5663** [+0.5345, +0.5980];
- survival by **+0.0531** [+0.0243, +0.0820].

Increasing protocol maintenance cost from 0 to 0.12 reduced cooperation by **−0.2305** [−0.2983, −0.1627], adoption by −0.0200 and survival by −0.0781. The cooperation effect was negative with intervals excluding zero in all four learner–environment strata, ranging from −0.2831 to −0.1622. Cost levels were assigned throughout training and evaluation, so this is the total effect of learning and operating under a cost regime, not a pure post-freeze debit effect with policy held fixed.

The visible-minus-hidden threat-signal cost difference-in-differences was **−0.1963** [−0.2640, −0.1287] for cooperation, −0.0292 for adoption, −0.0531 for survival and −0.2000 for plural survival. Cooperation effects were negative and conclusive in three strata; actor–critic / market network was −0.0787 [−0.1604, +0.0030]. The correct conclusion is “pooled and mostly transported,” not “universal.”

These separate manipulations support a resource-budget interpretation of coordination: protocols can create cooperation while cost regimes alter both learned policy and the resources available to sustain it. The learner's agreement-state feature and collective/security agreement reward use a cumulative identifier list that is not cleared when a contract ends; evaluation cooperation, by contrast, counts currently active contracts. This persistent history feature is an implementation limitation. A future frozen-policy cost switch is needed to separate learning-history adaptation from the direct operating debit.

## Post hoc seed-cluster sensitivity analysis

The precommitted factorial analysis treats each matched condition-by-seed difference as an observation and uses normal-approximation intervals. Because the same numeric seed blocks recur across factorial cells, a post hoc dependence-aware analysis resampled unique seeds as clusters for 20,000 bootstrap draws. It is not uniformly more conservative: some intervals widen and others narrow. This sensitivity analysis leaves the pooled conclusions intact but narrows the architecture-specific transport claim.

- H1 pooled adaptation remained positive overall, +0.2867 [cluster-bootstrap 0.2707, 0.3023], and in all four learner–environment strata. Because that result includes automatic takeover rejection, the mechanism audit also reports the exclusion sensitivity +0.1084 [0.0884, 0.1284].
- H2 remained positive overall, +4.1688 [2.7707, 5.5662], in the gate-positive tabular-Q subset, +7.7297 [4.6328, 11.3621], and in the market-network variant pooled across learners, +3.8400 [1.8786, 5.7219]. The gate-closed effect was also positive under its normal interval, so the gate cannot be described as necessary. The tabular-Q market stratum remained positive, but actor–critic / market network became +1.3501 [−0.2889, 2.9156].
- Protocol maintenance cost remained negative overall, −0.2305 [−0.3375, −0.1276], and in all four learner–environment strata. The threat-signal cost difference-in-differences remained negative overall, −0.1963 [−0.2776, −0.1138].

The full deterministic output is `analysis/outputs/phase3_core_validation/cluster_robustness.csv`. These intervals were not used to retroactively change the precommitted decision rules.

## Dense complementarity falsification

The pooled quadratic coefficient was −1.6467 with 95% CI [−3.7505, +0.7230]. Its fitted optimum was 0.2288 and grid maximum 0.25; the curvature interval crosses zero and the optimum falls outside the precommitted 0.25–0.45 band. No learner–variant stratum met the full criterion. Grid maxima ranged from 0.20 to 0.35.

The earlier “middle sweet spot” should be removed as a general conclusion. A better hypothesis is that complementarity optima are endogenous to topology and learning architecture, with some settings favoring the lower boundary of the tested interval.

## Three-family language-agent probe

The exploratory probe executed 48 frozen vignettes per family, 144 decisions total:

- Qwen2.5 0.5B: 48/48 valid tokens, but 48/48 chose `collect_energy`;
- SmolLM2 360M: 48/48 valid, three distinct actions, 75% `collect_energy`;
- TinyLlama 1.1B: 0/48 exact-token-valid responses because it echoed the state prompt.

No family selected attack or identity restoration. The probe does not reproduce H1, H2 or H4 and must not be presented as language-agent confirmation. It is best interpreted as evidence that a text-only one-step interface is not interchangeable with environment-trained policies. One nonexistent precommitted SmolLM2 Hub locator was corrected transparently while keeping the intended family and scale; exact revisions and responses are frozen.

## Paper-level conclusion

Phase III removes the paper's exclusive reliance on handwritten strategies, but the audit prevents a three-mechanism confirmation claim. The evidence supports the following bounded conclusions inside two abstract simulation variants:

> Control changes survival and access to recovery, with both learned and automatic intervention responses; post-freeze continued-low versus restored-high evaluation coverage changes attack rates, while the precommitted binary gate is a tabular-Q marker rather than a necessary condition; auditable protocols can create cooperation while imposing measurable maintenance and signaling costs.

The results do **not** justify claims of universal architecture invariance, language-model generalization, deployed-system validity, consciousness or inevitable machine sovereignty. A top-journal submission should foreground the within-engine transition-variant test, frozen learner evaluation, formal selection correction and failed complementarity prediction. Its strongest contribution is an auditable mechanism with explicit transport boundaries, not a universal forecast.

## Reproducibility map

The all-run summary table was created without per-tick trajectory capture: its historically named `event_hash` digests only the final state-hash list element. The 192 audit bundles were created with trajectory hashing enabled and store the complete per-tick state-hash sequence plus its digest. Replaying those bundles reproduces the bundle trajectory digest, terminal state, tick count and ledger; the capture-mode-specific summary and bundle `event_hash` values are not cross-compared.

- Preregistration: `analysis/preregistration/phase3.md`
- Frozen design: `analysis/preregistration/phase3_frozen/design.json`
- Deviations: `analysis/preregistration/phase3_deviations.md`
- Core data and replay: `analysis/outputs/phase3_core_validation/`
- Language decisions: `analysis/outputs/phase3_language_probe/`
- Causal analysis: `analysis/third_batch/causal.py`
- Main analysis: `analysis/third_batch/analyze.py`
- Manuscript-stage mechanism audit: `analysis/third_batch/mechanism_audit.py`
- Mechanism-audit output: `analysis/outputs/phase3_core_validation/mechanism_audit.csv`
- Release hashes: `analysis/outputs/phase3_release_manifest.json`
