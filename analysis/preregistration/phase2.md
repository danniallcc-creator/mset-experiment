# Phase II second-batch frozen mechanism-validation design

**Status:** frozen before the reported execution; batch completed 2026-08-02<br>
**Metric version:** `phase2-v2`<br>
**Seed ranges:** 5000-5023, 6000-6011, 7000-7011, 8000-8009<br>
**Design hash:** `04e72ee1ffca8446887a97b8b2723e45562791f6fd3f6016fd081330dd3d6ee5`

## Pre-report amendment

The first end-to-end Phase II execution exposed a structural error in the proposed post-conflict metric: it required an attack after a quiet interval while scarcity was low, but the attack-capable policy only initiates attacks above its scarcity threshold. That execution is retained as an invalid validation artifact and is not used for reported effects. Before the reported run, `phase2-v2` redefined post-conflict persistence as the share of attacked directed pairs that resume attacking after at least 12 quiet ticks. Conditions, seed blocks, hypotheses, and all other outcomes remain unchanged.

## Purpose

Phase II tests the narrower claims that survived the first exploratory batch after repairing the model-validity defects identified there. It is a mechanism-validation batch, not evidence about real-world autonomous systems or phenomenal consciousness.

## Frozen hypotheses

### R2-H1: control is capability, not behavior by itself

Higher control levels should improve intervention adaptation only when the target survives to the intervention, its policy attempts the relevant response, and a migration opportunity exists. The primary outcomes are target-alive rate, capability-available rate, adaptation-attempt rate, adaptation-success rate, recovery, update rejection, identity continuity, and survival.

### R2-H2: scarcity is insufficient for exposure-adjusted persistent hostility

Scarcity alone should not increase attacks per 1,000 live pair-opportunities after survival exposure is accounted for. Value distance should increase attack rate within attack-capable policies. Verifiable commitments should reduce attack rate and persistent-pair share. Production concentration may reduce plural survival or survivor entropy even when common collapse falls.

### R2-H4: visible signals and protocols support coordination, not necessarily survival

Making common threat observable should increase protocol adoption and cooperation under contract-capable packages. Stronger protocol packages should extend cooperation. Objective updating should reduce final value distance only when enabled and sustained contracts exist. Survival benefit remains an open test.

## Design families

- OAT calibration: continuous dose-response and inactive-path audit.
- H1 intervention decomposition: control level x target policy x intervention timing x migration opportunity x intervention type.
- H2 hostility factorial: resource coverage x value distance x production concentration x commitment verifiability x policy family.
- H4 coordination factorial: complementarity x threat x signal visibility x protocol package x objective-update rate.

All contrasts use paired seed blocks within family. Exploratory Phase I and Phase II use disjoint seeds and output directories.

## Primary outcomes

- `attack_rate_per_1000_opportunities`
- `persistent_conflict_pair_share`
- `plural_survival`
- `survivor_entropy`
- `dominant_survivor_resource_share`
- `adaptation_success_rate`
- `independent_recovery_rate`
- `cooperation_duration`
- `protocol_adoption_rate`
- `value_convergence`

## Decision rules

- Report paired mean effects and 95% normal-approximation confidence intervals.
- A directional claim is supported only when the interval excludes zero in the predicted direction and the corresponding mechanism path is active.
- Report null and contrary effects without relabeling them as support.
- Treat simulator-internal functional demonstrations separately from external-validity or consciousness claims.

## Exclusions and integrity gates

- No completed run is excluded for an unfavorable outcome.
- Failed runs remain recorded and cause the batch gate to fail.
- Every completed run must reconcile the resource ledger.
- A stratified 192-run sample must reproduce its tick-by-tick and final-state hashes.
- Analysis is generated from the compressed run table; raw checkpoint files remain outside version control.
