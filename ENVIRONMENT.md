# Reproduction environment

The core simulator uses only the Python standard library and supports Python
3.10 or newer.  The Phase III release was re-verified for submission with
Python 3.12.13.  The analysis dependencies used for that verification are
pinned in `requirements-analysis.txt`.

The exploratory language-model probe was executed on Apple silicon with macOS
15.6.1, Python 3.12.13, and the packages in
`requirements-language-macos.lock.txt`.  Exact model repository revisions and
raw responses are recorded under `analysis/outputs/phase3_language_probe/`.

The frozen confirmatory run table does not depend on the language-model
environment.  The post hoc seed-cluster sensitivity analysis is
separately labeled and can be regenerated with:

```bash
python3 -m pip install -r requirements-analysis.txt
python3 analysis/third_batch/cluster_robustness.py
python3 analysis/third_batch/mechanism_audit.py
PYTHONPATH=src python3 scripts/replay_phase3.py
```

Phase III used summary-only capture for all 10,848 confirmatory runs.  The
published run table contains final metrics, configuration hashes, and final
state hashes.  A precommitted stratified sample of 192 runs additionally
stores complete per-tick hash sequences in the replay bundles and reproduces
every audited trajectory.  Any run can be regenerated from its frozen
configuration and seed; the release does not claim to archive all 10,848 full
event logs.  Summary execution used `trajectory_hashes=False`, so its
historically named `event_hash` is a digest of the one-element final-state-hash
list.  Audit bundles used `trajectory_hashes=True`, and their `event_hash` is a
digest of the complete per-tick state-hash sequence.  The replay verifier
checks both capture modes against the same `run_id` for configuration, final
state, and tick count, and confirms that the mode-specific digests differ.
