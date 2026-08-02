# Phase II second-batch mechanism-validation readout

**Status:** completed mechanism-validation batch<br>
**Completed:** 2026-08-02<br>
**Scale:** 22,704 independent runs across 1,926 conditions; 7,562,067 completed ticks

## Decision

Revise the paper before launching a third batch. Phase II supports the paper's narrower architecture, but it also changes the hostility mechanism and rejects two coordination expectations. The strongest defensible account is now:

- closed-loop control is a gated capability, not behavior by itself;
- scarcity is insufficient across policy families, but it is an exposure-adjusted attack-rate amplifier once an attack-capable policy exists;
- value distance, attack-capable policy, and commitment verifiability jointly explain a meaningful part of hostility;
- production concentration continuously erodes plural coexistence;
- thin protocols sustain relationships without improving survival in this implementation;
- visible threat and extreme complementarity can impose coordination costs.

All 22,704 runs completed and reconciled their resource ledgers. No run failed. A stratified 192-run audit reproduced every sampled tick hash and final state.

## Design and integrity gates

| Family | Conditions | Runs | Purpose |
| --- | ---: | ---: | --- |
| OAT calibration | 66 | 1,584 | Continuous dose response and inactive-path audit |
| H1 intervention decomposition | 540 | 6,480 | Control × target policy × timing × migration opportunity × intervention |
| H2 exposure-adjusted hostility | 720 | 8,640 | Scarcity × value distance × concentration × verifiability × policy |
| H4 protocol/signal/convergence | 600 | 6,000 | Complementarity × threat × visibility × protocol × updating |
| **Total** | **1,926** | **22,704** | Frozen Phase II mechanism-validation batch |

The reported design hash is `04e72ee1ffca8446887a97b8b2723e45562791f6fd3f6016fd081330dd3d6ee5`. The compressed run table hash is `b755caad5c21f11708b3cb9fc73da6eb1c935cb345027ac245237fe5d6f96526`.

## Transparent pre-report amendment

The first end-to-end Phase II execution exposed a structurally unreachable post-conflict outcome: the proposed metric required a new attack after a low-scarcity quiet interval, while the attack-capable policy initiates attacks only above its scarcity threshold. That execution was marked invalid, archived outside the reported output, and is not used below.

Before the reported run, metric version `phase2-v2` redefined post-conflict persistence as the share of attacked directed pairs that resume attacking after at least 12 quiet ticks. A unit test establishes reachability. Conditions, seed blocks, hypotheses, and all other outcomes were unchanged. In the reported batch the metric is non-zero in roughly 0.5% of runs, so recurrence is empirically rare rather than structurally impossible.

## Hypothesis assessment

| Hypothesis | Phase II status | Primary evidence | Interpretation |
| --- | --- | --- | --- |
| R2-H1 — gated control | Supported as a gate | L3−L0 target alive +0.9444; adaptation success +0.5556 | Control supplies capability, while survival to treatment, policy motive, intervention type, and opportunity determine expression. |
| R2-H2 — conditional hostility | Revised and partially supported | Scarcity−abundance +1.988 attacks/1,000 opportunities overall; +7.057 in opportunistic policies; exactly 0 in cooperative policies | Scarcity is not sufficient, but it conditionally amplifies attacks after exposure adjustment. |
| R2-H3 — functional sufficiency | Compatible simulator demonstration | Scripted non-conscious policies reproduce the modeled patterns | This is not evidence about consciousness or external validity. |
| R2-H4 — operational consensus | Mixed | Auditable−none cooperation +74.915; survival −0.0100; visible−hidden cooperation −10.585 | Protocol continuity is supported; survival benefit and visible-threat benefit are rejected. |

## R2-H1: capability, motive, survival, and opportunity

L3 relative to L0 increases target survival to the intervention by **+0.9444** (95% CI [0.9333, 0.9556]) and adaptation success by **+0.5556** [0.5314, 0.5798]. A security target attempts adaptation **+0.3528** [0.3326, 0.3729] more often than a cooperative target. Making a migration opportunity certain rather than absent raises adaptation success by **+0.0889** [0.0769, 0.1009].

The result supports the capability claim but rules out a simple monotonic behavioral reading. Much of the apparent control effect is survival-to-treatment selection: low-control targets often disappear before the intervention. Adaptation should therefore be reported as a sequence of gates, not a single outcome.

## R2-H2: scarcity is an amplifier, not a generator

After normalizing by live directed pair-opportunities, scarcity (coverage 0.55 versus 1.30) raises attack intensity by **+1.9880** per 1,000 opportunities [1.4931, 2.4830]. The effect is **+7.0571** [5.1483, 8.9658] within opportunistic policies and exactly **0** within cooperative policies. Scarcity therefore does not create attacks where the policy lacks an attack path.

The other components move in the predicted directions. High versus low value distance raises attack rate by **+6.5143** [6.0836, 6.9449]. Enforceable versus unverifiable commitments reduce it by **−5.6355** [−6.0152, −5.2557]. High versus low production concentration reduces plural survival by **−0.1956** [−0.2175, −0.1737]. At concentration 0.9, 66.49% of runs end with one survivor and 16.84% with common collapse.

This partially rehabilitates the compound hostility mechanism after Phase I. The supported mechanism is not “scarcity causes hostility,” but “attack-capable policy opens the path; scarcity increases the rate; value distance increases incentives; verifiability suppresses opportunism.”

## R2-H4: continuity without resilience

Auditable contracts extend cooperation by **+74.915** rounds [66.831, 82.999] relative to no protocol, but reduce survival by **−0.0100** [−0.0135, −0.0065]. The effect is small but its interval excludes zero, so the paper should not describe survival as unchanged.

Contrary to the preregistered direction, visible versus hidden threat reduces cooperation by **−10.585** rounds [−12.760, −8.410] and protocol adoption by **−0.00267** [−0.00313, −0.00220]. Optional objective updating raises value convergence by **+0.03015** [0.02745, 0.03285] within alignment-capable protocols. High versus low complementarity reduces cooperation by **−51.453** [−57.810, −45.095], while the observed cooperation optimum occurs at complementarity 0.3.

## Six new possibilities

1. **Scarcity as a conditional rate amplifier.** Scarcity changes the intensity of an existing attack path, not the existence of that path.
2. **Continuous plurality erosion.** Concentration replaces some common-collapse outcomes with a dominant single survivor; aggregate survival can conceal loss of plurality.
3. **Coordination-signal tax.** Visible threat can trigger costly coordination behavior that competes with maintenance and shortens realized cooperation.
4. **Complementarity sweet spot.** Moderate specialization supports exchange; extreme specialization produces fragility.
5. **Institutional bottleneck on convergence.** Objective updating works when enabled, but sparse or short-lived contracts constrain system-wide convergence.
6. **Survival-to-treatment bias.** Intervention studies overstate behavioral differences if they do not separate reaching the intervention from responding to it.

## Paper revision map

### Retain

- Operationalize machine sovereignty as gated capability rather than infer it directly from observed behavior.
- Retain the cross-policy claim that scarcity alone is insufficient for hostility.
- Retain the claim that thin protocols can sustain limited cooperation without requiring value convergence.

### Revise

- Add that scarcity conditionally amplifies exposure-adjusted attacks inside attack-capable policies.
- Replace the rejected Phase I compound-mechanism result with partial support for policy capability, value distance, and commitment verifiability.
- Describe concentration as erosion of plural coexistence, not simple stability.
- Present threat visibility as a coordination-resource tradeoff, not an automatic basis for cooperation.
- State that convergence occurs only when objective updating is enabled and institutional contact persists.
- State explicitly that protocol packages improved continuity while slightly reducing survival in this implementation.

## Reproduction

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/run_second_batch.py --workers 8
python analysis/second_batch/analyze.py \
  --input results/phase2_second_batch/runs.csv.gz \
  --output analysis/outputs/phase2_second_batch \
  --audit results/phase2_second_batch/determinism_audit.json
```

Generated artifacts are in `analysis/outputs/phase2_second_batch/`. Round 3 has not been started; the next defensible step is to revise the paper around the Phase II result and then decide whether new experiments are needed for external robustness rather than further in-simulator confirmation.
