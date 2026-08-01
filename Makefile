PYTHON ?= python3

.PHONY: test smoke replay site clean

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

smoke:
	PYTHONPATH=src $(PYTHON) -m mset batch configs/smoke/matrix.json --output results/smoke
	PYTHONPATH=src $(PYTHON) -m mset summarize results/smoke --output results/smoke/aggregate.csv

replay:
	PYTHONPATH=src $(PYTHON) -m mset verify results/smoke

site:
	PYTHONPATH=src $(PYTHON) -m mset site results/smoke --docs docs

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(p) for p in (Path('results/smoke'), Path('results/demo')) if p.exists()]"
