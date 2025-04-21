#!/usr/bin/env python3
"""
Utility script to fix trailing whitespace issues and unused imports in Python files
"""
import re
import sys
import subprocess
from pathlib import Path

def check_autoflake():
    """Check if autoflake is installed"""
    try:
        return True
    except ImportError:
        print("Warning: autoflake is not installed. Will only fix whitespace.")
        print("To fix unused imports, install autoflake with: pip install autoflake")
        return False

def fix_trailing_whitespace(file_path):
    """Fix trailing whitespace in a file"""
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix trailing whitespace
        fixed_content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

        # Write back to the file if changed
        if content != fixed_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed trailing whitespace in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def fix_unused_imports(file_path):
    """Fix unused imports using autoflake"""
    try:
        result = subprocess.run([
            'autoflake',
            '--in-place',
            '--remove-all-unused-imports',
            '--remove-unused-variables',
            str(file_path)
        ], capture_output=True, text=True)

        if result.returncode == 0:
            if "Removed" in result.stderr:
                print(f"Fixed unused imports in {file_path}")
                return True
        else:
            print(f"Error fixing imports in {file_path}: {result.stderr}")
        return False
    except Exception as e:
        print(f"Error running autoflake on {file_path}: {e}")
        return False

def find_and_fix_python_files(directory='.'):
    """Find and fix trailing whitespace and unused imports in all Python files"""
    root_dir = Path(directory)
    whitespace_fixed_count = 0
    imports_fixed_count = 0
    has_autoflake = check_autoflake()

    # Find all Python files recursively
    for path in root_dir.glob('**/*.py'):
        if fix_trailing_whitespace(path):
            whitespace_fixed_count += 1

        if has_autoflake and path.is_file():
            if fix_unused_imports(path):
                imports_fixed_count += 1

    # Find specific files that might not be .py
    for path in root_dir.glob('README.md'):
        if fix_trailing_whitespace(path):
            whitespace_fixed_count += 1

    return whitespace_fixed_count, imports_fixed_count

if __name__ == "__main__":
    # Get directory from command line argument or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'

    # Fix trailing whitespace and unused imports
    whitespace_fixed, imports_fixed = find_and_fix_python_files(directory)

    # Print summary
    print(f"Fixed trailing whitespace in {whitespace_fixed} file(s)")
    print(f"Fixed unused imports in {imports_fixed} file(s)")