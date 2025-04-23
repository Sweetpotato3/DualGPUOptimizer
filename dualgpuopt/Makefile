.PHONY: data setup clean test docs

# Default development environment setup
setup:
	python -m pip install -e .[dev,train]
	pre-commit install
	cursor trust

# One-liner for data download and processing
data:
	@echo "Running data collection and preparation..."
	mkdir -p corpora/qc_statutes/raw corpora/canlii_fr/raw datasets
	python -m dualgpuopt.ingest.operator_tasks.legisqc
	python -m dualgpuopt.ingest.operator_tasks.canlii_fr
	python -m dualgpuopt.ingest.clean_html corpora/qc_statutes/raw datasets/qc_legal_clean.jsonl
	@echo "Data preparation complete"

# Run all tests
test:
	pytest -xvs dualgpuopt/tests/

# Generate documentation
docs:
	mkdir -p notebooks
	jupyter nbconvert --execute --to notebook --output notebooks/Quickstart_FR_Legal.ipynb dualgpuopt/notebooks/Quickstart_FR_Legal.ipynb.template
	mkdir -p docs
	pdoc --html --output-dir docs dualgpuopt

# Clean generated files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf dualgpuopt/__pycache__/
	find . -name "*.pyc" -delete
