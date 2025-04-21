#!/usr/bin/env python3
"""
Utility script to install autoflake if it's not already installed
"""
import subprocess
import sys

def check_autoflake():
    """Check if autoflake is installed"""
    try:
        print("autoflake is already installed.")
        return True
    except ImportError:
        print("autoflake is not installed.")
        return False

def install_autoflake():
    """Install autoflake using pip"""
    print("Installing autoflake...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "autoflake"], check=True)
        print("Successfully installed autoflake.")
        return True
    except subprocess.SubprocessError as e:
        print(f"Error installing autoflake: {e}")
        return False

def setup_pre_commit_hook():
    """Set up the pre-commit hook"""
    import os
    from pathlib import Path

    try:
        # Determine the git hooks directory
        git_dir = Path(".git")
        if not git_dir.exists():
            print("No .git directory found. Are you in a git repository?")
            return False

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        # Copy pre-commit-hook.py to .git/hooks/pre-commit
        pre_commit_hook = Path("pre-commit-hook.py")
        if not pre_commit_hook.exists():
            print("pre-commit-hook.py not found.")
            return False

        target_hook = hooks_dir / "pre-commit"

        with open(pre_commit_hook, 'r', encoding='utf-8') as src_file:
            hook_content = src_file.read()

        with open(target_hook, 'w', encoding='utf-8') as dest_file:
            dest_file.write(hook_content)

        # Make the hook executable
        os.chmod(target_hook, 0o755)  # rwxr-xr-x

        print(f"Pre-commit hook installed to {target_hook}")
        return True
    except Exception as e:
        print(f"Error setting up pre-commit hook: {e}")
        return False

if __name__ == "__main__":
    if not check_autoflake():
        if not install_autoflake():
            print("Failed to install autoflake. Please install it manually:")
            print("  pip install autoflake")
            sys.exit(1)

    install_hook = input("Do you want to install the pre-commit hook? (y/n): ").lower().strip()
    if install_hook == 'y':
        if setup_pre_commit_hook():
            print("\nSetup complete!")
            print("The pre-commit hook will now check for trailing whitespace and unused imports.")
        else:
            print("\nFailed to set up pre-commit hook.")
            sys.exit(1)
    else:
        print("\nPre-commit hook installation skipped.")
        print("You can manually install it later by copying pre-commit-hook.py to .git/hooks/pre-commit")
        print("and making it executable (chmod +x .git/hooks/pre-commit)")

    print("\nYou can now run the following to clean your codebase:")
    print("  python fix_whitespace.py")