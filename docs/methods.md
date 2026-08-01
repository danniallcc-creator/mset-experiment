# Methods implemented in Phase I

The simulator advances in discrete ticks. Resource generation is explicit, maintenance and action costs are debited, and destructive losses are recorded in a ledger. Transfers do not change the world total. Agents observe local resource, trust, intervention, and protocol state; they never receive hidden experimental condition labels.

Every tick records the complete environment state, observations, selected actions, costs, resource deltas, contract changes, identity changes, random seed, policy versions, and a canonical state hash. Replay re-executes a configuration from its seed and compares the full hash sequence. Counterfactual replay replaces one action with a neutral action and reports the target's outcome delta.

In the Phase A mechanism layer, objective vectors are declared and observable. Scripted policies respond to the realized pairwise distance among those vectors, not to a condition label. Later robustness checks will add noisy, delayed, and hidden-objective variants so this convenience assumption is not mistaken for a substantive claim.

This implementation is intentionally abstract. It does not connect to external networks, services, financial systems, infrastructure, or physical devices.
