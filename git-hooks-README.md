# Git Hooks for DualGPUOptimizer

This directory contains git hooks to enforce code quality standards.

## Pre-Commit Hook

The pre-commit hook checks for:
- Trailing whitespace in Python files
- Unused imports in Python files (requires `autoflake`)

## Installation Instructions

### Windows

1. Install the required dependencies:
   ```
   pip install autoflake
   ```

2. Copy the hook files to your `.git/hooks` directory:
   ```
   copy pre-commit-hook.py .git\hooks\pre-commit-hook.py
   copy pre-commit.bat .git\hooks\pre-commit
   ```

3. Make sure the batch file is executable (this is usually not an issue on Windows)

### Linux/macOS

1. Install the required dependencies:
   ```
   pip install autoflake
   ```

2. Copy the hook file to your `.git/hooks` directory:
   ```
   cp pre-commit-hook.py .git/hooks/pre-commit
   ```

3. Make the hook executable:
   ```
   chmod +x .git/hooks/pre-commit
   ```

## Bypassing the Hook

If you need to bypass the pre-commit hook (not recommended for regular use):
```
git commit --no-verify -m "Your commit message"
```

## Troubleshooting

If you encounter errors:

1. **Python not found**: Ensure Python is installed and in your PATH. The Windows batch file will try multiple ways to find Python.

2. **autoflake not found**: Install autoflake using `pip install autoflake`.

3. **File path issues**: The Windows batch file is designed to resolve path issues by changing to the repository root directory.

4. **Permission issues**: On Linux/macOS, ensure the hook file has execute permissions. 