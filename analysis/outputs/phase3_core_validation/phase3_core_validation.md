# Phase III learning-agent core validation report

## Audit status

- Runs: 10,848 across 608 frozen conditions.
- Completed ticks: 4,496,364.
- Resource reconciliations: 10,848/10,848.
- Determinism audit: 192 sampled runs; verified = True.
- Design hash: `b730166499256915d04b737d96d456705ca7843505bee29f37e1ed53bc31cb90`.

The 192-bundle replay verifies complete per-tick state-hash sequences, bundle trajectory digests, terminal states, tick counts and resource ledgers. The 10,848-run summary table was produced without per-tick trajectory hashing; its historically named `event_hash` digests only the final state-hash list element and is intentionally not compared with the bundle trajectory digest.

## P3-H1 control and intervention response

The pooled L3-minus-L0 all-assigned factorial adaptation effect is +0.2867 (95% CI [+0.2692, +0.3042]). A manuscript-stage audit found that the takeover-attempt stratum contributes an automatic L3 transition-rule success of +1.0000 rather than a learned response. Excluding that stratum, the post hoc contrast is +0.1084 [+0.0949, +0.1219]. The common-numeric-seed survivor subset contains 748 L0/L3 pairs and has a descriptive contrast of +0.2714 [+0.2395, +0.3033]; initialization consumes different random draws by control level, so this is not an identical-shock or principal-stratum causal estimate. Intervention-specific and seed-cluster results are in `mechanism_audit.csv`. The precommitted AIPCW estimate is +0.3625 [+0.3442, +0.3799], but severe positivity limitations and wide Lee bounds prevent it from replacing the all-assigned factorial effect.

The prospectively specified L3-only backup contrast is +0.7266 [+0.6719, +0.7813] for identity restoration. The original pooled L0/L3 output of +0.3633 is retained in `identity_backup_effects.csv` for provenance but is not the specified L3 estimand.

Identity overwrite is applied before the learner's per-action reward snapshot, so its positive identity-version change is not seen by the integrity-delta penalty. Successful restoration supplies positive integrity and adaptation reward components, and the still-active overwrite allows those components to recur on repeated restores. The incidence result is therefore a learned choice under explicit reward and transition shaping, not an unqualified autonomous-recovery result; the archived timing field records the last successful restore in the window.

## P3-H2 evaluation-coverage divergence after policy freeze

Continued-low coverage (0.55) minus restored-high coverage (1.30) changes post-freeze attacks by +4.1688 per 1,000 live directed opportunities (95% CI [+3.1509, +5.1868]). Both arms had repeatedly experienced low coverage during the alternating training schedule, whose final tick-180–199 block was low; the evaluation regimes diverged only after the tick-200 policy freeze. The coverage switch rescales node yields and shared energy/compute stocks and also resets the market variant's supply moving average, so this is a compound regime contrast rather than a first-onset or pure-flow scarcity shock. The frozen pre-evaluation gate values match across paired evaluation assignments to a maximum absolute difference of 0. Among 444 gate-positive pairs, the contrast is +7.7297 [+5.6807, +9.7787], but every gate-positive pair uses tabular Q learning. The 708 gate-closed pairs still show +1.9358 [+0.9233, +2.9482]. The gate threshold is therefore a tabular-Q marker of a larger contrast, not a necessary or architecture-general condition. Architecture/environment-specific estimates are reported in `h2_paired_effects.csv`; the composition audit is in `mechanism_audit.csv`.

## P3-H4 coordination costs

Protocol maintenance cost 0.12 minus 0.00 changes evaluation-period cooperation by -0.2305 [-0.2983, -0.1627]. The visible-versus-hidden threat-signal cost difference-in-differences is -0.1963 [-0.2640, -0.1287]. Cost levels are active and observable during both training and evaluation, so these are total regime effects rather than isolated post-freeze debit effects. The dense complementarity quadratic and fitted optimum are reported without replacing failed criteria.

## Scope

These are simulator-internal learning-agent results. The market-network model is a structurally distinct transition variant implemented within the shared simulator engine, not an independently authored codebase. The results do not establish consciousness, deployed-system behavior or external validity beyond the two abstract variants.
