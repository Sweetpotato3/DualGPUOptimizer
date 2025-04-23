.PHONY: test test-unit test-integration test-functional test-all test-coverage clean lint format help ingest train eval serve gui

# Variables
PYTHON := python
PYTEST := pytest
PYTEST_ARGS := -v
COVERAGE_THRESHOLD := 70
PY := python -m

help:
	@echo "Available targets:"
	@echo "  test              Run unit tests only"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-functional   Run functional tests only"
	@echo "  test-all          Run all tests"
	@echo "  test-coverage     Run tests with coverage report"
	@echo "  clean             Remove temp files and artifacts"
	@echo "  lint              Run linting checks"
	@echo "  format            Format code with black"
	@echo "  ingest            Clean and tokenize HTML files"
	@echo "  train             Train a model"
	@echo "  eval              Evaluate the model"
	@echo "  serve             Serve the model"
	@echo "  gui               Start the GUI application"

test: test-unit

test-unit:
	$(PYTEST) $(PYTEST_ARGS) test/unit

test-integration:
	$(PYTEST) $(PYTEST_ARGS) test/integration

test-functional:
	$(PYTEST) $(PYTEST_ARGS) test/functional

test-all:
	$(PYTEST) $(PYTEST_ARGS) test

test-coverage:
	$(PYTEST) $(PYTEST_ARGS) --cov=dualgpuopt --cov-report=term --cov-report=html --cov-fail-under=$(COVERAGE_THRESHOLD) test
	@echo "HTML coverage report generated in htmlcov/"

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

lint:
	flake8 dualgpuopt test
	mypy dualgpuopt

format:
	black dualgpuopt test

# Installation of dev dependencies
install-dev:
	$(PYTHON) -m pip install -e ".[dev,test]"

# Installation for users
install:
	$(PYTHON) -m pip install .

# Default target
.DEFAULT_GOAL := help

ingest:
	$(PY) ingest.clean_html datasets/raw_qc datasets/legal_clean.jsonl
	$(PY) datasets.qc_tokeniser

train:
	$(PY) scripts.train_qlora --base_model mistralai/Mistral-7B-Instruct \
	   --dataset_path datasets/legal_clean.jsonl \
	   --output_dir checkpoints/legal-lora

eval:
	pytest -q tests/test_lexglue_fr.py

serve:
	$(PY) serve.legal_api

gui:
	$(PY) dualgpuopt.qt.app_window
