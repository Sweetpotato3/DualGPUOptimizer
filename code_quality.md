# Code Quality Tools

This document describes the tools available for maintaining code quality in the DualGPUOptimizer project.

## Available Tools

### 1. Whitespace and Import Cleanup

The `fix_whitespace.py` script automatically removes:
- Trailing whitespace
- Unused imports (if autoflake is installed)

To use it:

```bash
# Clean up all Python files
python fix_whitespace.py

# Clean up files in a specific directory
python fix_whitespace.py dualgpuopt/
```

### 2. Pre-Commit Hook

The pre-commit hook automatically checks staged files for:
- Trailing whitespace
- Unused imports

This prevents committing code with these issues.

### 3. Installation Script

The `install_autoflake.py` script:
- Checks if autoflake is installed, and installs it if it's not
- Sets up the pre-commit hook in your local git repository

## Setup Instructions

### Quick Setup

Run the installation script:

```bash
python install_autoflake.py
```

This will:
1. Check if autoflake is installed
2. Install autoflake if it's not already installed
3. Ask if you want to install the pre-commit hook
4. Set up the pre-commit hook if you choose to

### Manual Setup

1. Install autoflake:

```bash
pip install autoflake
```

2. Install the pre-commit hook:

```bash
# Copy the hook script to the git hooks directory
cp pre-commit-hook.py .git/hooks/pre-commit

# Make it executable (Linux/Mac)
chmod +x .git/hooks/pre-commit

# For Windows (using PowerShell)
# icacls .git/hooks/pre-commit /grant Everyone:RX
```

## Usage

### Cleaning the Codebase

To clean the entire codebase:

```bash
python fix_whitespace.py
```

### During Development

With the pre-commit hook installed, Git will automatically check your code before each commit:

1. Stage your changes: `git add .`
2. Commit: `git commit -m "Your message"`
3. If issues are found, the commit will be aborted with details on what to fix
4. Fix the issues and try committing again

## Best Practices

- Keep all import statements at the top of the file
- Remove imports that are no longer used when refactoring code
- Set up your editor to automatically trim trailing whitespace
- Run `fix_whitespace.py` before making pull requests

## Editor Configuration

### VS Code

Add this to your `.vscode/settings.json`:

```json
{
  "files.trimTrailingWhitespace": true,
  "editor.formatOnSave": true,
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true
}
```

### PyCharm

1. Go to File → Settings → Editor → General
2. Check "Ensure line feed at file end on Save" and "Strip trailing spaces on Save"

### Vim

Add to your `.vimrc`:

```
autocmd BufWritePre *.py :%s/\s\+$//e
```

### Emacs

Add to your `.emacs`:

```
(add-hook 'before-save-hook 'delete-trailing-whitespace)
``` 