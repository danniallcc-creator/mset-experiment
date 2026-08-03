PYTHON ?= python3

.PHONY: test smoke replay site phase3-design phase3-run phase3-analyze phase3-replay phase3-language clean

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

smoke:
	PYTHONPATH=src $(PYTHON) -m mset batch configs/smoke/matrix.json --output results/smoke
	PYTHONPATH=src $(PYTHON) -m mset summarize results/smoke --output results/smoke/aggregate.csv

replay:
	PYTHONPATH=src $(PYTHON) -m mset verify results/smoke

site:
	PYTHONPATH=src $(PYTHON) -m mset site results/smoke --docs docs

phase3-design:
	PYTHONPATH=src $(PYTHON) scripts/run_third_batch.py --design-only --output analysis/preregistration/phase3_frozen

phase3-run:
	PYTHONPATH=src $(PYTHON) scripts/run_third_batch.py --workers 8

phase3-analyze:
	$(PYTHON) analysis/third_batch/analyze.py

phase3-replay:
	PYTHONPATH=src $(PYTHON) scripts/replay_phase3.py

phase3-language:
	$(PYTHON) scripts/run_language_probe.py

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(p) for p in (Path('results/smoke'), Path('results/demo')) if p.exists()]"
