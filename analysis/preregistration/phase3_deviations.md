# Phase III deviation log

The confirmatory simulation design, seeds, hypotheses, estimands, thresholds and analysis rules were not changed after execution began.

## D1 — SmolLM2 Hub locator correction

- Frozen locator: `mlx-community/SmolLM2-360M-Instruct-4bit`
- Executed locator: `mlx-community/SmolLM2-360M-Instruct`
- Reason: the frozen locator does not exist on Hugging Face Hub.
- Scope: the intended SmolLM2 360M Instruct family and scale were retained. The executed revision is recorded in the output manifest. This is an implementation deviation in the exploratory language probe, not a confirmatory simulation-design change.

## D2 — TinyLlama legacy filename compatibility

The frozen TinyLlama MLX snapshot stores unchanged weights as `weights.00.safetensors`, while current `mlx-lm` expects `model.safetensors`. The runner creates a symbolic filename alias without modifying weight bytes. The original Hub revision remains fixed and recorded.

## D3 — Identity recovery latency reporting

The frozen run table encodes latency as zero when no restoration occurs. Direct paired contrasts would therefore mix restoration incidence and timing. The confirmatory identity result uses restoration success and identity continuity; latency is reported descriptively only among successful restores. No run value was altered.
