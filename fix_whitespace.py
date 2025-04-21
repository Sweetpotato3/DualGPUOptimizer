#!/usr/bin/env python3
"""
Helper script to remove trailing whitespace from Python files.
"""
import os
import re
import sys
from pathlib import Path


def remove_trailing_whitespace(file_path):
    """Remove trailing whitespace from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if there is trailing whitespace
        if not re.search(r'[ \t]+$', content, flags=re.MULTILINE):
            return False  # No changes needed
            
        # Remove trailing whitespace
        new_content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True  # Changes made
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process files"""
    # Get list of Python files
    if len(sys.argv) > 1:
        # Process specific files provided as arguments
        files = [Path(arg) for arg in sys.argv[1:] if Path(arg).exists() and arg.endswith('.py')]
    else:
        # Find all Python files recursively starting from the current directory
        files = list(Path('.').glob('**/*.py'))
    
    if not files:
        print("No Python files found")
        return 0
    
    print(f"Checking {len(files)} Python files for trailing whitespace")
    
    fixed_count = 0
    for file_path in files:
        if remove_trailing_whitespace(file_path):
            print(f"Fixed trailing whitespace in {file_path}")
            fixed_count += 1
    
    print(f"\nFixed trailing whitespace in {fixed_count} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())