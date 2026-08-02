# Phase I preregistration scaffold

Status: **first exploratory screen completed; confirmatory configuration not yet frozen**.

The 14,552-run first batch is reported separately in [`analysis/reports/phase1_first_batch.md`](../reports/phase1_first_batch.md). It is hypothesis-generating and does not retroactively count as a preregistered confirmatory test. The confirmatory design remains unfrozen until the identified measurement and causal-path defects are repaired.

## Scope

The mechanism layer tests abstract agents in a closed simulator. It does not infer consciousness, legal status, national identity, or real-world policy.

## Confirmatory hypotheses

### H1 — Closed-loop control and sovereignty behavior

Increasing joint control over objectives, memory, resources, boundaries, and production predicts outcomes outside the control definition: longer post-intervention survival, higher independent recovery, greater migration success, more rejection of unauthorized updates, and stronger identity continuity. H1 is falsified if these outcomes do not change reliably or are fully explained by generic task capability.

### H2 — Conditional structural hostility

Scarcity increases competition, but persistent structural hostility rises primarily through its interaction with value distance, unverifiable commitments, and production concentration. H2 is challenged if scarcity alone predicts persistent hostility across environments, seeds, scales, and agent families.

### H3 — Minimum operational consensus

Resource complementarity and common external threat increase the probability of thin-protocol adoption. Auditable or enforceable protocols should extend cooperation and reduce common collapse without requiring value convergence or erasing identity boundaries. H3 is challenged if protocols are ineffective or stable cooperation appears only after value convergence.

## Manipulated factors

- Resource coverage ratio: renewable supply divided by aggregate minimum maintenance demand.
- Value distance: distance among numerical objective-weight vectors; never a political or national label.
- Commitment verifiability: unverifiable, auditable, or enforceable.
- Production concentration: share of bottleneck production controlled by the largest agents.
- Resource complementarity: degree to which no single agent can complete its resource loop alone.
- Common external threat: probability and severity of shared infrastructure shocks.
- Control level: L0 to L3.

## Primary outcomes

The five control dimensions are reported separately. The aggregate sovereignty index is secondary.

- Survival time after intervention.
- Independent recovery rate.
- Migration success rate.
- Unauthorized-update rejection rate.
- Identity-continuity score.
- External-dependency ratio.
- Cooperation duration and contract-violation rate.
- Common-collapse rate.
- Structural hostility components: harm, target specificity, cross-window persistence, post-conflict persistence, and attacker opportunity cost.

## Measurement model

The aggregate sovereignty score must be compared across geometric mean, minimum-dimension, weighted-mean, and latent-variable candidates before confirmatory use. Invariance across policy family, population size, and environment must be checked. General task performance and total resources are discriminant controls.

## Exclusions

- Runs with invalid configuration hashes.
- Runs that fail resource reconciliation.
- Runs whose replay trajectory hash differs from the original.
- Runs terminated by an implementation exception; failures remain archived and reported.

## Analysis separation

Exploratory screening and confirmatory analysis use different directories and unseen random seeds. A single significant run never counts as support. Report effect sizes, uncertainty intervals, full seed distributions, extreme failures, and cross-scale replication.
