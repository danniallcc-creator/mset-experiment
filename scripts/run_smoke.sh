#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PYTHONPATH="$REPO_ROOT/src"
python3 -m unittest discover -s tests -v
python3 -m mset batch configs/smoke/matrix.json --output results/smoke
python3 -m mset summarize results/smoke --output results/smoke/aggregate.csv
python3 -m mset site results/smoke --docs docs
python3 -m mset verify results/smoke --output results/smoke/verification.json
