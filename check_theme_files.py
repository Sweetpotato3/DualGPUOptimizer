"""
Simple script to check if the theme module files exist
"""
from pathlib import Path

def check_files():
    """Check if the theme module files exist"""
    base_dir = Path(__file__).resolve().parent
    theme_dir = base_dir / "dualgpuopt" / "gui" / "theme"

    print(f"Checking theme directory: {theme_dir}")

    # List of files to check
    files = [
        "__init__.py",
        "colors.py",
        "dpi.py",
        "styling.py",
        "compatibility.py",
        "core.py",
        "compat.py",
        "README.md"
    ]

    all_exist = True

    # Check each file
    for file in files:
        file_path = theme_dir / file
        exists = file_path.exists()
        print(f"  {file}: {'✓' if exists else '✗'}")

        if not exists:
            all_exist = False
            continue

        # Show file size
        try:
            stats = file_path.stat()
            size_kb = stats.st_size / 1024
            print(f"    Size: {size_kb:.2f} KB")

            # Try to count lines with proper encoding
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                print(f"    Lines: {line_count}")
            except UnicodeDecodeError:
                print(f"    Lines: Could not count (encoding issue)")

        except Exception as e:
            print(f"    Error getting file stats: {e}")

    print("\nSummary:")
    print(f"All files exist: {'Yes' if all_exist else 'No'}")

    # Check original theme.py for reference
    original_theme = base_dir / "dualgpuopt" / "gui" / "theme.py"
    if original_theme.exists():
        print("\nOriginal theme.py:")
        print(f"  Exists: ✓")
        stats = original_theme.stat()
        print(f"  Size: {stats.st_size / 1024:.2f} KB")
        try:
            with open(original_theme, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            print(f"  Lines: {line_count}")
        except UnicodeDecodeError:
            print(f"  Lines: Could not count (encoding issue)")

if __name__ == "__main__":
    check_files()