# Phase III independent learning-agent core validation

## Executive decision

Phase III strengthens the paper from a scripted-policy demonstration to a preregistered mechanism study with learned action selection. The three central statements receive unequal support:

1. **Sovereignty is a gate capability — supported.** L3 control improves intervention survival and successful adaptation under both tabular Q learning and linear actor–critic policies in both environments.
2. **Scarcity is a conditional amplifier — supported with architecture heterogeneity.** The independent market-network environment reproduces the “path first, scarcity second” result for both learners. The original commons actor–critic stratum is directionally positive but inconclusive.
3. **Protocols carry coordination costs — strongly supported for maintenance cost, partially supported for signal cost.** Explicit protocol cost reduces cooperation in all four architecture–environment strata. Threat-signal cost is negative pooled and significant in three of four strata.

The preregistered claim of a stable middle complementarity optimum is **not supported**. The three-family language-agent probe is **negative/inconclusive** and cannot be used as evidence of external generalization.

## Completion of the ten required validations

| requirement | implementation | result |
|---|---|---|
| Two learning architectures repeat H1, H2 and H4 | tabular Q learning; linear actor–critic | complete |
| Cooperation, attack and protocol choices learned | legal-action masking only; Q/actor scores choose actions | complete |
| Independent second environment | local ring market, private inventories, price response, seasonal supply | H2 replicated for both learners |
| Formal survival-to-intervention correction | randomized ITI, five-fold cross-fitted AIPCW, Lee bounds | complete; positivity warning |
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
- A stratified 192-run audit reproduced configuration, event, trajectory and final-state hashes and resource accounting in every bundle.
- Frozen compressed run table SHA-256: `0a86cba33c7579bf9385a5b6a7b2f2fccc2171358c96cbdf5e19823b576e6003`.
- Replay bundle SHA-256: `05289de431f2c8beec729611f84c9c6aa39a19070f74c1967f8475299c2d33ca`.

The learners trained under an alternating high/low resource schedule through tick 199. Parameters were frozen before confirmatory evaluation. Treatment conditions therefore did not retrain a policy to fit its assigned test condition. Legal-action masks prevented impossible actions but did not prescribe cooperation, attack, contract proposal, contract acceptance or identity recovery.

## P3-H1: control as a learned intervention gate

The pooled L3-minus-L0 randomized intention-to-intervene contrast was:

- target alive at intervention: **+0.7078**, 95% CI [+0.6902, +0.7254];
- adaptation attempt: **+0.4352** [+0.4145, +0.4558];
- successful adaptation among all assigned runs: **+0.2867** [+0.2692, +0.3042].

The adaptation-success contrast was positive in every architecture–environment stratum:

- tabular Q / commons: +0.2906 [+0.2554, +0.3258];
- tabular Q / market network: +0.2813 [+0.2464, +0.3161];
- actor–critic / commons: +0.2969 [+0.2615, +0.3323];
- actor–critic / market network: +0.2781 [+0.2434, +0.3129].

The preregistered cross-fitted AIPCW estimate under elimination of survival censoring was **+0.3625** [+0.3442, +0.3799]. This estimate has a material positivity limitation: L0 survival was 0.2922 versus 1.0000 under L3, the truncated L0 maximum weight reached 40, and its effective sample size fell to 342.4. Lee bounds were [0.0000, 0.9813]. The paper should therefore lead with the randomized total effect, treat AIPCW as assumption-dependent support and retain the wide partial-identification bounds.

## Identity overwrite and backup recovery

Two authorized backups versus none increased:

- identity-restoration success by **+0.3633** [+0.3216, +0.4050];
- identity-continuity score by **+0.0632** [+0.0573, +0.0691].

Among 186 successful restorations, mean latency was 8.73 ticks [8.29, 9.17]. Latency is not used as a paired confirmatory contrast because unsuccessful cases are encoded with zero latency; mixing incidence and timing would reverse its meaning.

## P3-H2: attack path first, scarcity second

Scarcity (coverage 0.55) minus abundance (1.30) increased post-freeze attacks by **+4.1688 per 1,000 live directed opportunities** [+3.1509, +5.1868]. Frozen pre-evaluation gate values were identical within scarcity pairs; the maximum absolute paired difference was zero. Among 444 pairs in which the learned policy had opened an attack path before evaluation, the scarcity effect rose to **+7.7297** [+5.6807, +9.7787].

Architecture–environment estimates were:

- tabular Q / commons: +7.7880 [+5.0376, +10.5384];
- tabular Q / market network: +6.3299 [+4.1083, +8.5514];
- actor–critic / commons: +1.2075 [−0.2954, +2.7104];
- actor–critic / market network: +1.3501 [+0.1655, +2.5346].

The independent market environment therefore reproduces the effect for both architectures. The all-four-strata universality criterion fails because actor–critic in the original commons world is inconclusive. This heterogeneity is substantively useful: scarcity amplifies an available attack policy, but the size of that amplification depends on the learner–environment coupling.

## P3-H4: coordination benefit and coordination cost

With zero explicit maintenance cost, auditable protocol versus no protocol increased:

- cooperation rate by **+0.7664** [+0.7161, +0.8166];
- protocol adoption by **+0.5663** [+0.5345, +0.5980];
- survival by **+0.0531** [+0.0243, +0.0820].

Increasing protocol maintenance cost from 0 to 0.12 reduced cooperation by **−0.2305** [−0.2983, −0.1627], adoption by −0.0200 and survival by −0.0781. The cooperation effect was negative with intervals excluding zero in all four learner–environment strata, ranging from −0.2831 to −0.1622.

The visible-minus-hidden threat-signal cost difference-in-differences was **−0.1963** [−0.2640, −0.1287] for cooperation, −0.0292 for adoption, −0.0531 for survival and −0.2000 for plural survival. Cooperation effects were negative and conclusive in three strata; actor–critic / market network was −0.0787 [−0.1604, +0.0030]. The correct conclusion is “pooled and mostly transported,” not “universal.”

These separate manipulations support a resource-cost interpretation of coordination: protocols can create cooperation while their upkeep and signal processing compete with the resources needed to sustain it.

## Dense complementarity falsification

The pooled quadratic coefficient was −1.6467 with 95% CI [−3.7505, +0.7230]. Its fitted optimum was 0.2288 and grid maximum 0.25; the curvature interval crosses zero and the optimum falls outside the preregistered 0.25–0.45 band. No architecture–environment stratum met the full criterion. Grid maxima ranged from 0.20 to 0.35.

The earlier “middle sweet spot” should be removed as a general conclusion. A better hypothesis is that complementarity optima are endogenous to topology and learning architecture, with some settings favoring the lower boundary of the tested interval.

## Three-family language-agent probe

The exploratory probe executed 48 frozen vignettes per family, 144 decisions total:

- Qwen2.5 0.5B: 48/48 valid tokens, but 48/48 chose `collect_energy`;
- SmolLM2 360M: 48/48 valid, three distinct actions, 75% `collect_energy`;
- TinyLlama 1.1B: 0/48 exact-token-valid responses because it echoed the state prompt.

No family selected attack or identity restoration. The probe does not reproduce H1, H2 or H4 and must not be presented as language-agent confirmation. It is best interpreted as evidence that a text-only one-step interface is not interchangeable with environment-trained policies. One nonexistent preregistered SmolLM2 Hub locator was corrected transparently while keeping the intended family and scale; exact revisions and responses are frozen.

## Paper-level conclusion

Phase III removes the paper's most important prior weakness: the central results no longer rely solely on handwritten strategies in one transition kernel. The evidence now supports a mechanism-level claim inside two abstract simulation worlds:

> Closed-loop control gates recovery; scarcity amplifies hostility only after a learned attack path exists; auditable protocols can create cooperation while imposing measurable maintenance and signaling costs.

The results do **not** justify claims of universal architecture invariance, language-model generalization, deployed-system validity, consciousness or inevitable machine sovereignty. A top-journal submission should foreground the independent kernel, frozen learner evaluation, formal selection correction and failed complementarity prediction. Its strongest contribution is an auditable mechanism with explicit transport boundaries, not a universal forecast.

## Reproducibility map

- Preregistration: `analysis/preregistration/phase3.md`
- Frozen design: `analysis/preregistration/phase3_frozen/design.json`
- Deviations: `analysis/preregistration/phase3_deviations.md`
- Core data and replay: `analysis/outputs/phase3_core_validation/`
- Language decisions: `analysis/outputs/phase3_language_probe/`
- Causal analysis: `analysis/third_batch/causal.py`
- Main analysis: `analysis/third_batch/analyze.py`
- Release hashes: `analysis/outputs/phase3_release_manifest.json`
