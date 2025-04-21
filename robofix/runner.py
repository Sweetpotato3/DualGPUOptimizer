from __future__ import annotations

import logging
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

from .config import Settings
from .core import clean_and_wrap, ensure_pass

log = logging.getLogger("robofix")


def process(path: Path, cfg: Settings) -> Dict[str, int]:
    stats = {"changed": 0, "fixed": 0}
    # read using tokenize to respect encodings
    import tokenize

    with tokenize.open(path) as fh:
        original = fh.read().splitlines()

    cleaned = clean_and_wrap(original, cfg.max_line)
    if cleaned != original:
        stats["changed"] = 1
        if cfg.backup:
            dst = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, dst)
        tmp = Path(tempfile.mktemp(dir=str(path.parent)))
        tmp.write_text("\n".join(cleaned), encoding="utf-8")
        os.replace(tmp, path)

    ok, msg, line = ensure_pass(path, cfg)
    if not ok:
        log.warning(f"unfixed: {path} - {msg} at line {line}")
    else:
        if msg == "fixed":
            stats["fixed"] = 1
            log.info(f"fixed: {path} at line {line}")
    return stats


def run(paths: List[Path], cfg: Settings) -> Dict[str, int]:
    total = {"files": 0, "changed": 0, "fixed": 0}
    with ThreadPoolExecutor(max_workers=cfg.jobs) as pool:
        fut = {pool.submit(process, p, cfg): p for p in paths}
        for f in as_completed(fut):
            res = f.result()
            for k in res:
                if k in total:
                    total[k] += res[k]
    total["files"] = len(paths)
    return total 