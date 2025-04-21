#!/usr/bin/env python3
"""
Utility script to fix trailing whitespace and long line issues in Python files
"""
import re
import sys
import subprocess
from pathlib import Path

MAX_LINE_LENGTH = 88  # PEP 8 recommends 79, but many projects use 88 or 100

def check_autoflake():
    """Check if autoflake is installed"""
    try:
        subprocess.run(['autoflake', '--version'], capture_output=True, check=True)
        return True
    except (ImportError, subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: autoflake is not installed. Will only fix whitespace and line" +
        " length.")
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

def fix_long_lines(file_path, max_length=MAX_LINE_LENGTH):
    """
    Attempt to fix lines that are too long by doing simple fixes:
    - Break up long string literals
    - Move closing brackets to their own line
    - Split long function calls
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed = False
        new_lines = []

        for line in lines:
            if len(line.rstrip('\n')) > max_length:
                # Try various fixes for long lines

                # 1. String literals with + operators
                if '"' in line or "'" in line:
                    fixed_line = fix_string_literal(line, max_length)
                    if fixed_line != line:
                        new_lines.append(fixed_line)
                        fixed = True
                        continue

                # 2. Function calls with many arguments
                if '(' in line and ')' in line:
                    fixed_line = fix_function_call(line, max_length)
                    if fixed_line != line:
                        new_lines.append(fixed_line)
                        fixed = True
                        continue

                # 3. Lists, dicts with many items
                if '[' in line or '{' in line:
                    fixed_line = fix_container(line, max_length)
                    if fixed_line != line:
                        new_lines.append(fixed_line)
                        fixed = True
                        continue

                # Just add the original line if we couldn't fix it
                new_lines.append(line)
                # Print a warning for lines we couldn't fix
                print(f"WARNING: Could not automatically fix long line in {file_path}:" +
                " {line.strip()}")
            else:
                new_lines.append(line)

        if fixed:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Fixed long lines in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing long lines in {file_path}: {e}")
        return False

def fix_string_literal(line, max_length):
    """Split a long string literal across multiple lines using string concatenation"""
    # This is a simplified version - a real implementation would need to be more sophisticated
    # to handle various string types and contexts
    match = re.search(r'(["\'])(.*?)(\1)', line)
    if not match:
        return line

    # If line is too long and contains a string
    indent = len(line) - len(line.lstrip())
    indent_str = ' ' * indent

    # Split the string at a reasonable point
    string_content = match.group(2)
    split_point = max_length - indent - 10  # Allow room for quotes and +

    if len(string_content) > split_point:
        # Simple string split approach
        part1 = string_content[:split_point]
        part2 = string_content[split_point:]

        # Replace the original string with a split version
        new_line = line.replace(
            f"{match.group(1)}{string_content}{match.group(3)}",
            f"{match.group(1)}{part1}{match.group(3)} +\n{indent_str}{match.grou" +
            "p(1)}{part2}{match.group(3)}"
        )
        return new_line

    return line

def fix_function_call(line, max_length):
    """Break a long function call into multiple lines"""
    if '(' not in line or ')' not in line:
        return line

    # Find the function call opening parenthesis
    open_paren_idx = line.find('(')
    if open_paren_idx == -1:
        return line

    # Calculate indentation
    indent = len(line) - len(line.lstrip())
    indent_str = ' ' * indent
    function_indent = ' ' * (open_paren_idx + 1)

    # Simple approach: move closing parenthesis to new line
    if line.rstrip().endswith(')'):
        # Split at commas for function arguments
        prefix = line[:open_paren_idx+1].rstrip()
        content = line[open_paren_idx+1:-1].strip()

        # If we have multiple args, split them
        if ',' in content:
            args = content.split(',')
            result = prefix + '\n'
            for i, arg in enumerate(args):
                arg = arg.strip()
                if i < len(args) - 1:
                    result += f"{function_indent}{arg},\n"
                else:
                    result += f"{function_indent}{arg}\n"
            result += f"{indent_str})"
            return result

    return line

def fix_container(line, max_length):
    """Break a long list, dict, or set declaration into multiple lines"""
    if ('[' not in line and '{' not in line) or (']' not in line and '}' not in line):
        return line

    # Find opening bracket
    open_bracket_idx = min(
        line.find('[') if '[' in line else float('inf'),
        line.find('{') if '{' in line else float('inf')
    )

    if open_bracket_idx == float('inf'):
        return line

    # Find corresponding closing bracket
    close_char = ']' if line[open_bracket_idx] == '[' else '}'

    # Calculate indentation
    indent = len(line) - len(line.lstrip())
    indent_str = ' ' * indent
    container_indent = ' ' * (open_bracket_idx + 1)

    # Simple approach: move closing bracket to new line
    if line.rstrip().endswith(close_char):
        # Split at commas for container items
        prefix = line[:open_bracket_idx+1].rstrip()
        content = line[open_bracket_idx+1:-1].strip()

        # If we have multiple items, split them
        if ',' in content:
            items = content.split(',')
            result = prefix + '\n'
            for i, item in enumerate(items):
                item = item.strip()
                if not item:
                    continue
                if i < len(items) - 1:
                    result += f"{container_indent}{item},\n"
                else:
                    result += f"{container_indent}{item}\n"
            result += f"{indent_str}{close_char}"
            return result

    return line

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
    """Find and fix style issues in all Python files"""
    root_dir = Path(directory)
    whitespace_fixed_count = 0
    line_length_fixed_count = 0
    imports_fixed_count = 0
    has_autoflake = check_autoflake()

    # Find all Python files recursively
    for path in root_dir.glob('**/*.py'):
        if fix_trailing_whitespace(path):
            whitespace_fixed_count += 1

        if fix_long_lines(path):
            line_length_fixed_count += 1

        if has_autoflake and path.is_file():
            if fix_unused_imports(path):
                imports_fixed_count += 1

    # Find specific non-Python files to fix whitespace
    for pattern in ['**/*.md', '**/*.json', '**/*.toml', '**/*.yml', '**/*.yaml']:
        for path in root_dir.glob(pattern):
            if fix_trailing_whitespace(path):
                whitespace_fixed_count += 1

    return whitespace_fixed_count, line_length_fixed_count, imports_fixed_count

if __name__ == "__main__":
    # Get directory from command line argument or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'

    # Fix style issues
    whitespace_fixed, line_length_fixed, imports_fixed = find_and_fix_python_files(directory)

    # Print summary
    print(f"Fixed trailing whitespace in {whitespace_fixed} file(s)")
    print(f"Fixed long lines in {line_length_fixed} file(s)")
    print(f"Fixed unused imports in {imports_fixed} file(s)")