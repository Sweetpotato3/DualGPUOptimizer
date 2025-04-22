"""
Hugging Face search & streamed download with resume + SHA‑256 check.
"""

from __future__ import annotations

import functools
import hashlib
import os
import pathlib
import shutil
from typing import Any, Callable, Dict, List

import requests

_API = "https://huggingface.co/api/models"
_TOKEN = os.getenv("HF_TOKEN")
_HDR = {"Authorization": f"Bearer {_TOKEN}"} if _TOKEN else {}


@functools.lru_cache(maxsize=128)
def search(text: str, limit: int = 30) -> List[Dict[str, Any]]:
    r = requests.get(_API, params={"search": text, "limit": limit}, headers=_HDR, timeout=20)
    r.raise_for_status()
    return [
        {
            "id": m["modelId"],
            "downloads": m.get("downloads", 0),
            "size": next(
                (
                    f["size"]
                    for f in m["siblings"]
                    if f["rfilename"].endswith((".gguf", ".safetensors", ".bin"))
                ),
                None,
            ),
            "sha": {f["rfilename"]: f.get("sha256") for f in m["siblings"]},
        }
        for m in r.json()
    ]


def download(
    model: str, pattern: str, dest: pathlib.Path, progress: Callable[[int, int], None] | None = None
) -> pathlib.Path:
    meta = requests.get(f"{_API}/{model}", headers=_HDR, timeout=20).json()
    files = [f for f in meta["siblings"] if f["rfilename"].endswith(pattern)]
    f = files[0]
    size, sha = f["size"], f.get("sha256")
    url = f"https://huggingface.co/{model}/resolve/main/{f['rfilename']}"
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f["rfilename"]
    part = out.with_suffix(out.suffix + ".part")
    downloaded = part.stat().st_size if part.exists() else 0
    mode = "ab" if downloaded else "wb"
    hdr = dict(_HDR)
    hdr["Range"] = f"bytes={downloaded}-"
    with requests.get(url, headers=hdr, stream=True, timeout=60) as r, open(part, mode) as fh:
        r.raise_for_status()
        for chunk in r.iter_content(64 << 10):
            fh.write(chunk)
            downloaded += len(chunk)
            if progress:
                progress(downloaded, size)
    if sha and hashlib.sha256(open(part, "rb").read()).hexdigest() != sha:
        raise RuntimeError("SHA‑256 mismatch! Download corrupted.")
    shutil.move(part, out)
    return out
