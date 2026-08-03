# Phase III learning-agent core validation report

## Audit status

- Runs: 10,848 across 608 frozen conditions.
- Completed ticks: 4,496,364.
- Resource reconciliations: 10,848/10,848.
- Determinism audit: 192 sampled runs; verified = True.
- Design hash: `b730166499256915d04b737d96d456705ca7843505bee29f37e1ed53bc31cb90`.

## P3-H1 learned control gate

The pooled L3-minus-L0 intention-to-intervene adaptation effect is +0.2867 (95% CI [+0.2692, +0.3042]). The preregistered AIPCW estimate is +0.3625 [+0.3442, +0.3799]. The naïve survivor-only estimate, Lee bounds and positivity diagnostics are preserved in `analysis_summary.json` and are not substituted for the randomized total effect.

## P3-H2 learned path then scarcity

Scarcity minus abundance changes post-freeze attacks by +4.1688 per 1,000 live directed opportunities (95% CI [+3.1509, +5.1868]). The frozen pre-treatment gate values match across paired scarcity assignments to a maximum absolute difference of 0. Among 444 pairs with a pre-evaluation gate, the contrast is +7.7297 [+5.6807, +9.7787]. Architecture/environment-specific estimates are reported in `h2_paired_effects.csv`.

## P3-H4 coordination costs

Protocol maintenance cost 0.12 minus 0.00 changes post-freeze cooperation by -0.2305 [-0.2983, -0.1627]. The visible-versus-hidden threat-signal cost difference-in-differences is -0.1963 [-0.2640, -0.1287]. The dense complementarity quadratic and fitted optimum are reported without replacing failed criteria.

## Scope

These are simulator-internal learning-agent results. They do not establish consciousness, deployed-system behavior or external validity beyond the two abstract transition kernels.
