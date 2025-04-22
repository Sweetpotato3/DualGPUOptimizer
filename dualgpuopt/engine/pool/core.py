"""
Thread‑safe LRU Engine pool with automatic watchdog and Prometheus metrics.
"""

from __future__ import annotations
import atexit, threading, time
from collections import OrderedDict, Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Iterable
from pathlib import Path

from dualgpuopt.engine.backend import LlamaCppBackend, VLLMBackend, HFBackend  # noqa
from dualgpuopt.engine.backend import Engine
from dualgpuopt.services.event_bus import publish

try:
    from dualgpuopt.engine.metrics import update_pool_metrics, record_model_load_time
    METRICS = True
except ImportError:
    METRICS = False

MAX_FAIL = 3
CHECK_INT = 10.0
CACHE_SIZE = 2

_executor = ThreadPoolExecutor(max_workers=4)
_lock = threading.RLock()


@dataclass
class _Entry:
    engine: Engine
    kwargs: Dict[str, Any]
    last_used: float = field(default_factory=time.time)
    fails: int = 0
    load_time: float = 0.0


class _LRU:
    def __init__(self, maxsize: int):
        self._max = maxsize
        self._data: OrderedDict[str, _Entry] = OrderedDict()

    @property
    def maxsize(self): return self._max
    @maxsize.setter
    def maxsize(self, v): self._max = max(1, v)

    def get(self, k: str) -> Optional[_Entry]:
        ent = self._data.get(k)
        if ent:
            ent.last_used = time.time()
            self._data.move_to_end(k)
        return ent

    def put(self, k: str, ent: _Entry):
        self._data[k] = ent
        self._data.move_to_end(k)
        while len(self._data) > self._max:
            _, old = self._data.popitem(last=False)
            _executor.submit(old.engine.unload)

    def pop(self, k: str):
        ent = self._data.pop(k, None)
        if ent:
            _executor.submit(ent.engine.unload)

    def items(self) -> Iterable[tuple[str, _Entry]]: return list(self._data.items())


class EnginePool:
    _cache = _LRU(CACHE_SIZE)
    _stats = Counter()
    _watch_started = False

    # ---------- public ----------
    @classmethod
    def get(cls, model: str, **kw) -> Engine:
        with _lock:
            ent = cls._cache.get(model)
        if ent and ent.engine.backend.health():          # no lock while pinging
            with _lock: cls._stats["hits"] += 1
            return ent.engine

        with _lock: cls._stats["misses"] += 1

        if ent:  # unhealthy
            cls._cache.pop(model)

        eng = Engine()
        t0 = time.time()
        _executor.submit(eng.load, model, **kw).result()
        load_time = time.time() - t0

        if METRICS:
            record_model_load_time(model, eng.backend.__class__.__name__, load_time)

        with _lock:
            cls._stats["total_loads"] += 1
            cls._cache.put(model, _Entry(eng, kw, load_time=load_time))
            cls._maybe_start_watchdog()
        return eng

    @classmethod
    def evict(cls, model: str): cls._cache.pop(model)
    @classmethod
    def clear(cls):                         # unload synchronously
        for k, ent in cls._cache.items():
            ent.engine.unload()
        cls._cache._data.clear()

    @classmethod
    def stats(cls) -> Dict[str, Any]:
        with _lock:
            miss = cls._stats["misses"]; hit = cls._stats["hits"]
            total = hit + miss
            return {**cls._stats,
                    "cache_size": len(cls._cache._data),
                    "hit_rate": 100 * hit / total if total else 0,
                    "models": list(cls._cache._data)}
    # ---------- internal ----------
    @classmethod
    def _maybe_start_watchdog(cls):
        if cls._watch_started:
            return
        threading.Thread(target=cls._watch, daemon=True).start()
        cls._watch_started = True

    @classmethod
    def _watch(cls):
        while True:
            time.sleep(CHECK_INT)
            with _lock:
                cache_snapshot = list(cls._cache._data.items())
            for path, ent in cache_snapshot:
                if ent.engine.backend.health():
                    ent.fails = 0
                    continue
                ent.fails += 1
                with _lock: cls._stats["health_failures"] += 1
                if ent.fails >= MAX_FAIL:
                    publish("alert", {"level": "CRITICAL",
                                      "message": f"Restarting backend for {Path(path).name}"})
                    ent.engine.unload()
                    _executor.submit(ent.engine.load, path, **ent.kwargs).result()
                    ent.fails = 0
                    with _lock: cls._stats["auto_restarts"] += 1
            if METRICS:
                update_pool_metrics(cls.stats())


# graceful shutdown
@atexit.register
def _shutdown():
    _executor.shutdown(wait=True)
    for _, ent in EnginePool._cache.items():
        ent.engine.unload() 