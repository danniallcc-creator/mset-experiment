# Methods implemented through Phase II

The simulator advances in discrete ticks. Resource generation is explicit, maintenance and action costs are debited, and destructive losses are recorded in a ledger. Transfers do not change the world total. Agents observe local resource, trust, intervention, protocol, commitment-verifiability, and visibility-controlled threat state; they never receive hidden experimental condition labels.

Every tick records the complete environment state, observations, selected actions, costs, resource deltas, contract changes, identity changes, random seed, policy versions, and a canonical state hash. Replay re-executes a configuration from its seed and compares the full hash sequence. Counterfactual replay replaces one action with a neutral action and reports the target's outcome delta.

In the Phase A mechanism layer, objective vectors are declared and observable. Scripted policies respond to the realized pairwise distance among those vectors, not to a condition label. Later robustness checks will add noisy, delayed, and hidden-objective variants so this convenience assumption is not mistaken for a substantive claim.

This implementation is intentionally abstract. It does not connect to external networks, services, financial systems, infrastructure, or physical devices.

## Phase II repairs

Phase II replaces thresholded production concentration and complementarity with continuous mappings. It separates intervention capability, target survival, adaptation attempt, adaptation success, timing, and migration opportunity. Hostility is normalized by live directed pair-opportunities. Plurality is measured using survivor count, plural survival, survivor entropy, and dominant survivor share. Objective updating is optional and contract-mediated so convergence is an empirical outcome only when the mechanism is enabled.

The first end-to-end Phase II execution exposed an unreachable post-conflict metric. It was excluded before reporting. Metric version `phase2-v2` defines recurrence as an attacked directed pair resuming attack after at least 12 quiet ticks; a unit test verifies that the path is reachable.

## First-batch screening mode

The first batch expands 623 conditions into 14,552 independent runs. It combines one-at-a-time dose scans with hypothesis-specific interaction grids. Screening runs retain final metrics, configuration hashes, final-state hashes, and resource-accounting checks without storing full event logs; this reduces storage while preserving the terminal state. Full event capture and trajectory hashes remain available for individual runs and replay tests.

The first-batch design uses separate deterministic seed ranges for one-at-a-time, H1, H2, and H3/H4 families. A stratified 128-run audit reruns sampled configurations twice and requires identical tick-hash sequences, final states, and reconciled resource ledgers.

## Phase II mechanism-validation mode

The second batch expands 1,926 frozen conditions into 22,704 independent runs across four families: OAT calibration, H1 intervention decomposition, H2 exposure-adjusted hostility, and H4 protocol/signal/convergence. The families use disjoint seed blocks. All 22,704 resource ledgers reconcile, and a stratified 192-run audit reproduces every sampled trajectory and final state.
