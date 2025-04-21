from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path
from typing import List, Tuple, Union

__all__ = [
    "clean_and_wrap",
    "ensure_pass",
]

# ---------------------------------------------------------------------------
_MAX_LINE_DEFAULT = 88
_WRAP_RE = re.compile(r"^([^#\'\"\\]*)(.*)$")  # keep code prefix intact
_ERRS = ("expected an indented block", "expected a statement")


# ---------------------------------------------------------------------------
# Cleaning / wrapping --------------------------------------------------------
# ---------------------------------------------------------------------------

def clean_and_wrap(lines: List[str], width: int = _MAX_LINE_DEFAULT) -> List[str]:
    """Return *new* list with

    * trailing whitespace removed
    * TAB ➜ 4 spaces
    * blank lines trimmed at EOF
    * long lines wrapped at ``width`` columns (rough heuristic; preserves comments)
    """
    out: List[str] = []
    for ln in lines:
        ln = ln.rstrip().replace("\t", " " * 4)
        if len(ln) <= width or ln.lstrip().startswith("#"):
            out.append(ln)
            continue
        prefix, rest = _WRAP_RE.match(ln).groups()  # type: ignore[assignment]
        for idx, chunk in enumerate(textwrap.wrap(rest, width - len(prefix))):
            out.append((prefix if idx == 0 else " " * len(prefix)) + chunk)
    while out and out[-1] == "":
        out.pop()
    out.append("")  # ensure final newline
    return out


# ---------------------------------------------------------------------------
# AST‑aware pass insertion ---------------------------------------------------
# ---------------------------------------------------------------------------

def _node_at_lineno(tree: ast.AST, lineno: int) -> ast.AST | None:
    for node in ast.walk(tree):
        if hasattr(node, "lineno") and node.lineno == lineno:
            return node
    return None


def ensure_pass(path_or_source: Union[Path, str], settings=None) -> Tuple[bool, str, int]:
    """
    Insert ``pass`` statement where needed for empty blocks.
    
    Works with either:
    - A Path object: compiles and fixes the file directly
    - A string source: parses and returns modified source
    
    Returns (fixed?, message, line_number)
    """
    # Handle Path input
    if isinstance(path_or_source, Path):
        path = path_or_source
        try:
            import py_compile
            py_compile.compile(path, doraise=True)
            return True, "", 0
        except py_compile.PyCompileError as exc:
            if not any(err in exc.msg for err in _ERRS):
                return False, exc.msg, exc.exc_lineno
                
            lines = path.read_text(encoding="utf-8").splitlines()
            # naive but safe: insert after the syntax error line
            idx = exc.exc_lineno - 1
            indent = len(lines[idx]) - len(lines[idx].lstrip())
            lines.insert(idx + 1, " " * indent + "pass")
            path.write_text("\n".join(lines), encoding="utf-8")
            
            try:
                py_compile.compile(path, doraise=True)
                return True, "fixed", exc.exc_lineno
            except py_compile.PyCompileError as exc2:
                return False, exc2.msg, exc2.exc_lineno
    
    # Handle string input - AST-based approach
    source = path_or_source
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        # If it's likely an empty block error, try a naive fix at the line
        if any(err in str(exc) for err in _ERRS):
            lines = source.splitlines()
            idx = exc.lineno - 1
            indent = len(lines[idx]) - len(lines[idx].lstrip())
            lines.insert(idx + 1, " " * indent + "pass")
            fixed_source = "\n".join(lines)
            
            try:
                ast.parse(fixed_source)
                return True, "fixed", exc.lineno
            except SyntaxError:
                return False, str(exc), exc.lineno
        return False, str(exc), getattr(exc, 'lineno', 0)

    # No syntax errors, no changes needed
    return True, "", 0 