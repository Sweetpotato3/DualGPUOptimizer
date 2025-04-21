#!/usr/bin/env python
"""
Fix invalid escape sequences in ttkbootstrap files
This script patches the ttkbootstrap msgs.py file to fix the invalid escape sequences
that cause warnings during PyInstaller build.
"""

import os
import re
import site
from pathlib import Path

def fix_ttkbootstrap_escapes():
    """Fix invalid escape sequences in ttkbootstrap modules"""
    # Find ttkbootstrap installation
    site_packages = site.getsitepackages()[0]
    msgs_path = Path(site_packages) / "ttkbootstrap" / "localization" / "msgs.py"
    validation_path = Path(site_packages) / "ttkbootstrap" / "validation.py"

    if not msgs_path.exists():
        print(f"ttkbootstrap msgs.py not found at {msgs_path}")
        return False

    # Fix msgs.py - replace %1\$s with %1$s (proper escaping)
    with open(msgs_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace invalid escape sequences
    fixed_content = re.sub(r'%1\\\\?\$s', r'%1$s', content)

    if content != fixed_content:
        with open(msgs_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Fixed escape sequences in {msgs_path}")

    # Fix validation.py - replace \d with \\d
    if validation_path.exists():
        with open(validation_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed_content = content.replace('\\d', '\\\\d')

        if content != fixed_content:
            with open(validation_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed escape sequences in {validation_path}")

    return True

if __name__ == "__main__":
    if fix_ttkbootstrap_escapes():
        print("Successfully fixed ttkbootstrap escape sequences")
    else:
        print("Failed to fix ttkbootstrap escape sequences")