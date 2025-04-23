"""
dualgpuopt.engine.pool
Hot-reload Engine cache (LRU) + watchdog.

Provides a caching layer for Engine instances with automatic health monitoring
and recovery. This allows immediate switching between models that are already
loaded, and automatic recovery if a backend crashes.

Usage
-----
from dualgpuopt.engine.pool import EnginePool
engine = EnginePool.get("/models/dolphin-34b-awq", quant="awq")
for tok in engine.stream("Hello"): ...
"""

from __future__ import annotations

import atexit
import contextlib
import socket
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Optional

from dualgpuopt.engine.backend import Engine
from dualgpuopt.services.event_bus import event_bus

# Optional imports for metrics and benchmarking
try:
    from dualgpuopt.engine.metrics import (
        record_model_load_time,
        update_model_metrics,
        update_pool_metrics,
    )

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

try:
    from dualgpuopt.engine.benchmark import record_benchmark

    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False

# Configuration constants
MAX_FAIL = 3  # health failures before reboot
CHECK_INT = 10.0  # seconds
CACHE_SIZE = 2  # LRU cache size
METRICS_UPDATE_INT = 30.0  # seconds

_pool_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=2)

# Stats tracking
_stats = {
    "hits": 0,
    "misses": 0,
    "total_loads": 0,
    "total_unloads": 0,
    "health_checks": 0,
    "health_failures": 0,
    "auto_restarts": 0,
}


@dataclass
class _Entry:
    """Internal cache entry for the LRU pool"""

    engine: Engine
    model_path: str
    kwargs: dict[str, Any]
    last_used: float = field(default_factory=time.time)
    fails: int = 0
    load_time: float = 0.0
    benchmarks: dict[str, float] = field(default_factory=dict)


class _LRUPool:
    """LRU dictionary: key=model_path, value=_Entry. Maintains order based on access."""

    def __init__(self, maxsize: int):
        self._max = maxsize
        self._data: OrderedDict[str, _Entry] = OrderedDict()

    @property
    def size(self) -> int:
        """Get the current size of the cache"""
        return len(self._data)

    @property
    def max_size(self) -> int:
        """Get the maximum size of the cache"""
        return self._max

    @max_size.setter
    def max_size(self, value: int):
        """Set the maximum size of the cache and evict if necessary"""
        if value < 1:
            raise ValueError("Cache size must be at least 1")
        old_max = self._max
        self._max = value
        # Evict if necessary
        if value < old_max:
            while len(self._data) > self._max:
                _, old = self._data.popitem(last=False)
                _executor.submit(old.engine.unload)
                _stats["total_unloads"] += 1

    def get(self, key: str) -> Optional[_Entry]:
        """Get an entry from the cache and update its position in the LRU order"""
        ent = self._data.get(key)
        if ent:
            ent.last_used = time.time()
            self._data.move_to_end(key)
        return ent

    def put(self, key: str, val: _Entry):
        """Add an entry to the cache, evicting oldest entries if necessary"""
        self._data[key] = val
        self._data.move_to_end(key)
        if len(self._data) > self._max:
            _, old = self._data.popitem(last=False)
            _executor.submit(old.engine.unload)
            _stats["total_unloads"] += 1

    def values(self):
        """Get all entries in the cache"""
        return list(self._data.values())

    def keys(self):
        """Get all keys in the cache"""
        return list(self._data.keys())

    def remove(self, key: str):
        """Remove an entry from the cache"""
        if key in self._data:
            entry = self._data.pop(key)
            _executor.submit(entry.engine.unload)
            _stats["total_unloads"] += 1
            return True
        return False

    def clear(self):
        """Clear all entries from the cache"""
        keys = list(self._data.keys())
        for key in keys:
            self.remove(key)


class EnginePool:
    """
    Manages a pool of Engine instances with LRU caching and health monitoring.

    The pool maintains a cache of loaded models for immediate reuse. When a new model
    is requested, it's either retrieved from the cache or loaded and added to the cache.

    Health monitoring periodically checks each loaded model and automatically restarts
    any that have failed.
    """

    _cache = _LRUPool(CACHE_SIZE)
    _watch_started = False
    _metrics_update_started = False

    @classmethod
    def get(cls, model_path: str, **kwargs) -> Engine:
        """
        Get an Engine instance for the given model, either from cache or newly loaded.

        Args:
        ----
            model_path: Path to the model file or HF model identifier
            **kwargs: Arguments to pass to the engine's load method

        Returns:
        -------
            A ready-to-use Engine instance
        """
        with _pool_lock:
            # Try to get from cache
            ent = cls._cache.get(model_path)
            if ent and cls._healthy(ent):
                _stats["hits"] += 1
                return ent.engine

            # Count as a miss
            _stats["misses"] += 1

            # If unhealthy, unload it
            if ent:
                _executor.submit(ent.engine.unload)
                _stats["total_unloads"] += 1

            # Create new engine
            eng = Engine()

            # Load in executor thread but wait for completion
            start_time = time.time()
            _executor.submit(eng.load, model_path, **kwargs).result()
            load_time = time.time() - start_time
            _stats["total_loads"] += 1

            # Record metrics
            if METRICS_AVAILABLE:
                try:
                    backend_cls = eng.backend.__class__.__name__
                    record_model_load_time(model_path, backend_cls, load_time)
                except Exception:
                    pass

            # Add to cache
            ent = _Entry(
                engine=eng,
                model_path=model_path,
                kwargs=kwargs,
                load_time=load_time,
            )
            cls._cache.put(model_path, ent)

            # Start watchdog if not already running
            cls._start_watchdog()

            # Start metrics update thread if not already running
            if METRICS_AVAILABLE and not cls._metrics_update_started:
                cls._start_metrics_update()

            return eng

    @classmethod
    def evict(cls, model_path: str) -> bool:
        """
        Explicitly remove a model from the cache

        Args:
        ----
            model_path: Path to the model to evict

        Returns:
        -------
            True if the model was found and evicted, False otherwise
        """
        with _pool_lock:
            return cls._cache.remove(model_path)

    @classmethod
    def clear(cls) -> None:
        """Remove all models from the cache"""
        with _pool_lock:
            cls._cache.clear()

    @classmethod
    def get_stats(cls) -> dict[str, Any]:
        """
        Get statistics about the cache

        Returns
        -------
            A dictionary of stats including:
            - cache_size: Current number of models in cache
            - max_size: Maximum cache size
            - hit_rate: Cache hit rate as a percentage
            - models: List of cached model paths
            - total_loads: Total number of model loads
            - total_unloads: Total number of model unloads
            - hits: Number of cache hits
            - misses: Number of cache misses
            - health_checks: Number of health checks performed
            - health_failures: Number of health check failures
            - auto_restarts: Number of automatic restarts
        """
        with _pool_lock:
            # Calculate hit rate
            total = _stats["hits"] + _stats["misses"]
            hit_rate = (_stats["hits"] / total * 100) if total > 0 else 0

            # Get models currently in cache
            models = cls._cache.keys()

            # Combine all stats
            return {
                "cache_size": cls._cache.size,
                "max_size": cls._cache.max_size,
                "hit_rate": hit_rate,
                "models": models,
                **_stats,
            }

    @classmethod
    def set_max_size(cls, size: int) -> None:
        """
        Set the maximum cache size

        Args:
        ----
            size: New maximum size (must be at least 1)
        """
        with _pool_lock:
            cls._cache.max_size = size

    @classmethod
    def record_benchmark(cls, model_path: str, tokens_per_second: float, **kwargs) -> None:
        """
        Record a benchmark for a model

        Args:
        ----
            model_path: Path to the model
            tokens_per_second: Tokens per second for the model
            **kwargs: Additional benchmark metrics
        """
        if not BENCHMARK_AVAILABLE:
            return

        with _pool_lock:
            # Find the model in the cache
            ent = cls._cache.get(model_path)
            if not ent:
                return

            try:
                # Get backend type
                backend_cls = ent.backend.__class__.__name__

                # Update benchmarks in entry
                ent.benchmarks["tokens_per_second"] = tokens_per_second
                for key, value in kwargs.items():
                    ent.benchmarks[key] = value

                # Record benchmark in database
                record_benchmark(model_path, backend_cls, tokens_per_second, **kwargs)

                # Update prometheus metrics if available
                if METRICS_AVAILABLE:
                    update_model_metrics(
                        model_path,
                        backend_cls,
                        tokens_per_second,
                        kwargs.get("memory_used"),
                        kwargs.get("gpu_utilization"),
                    )
            except Exception:
                pass

    @staticmethod
    def _healthy(ent: _Entry) -> bool:
        """Check if an engine is healthy by pinging its backend"""
        _stats["health_checks"] += 1
        try:
            result = _ping_backend(ent.engine)
            if not result:
                _stats["health_failures"] += 1
            return result
        except Exception:
            _stats["health_failures"] += 1
            return False

    @classmethod
    def _watch(cls):
        """Watchdog thread that monitors engine health and restarts failing engines"""
        while True:
            time.sleep(CHECK_INT)
            with _pool_lock:
                for ent in cls._cache.values():
                    if cls._healthy(ent):
                        ent.fails = 0
                        continue

                    ent.fails += 1
                    if ent.fails >= MAX_FAIL:
                        # Publish alert
                        event_bus.publish(
                            "alert",
                            {
                                "level": "CRITICAL",
                                "message": f"Backend restart: {ent.engine.backend.__class__.__name__}",
                            },
                        )

                        # Restart engine
                        _executor.submit(ent.engine.unload).result()
                        start_time = time.time()
                        _executor.submit(ent.engine.load, ent.model_path, **ent.kwargs).result()
                        ent.load_time = time.time() - start_time
                        ent.fails = 0
                        _stats["auto_restarts"] += 1

    @classmethod
    def _update_metrics(cls):
        """Update metrics periodically"""
        while True:
            time.sleep(METRICS_UPDATE_INT)
            try:
                if METRICS_AVAILABLE:
                    stats = cls.get_stats()
                    update_pool_metrics(stats)
            except Exception:
                pass

    @classmethod
    def _start_watchdog(cls):
        """Start the watchdog thread if not already running"""
        if cls._watch_started:
            return
        t = threading.Thread(target=cls._watch, daemon=True)
        t.start()
        cls._watch_started = True

    @classmethod
    def _start_metrics_update(cls):
        """Start the metrics update thread if not already running"""
        if cls._metrics_update_started:
            return
        t = threading.Thread(target=cls._update_metrics, daemon=True)
        t.start()
        cls._metrics_update_started = True


# ------------------------------------------------------------------ #
#           backend-specific health-probe helpers
# ------------------------------------------------------------------ #
def _port_open(port: int) -> bool:
    """Check if a port is open by attempting to connect to it"""
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _ping_backend(engine: Engine) -> bool:
    """Check if an engine's backend is healthy based on its type"""
    if not engine.backend:
        return False

    backend_cls = engine.backend.__class__.__name__

    if backend_cls == "VLLMBackend":
        return _port_open(8000)
    if backend_cls == "LlamaCppBackend":
        return _port_open(8080)

    # HFBackend has no server to check, assume healthy if object exists
    if backend_cls == "HFBackend":
        return True

    # Unknown backend, conservative assumption
    return False


# Register cleanup on process exit
@atexit.register
def _cleanup():
    """Clean up resources when the process exits"""
    for entry in EnginePool._cache.values():
        with contextlib.suppress(Exception):
            entry.engine.unload()
