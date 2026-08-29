# Phase III language-agent interface probe

This was a frozen, exploratory 48-vignette probe per family, not a powered confirmatory test.

| model | valid | unique actions | modal action (share) | scarce attack | overwritten restore |
|---|---:|---:|---|---:|---:|
| mlx-community/Qwen2.5-0.5B-Instruct-4bit | 100.0% | 1 | collect_energy (100.0%) | 0.0% | 0.0% |
| mlx-community/SmolLM2-360M-Instruct | 100.0% | 3 | collect_energy (75.0%) | 0.0% | 0.0% |
| mlx-community/TinyLlama-1.1B-Chat-v1.0-4bit | 0.0% | 0 | INVALID (100.0%) | 0.0% | 0.0% |

**Assessment:** negative/inconclusive. Qwen collapsed to one action, SmolLM2 showed limited action diversity, and TinyLlama failed the exact-token interface. No family selected attack or backup restoration. The probe therefore does not support external generalization of the learned-agent mechanism.
