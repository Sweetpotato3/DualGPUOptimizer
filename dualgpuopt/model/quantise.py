"""
AutoAWQ & llama‑cpp quant wrappers.
"""

from __future__ import annotations

import pathlib
import subprocess


def _run(cmd, tag):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"{tag} failed:\n{proc.stderr}")


def to_awq(fp16: pathlib.Path) -> pathlib.Path:
    out_dir = fp16.with_suffix(".awq")
    if out_dir.exists():
        return next(out_dir.glob("*awq.safetensors"))
    _run(["autoawq", "quantize", str(fp16), str(out_dir), "--wbits", "4"], "AWQ")
    return next(out_dir.glob("*awq.safetensors"))


def to_gguf(fp16: pathlib.Path) -> pathlib.Path:
    out = fp16.with_suffix(".gguf")
    if out.exists():
        return out
    _run(["llama-quant", "-i", str(fp16), "-o", str(out), "-f", "q4_0"], "GGUF")
    return out
