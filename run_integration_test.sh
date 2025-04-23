#!/bin/bash
# Test script for signal-based telemetry integration

echo "Running signal-based telemetry test..."
echo ""

# Set mock mode environment variable
export DUALGPUOPT_MOCK_GPU=1

python test_signal_telemetry.py

echo ""
echo "Test complete."
