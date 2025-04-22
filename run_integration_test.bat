@echo off
REM Test script for signal-based telemetry integration

echo Running signal-based telemetry test...
echo.

REM Set mock mode environment variable
set DUALGPUOPT_MOCK_GPU=1

python test_signal_telemetry.py

echo.
echo Test complete.
pause 