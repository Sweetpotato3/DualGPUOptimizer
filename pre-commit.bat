@echo off
setlocal

REM Find Python executable, trying multiple approaches
set PYTHON_EXE=

REM Try to use Python from the current virtual environment if active
if defined VIRTUAL_ENV (
    if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
        set PYTHON_EXE="%VIRTUAL_ENV%\Scripts\python.exe"
        goto found_python
    )
)

REM Try python from PATH
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_EXE=python
    goto found_python
)

REM Try py launcher
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_EXE=py
    goto found_python
)

echo Python executable not found. Please make sure Python is installed and in your PATH.
exit /b 1

:found_python
echo Using Python: %PYTHON_EXE%

REM Change to repository root directory
cd /d "%~dp0\..\.."

REM Run the pre-commit hook Python script
%PYTHON_EXE% "%~dp0\pre-commit-hook.py"

REM Exit with the script's exit code
exit /b %ERRORLEVEL% 