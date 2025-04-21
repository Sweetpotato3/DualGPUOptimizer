#!/usr/bin/env python3
"""
Utility script to fix trailing whitespace issues in Python files
"""
import os
import re
import sys
from pathlib import Path

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

def find_and_fix_python_files(directory='.'):
    """Find and fix trailing whitespace in all Python files"""
    root_dir = Path(directory)
    fixed_count = 0

    # Find all Python files recursively
    for path in root_dir.glob('**/*.py'):
        if fix_trailing_whitespace(path):
            fixed_count += 1

    # Find specific files that might not be .py
    for path in root_dir.glob('README.md'):
        if fix_trailing_whitespace(path):
            fixed_count += 1

    return fixed_count

if __name__ == "__main__":
    # Get directory from command line argument or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'

    # Fix trailing whitespace
    fixed_count = find_and_fix_python_files(directory)

    # Print summary
    print(f"Fixed trailing whitespace in {fixed_count} file(s)")