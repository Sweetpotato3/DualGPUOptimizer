"""
dualgpuopt.engine.metrics
Prometheus metrics for the EnginePool and model benchmarks.

Exports metrics for monitoring the engine pool performance, model loading times,
health check status, and other key performance indicators.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

try:
    import prometheus_client as prom
    from prometheus_client import Counter, Gauge, Histogram, Summary

    PROMETHEUS_AVAILABLE = True
except ImportError:
    logging.warning("prometheus_client not available, metrics will be disabled")
    PROMETHEUS_AVAILABLE = False

    # Create dummy metrics classes for type checking
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, val=1):
            pass

        def labels(self, **kwargs):
            return self

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def set(self, val):
            pass

        def inc(self, val=1):
            pass

        def dec(self, val=1):
            pass

        def labels(self, **kwargs):
            return self

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, val):
            pass

        def labels(self, **kwargs):
            return self

    class Summary:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, val):
            pass

        def labels(self, **kwargs):
            return self


# Initialize logger
logger = logging.getLogger("dualgpuopt.engine.metrics")

# Metrics namespace prefix
NAMESPACE = "dualgpuopt"

# Engine Pool metrics
if PROMETHEUS_AVAILABLE:
    # Engine pool metrics
    POOL_MODELS = Gauge(
        f"{NAMESPACE}_engine_pool_models",
        "Number of models currently in the engine pool",
        ["status"],  # active, total
    )

    POOL_SIZE = Gauge(
        f"{NAMESPACE}_engine_pool_size",
        "Current size of the engine pool cache",
    )

    POOL_MAX_SIZE = Gauge(
        f"{NAMESPACE}_engine_pool_max_size",
        "Maximum size of the engine pool cache",
    )

    POOL_HITS = Counter(
        f"{NAMESPACE}_engine_pool_hits_total",
        "Total number of cache hits in the engine pool",
    )

    POOL_MISSES = Counter(
        f"{NAMESPACE}_engine_pool_misses_total",
        "Total number of cache misses in the engine pool",
    )

    POOL_EVICTIONS = Counter(
        f"{NAMESPACE}_engine_pool_evictions_total",
        "Total number of model evictions from the engine pool",
    )

    # Health check metrics
    HEALTH_CHECKS = Counter(
        f"{NAMESPACE}_engine_health_checks_total",
        "Total number of health checks performed",
    )

    HEALTH_FAILURES = Counter(
        f"{NAMESPACE}_engine_health_failures_total",
        "Total number of health check failures",
    )

    AUTO_RESTARTS = Counter(
        f"{NAMESPACE}_engine_auto_restarts_total",
        "Total number of automatic engine restarts",
    )

    # Model metrics
    MODEL_LOAD_TIME = Histogram(
        f"{NAMESPACE}_model_load_seconds",
        "Time taken to load a model",
        ["model_name", "backend"],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
    )

    MODEL_TOKENS_PER_SECOND = Gauge(
        f"{NAMESPACE}_model_tokens_per_second",
        "Tokens per second for a model",
        ["model_name", "backend"],
    )

    MODEL_MEMORY_USAGE = Gauge(
        f"{NAMESPACE}_model_memory_mb",
        "Memory usage in MB for a model",
        ["model_name", "backend"],
    )

    MODEL_GPU_UTIL = Gauge(
        f"{NAMESPACE}_model_gpu_utilization",
        "GPU utilization percentage for a model",
        ["model_name", "backend"],
    )

    # Initialize HTTP server if not already initialized
    PORT = int(os.getenv("DUALGPUOPT_METRICS_PORT", 0))
    if PORT and not getattr(prom, "_dgp_srv_started", False):
        prom.start_http_server(PORT)
        prom._dgp_srv_started = True
        logger.info("Prometheus on %d", PORT)


def _label(path: str) -> str:
    name = os.path.basename(path)
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return name[-32:]  # cap label length


def update_pool_metrics(stats: dict) -> None:
    """
    Update EnginePool metrics from stats dictionary.

    Args:
    ----
        stats: Dictionary of stats from EnginePool.get_stats()
    """
    if not PROMETHEUS_AVAILABLE:
        return

    try:
        # Update pool metrics
        POOL_MODELS.labels(status="active").set(stats["cache_size"])
        POOL_SIZE.set(stats["cache_size"])
        POOL_MAX_SIZE.set(stats["max_size"])

        # Update counters only if they've changed from our internal state
        global _last_hits, _last_misses, _last_unloads, _last_health_checks
        global _last_health_failures, _last_restarts

        # Initialize globals if needed
        if not globals().get("_last_hits"):
            _last_hits = 0
            _last_misses = 0
            _last_unloads = 0
            _last_health_checks = 0
            _last_health_failures = 0
            _last_restarts = 0

        # Update hit/miss counters
        if stats["hits"] > _last_hits:
            POOL_HITS.inc(stats["hits"] - _last_hits)
            _last_hits = stats["hits"]

        if stats["misses"] > _last_misses:
            POOL_MISSES.inc(stats["misses"] - _last_misses)
            _last_misses = stats["misses"]

        if stats["total_unloads"] > _last_unloads:
            POOL_EVICTIONS.inc(stats["total_unloads"] - _last_unloads)
            _last_unloads = stats["total_unloads"]

        # Update health check counters
        if stats["health_checks"] > _last_health_checks:
            HEALTH_CHECKS.inc(stats["health_checks"] - _last_health_checks)
            _last_health_checks = stats["health_checks"]

        if stats["health_failures"] > _last_health_failures:
            HEALTH_FAILURES.inc(stats["health_failures"] - _last_health_failures)
            _last_health_failures = stats["health_failures"]

        if stats["auto_restarts"] > _last_restarts:
            AUTO_RESTARTS.inc(stats["auto_restarts"] - _last_restarts)
            _last_restarts = stats["auto_restarts"]

    except Exception as e:
        logger.error(f"Error updating pool metrics: {e}")


def record_model_load_time(model_name: str, backend: str, load_time: float) -> None:
    """
    Record model load time metric.

    Args:
    ----
        model_name: The name or path of the model
        backend: The backend used (e.g., "vllm", "llama.cpp", "hf")
        load_time: Time in seconds taken to load the model
    """
    if not PROMETHEUS_AVAILABLE:
        return

    try:
        # Extract the model name without path for cleaner labels
        model_short_name = _label(model_name)
        MODEL_LOAD_TIME.labels(model_name=model_short_name, backend=backend).observe(load_time)
    except Exception as e:
        logger.error(f"Error recording model load time: {e}")


def update_model_metrics(
    model_name: str,
    backend: str,
    tokens_per_second: float,
    memory_mb: Optional[float] = None,
    gpu_util: Optional[float] = None,
) -> None:
    """
    Update model performance metrics.

    Args:
    ----
        model_name: The name or path of the model
        backend: The backend used (e.g., "vllm", "llama.cpp", "hf")
        tokens_per_second: Tokens per second for the model
        memory_mb: Optional memory usage in MB
        gpu_util: Optional GPU utilization percentage
    """
    if not PROMETHEUS_AVAILABLE:
        return

    try:
        # Extract the model name without path for cleaner labels
        model_short_name = _label(model_name)

        # Update performance metrics
        MODEL_TOKENS_PER_SECOND.labels(model_name=model_short_name, backend=backend).set(
            tokens_per_second
        )

        if memory_mb is not None:
            MODEL_MEMORY_USAGE.labels(model_name=model_short_name, backend=backend).set(memory_mb)

        if gpu_util is not None:
            MODEL_GPU_UTIL.labels(model_name=model_short_name, backend=backend).set(gpu_util)
    except Exception as e:
        logger.error(f"Error updating model metrics: {e}")


# Start metrics server if prometheus_client is available and this module is imported directly
if __name__ == "__main__" and PROMETHEUS_AVAILABLE:
    logger.info("Starting metrics server as standalone module")
    metrics_port = int(os.environ.get("DUALGPUOPT_METRICS_PORT", 8005))
    prom.start_http_server(metrics_port)
    logger.info(f"Prometheus metrics server started on port {metrics_port}")

    # Keep the server running
    while True:
        time.sleep(1)
