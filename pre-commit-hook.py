#!/usr/bin/env python3
"""
Git pre-commit hook to check for trailing whitespace and unused imports.
Place this file in .git/hooks/pre-commit and make it executable (chmod +x .git/hooks/pre-commit)
"""
import os
import re
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []

    try:
        import autoflake
    except ImportError:
        missing_deps.append("autoflake")

    if missing_deps:
        print("Warning: The following dependencies are missing:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstall them with:")
        print("  pip install " + " ".join(missing_deps))
        return False

    return True

def get_staged_python_files():
    """Get list of staged Python files"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--staged', '--diff-filter=ACMR'],
            capture_output=True, text=True, check=True
        )
        files = result.stdout.splitlines()
        # Return only files that exist and have a .py extension
        return [f for f in files if f.endswith('.py') and os.path.isfile(f)]
    except subprocess.SubprocessError as e:
        print(f"Error getting staged files: {e}")
        return []

def check_trailing_whitespace(file_path):
    """Check for trailing whitespace in a file"""
    try:
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            return True
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if re.search(r'[ \t]+$', content, flags=re.MULTILINE):
            print(f"Error: Trailing whitespace found in {file_path}")
            return False
        return True
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return True  # Don't fail on errors

def check_unused_imports(file_path):
    """Check for unused imports using autoflake"""
    try:
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            return True
            
        result = subprocess.run([
            sys.executable, '-m', 'autoflake',
            '--check-only',
            '--remove-all-unused-imports',
            '--stdout',
            file_path
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error checking imports in {file_path}: {result.stderr}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        if original_content != result.stdout:
            print(f"Error: Unused imports found in {file_path}")
            return False

        return True
    except Exception as e:
        print(f"Error checking imports in {file_path}: {e}")
        return True  # Don't fail on errors

def main():
    """Main function to check files"""
    has_deps = check_dependencies()
    staged_files = get_staged_python_files()

    if not staged_files:
        print("No Python files staged for commit")
        return 0

    print(f"Checking {len(staged_files)} staged Python files")
    
    whitespace_errors = []
    import_errors = []

    for file_path in staged_files:
        if not check_trailing_whitespace(file_path):
            whitespace_errors.append(file_path)

        if has_deps and not check_unused_imports(file_path):
            import_errors.append(file_path)

    if whitespace_errors or import_errors:
        print("\nCommit failed due to code quality checks.")

        if whitespace_errors:
            print("\nFiles with trailing whitespace:")
            for file in whitespace_errors:
                print(f"  - {file}")
            print("\nFix with: python -c \"import re, sys; f = open(sys.argv[1], 'r'); content = f.read(); f.close(); content = re.sub(r'[ \\t]+$', '', content, flags=re.MULTILINE); f = open(sys.argv[1], 'w'); f.write(content); f.close()\" <file>")

        if import_errors:
            print("\nFiles with unused imports:")
            for file in import_errors:
                print(f"  - {file}")
            print("\nFix with: python -m autoflake --in-place --remove-all-unused-imports <file>")

        print("\nFix the issues and try committing again.")
        print("To bypass this check, use: git commit --no-verify")
        return 1

    print("All checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())