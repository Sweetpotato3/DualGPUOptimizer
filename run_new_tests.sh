#!/bin/bash
echo "Installing required test dependencies..."
pip install pytest pytest-env pytest-cov fastapi faiss-cpu

echo "Setting up PYTHONPATH..."
export PYTHONPATH=$(pwd):$PYTHONPATH

echo "Running lightweight test suite..."
pytest tests/test_engine_pool.py tests/test_fit_plan.py -v

echo
echo "Note: API and retriever tests require additional dependencies."
echo "To run these tests, install: pip install fastapi faiss-cpu uvicorn"
echo
echo "To run API tests: pytest tests/test_api.py -v"
echo "To run retriever tests: pytest tests/test_retriever.py -v"
