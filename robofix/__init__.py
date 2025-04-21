from __future__ import annotations
from pathlib import Path
from typing import Tuple

from .core import clean_and_wrap, ensure_pass
from .config import Settings


def clean_code(text: str, settings: Settings) -> str:
    """Return cleaned code (no I/O)."""
    lines = clean_and_wrap(text.splitlines(), settings.max_line)
    return "\n".join(lines)


def repair_code(path: Path, settings: Settings) -> Tuple[bool, str, int]:
    """
    Attempt AST‑aware 'pass' insertion for the two common syntax errors.
    Returns (fixed?, message, line_number)
    """
    ok, msg, line = ensure_pass(path, settings)
    return ok, msg, line 