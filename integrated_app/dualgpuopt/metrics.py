#!/usr/bin/env python3
"""
Optional Prometheus metrics (no hard dependency).

Importing this module never raises ImportError; if `prometheus_client`
is missing, stub collectors discard data silently.
"""
from __future__ import annotations
import types, typing as _t

try:
    from prometheus_client import Counter, Histogram  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    def _noop(*_a: _t.Any, **_kw: _t.Any):  # noqa: D401 – internal stub
        class _Dummy:  # pylint: disable=too-few-public-methods
            def labels(self, *args: _t.Any, **kw: _t.Any): return self
            def inc(self, *_a: _t.Any): ...
            def observe(self, *_a: _t.Any): ...
        return _Dummy()

    Counter = Histogram = _noop  # type: ignore[misc,assignment]

BATCH_LAT = Histogram("dgp_batch_latency_ms", "End‑to‑end batch time", ["bucket"])
QUEUE_DEPTH = Counter("dgp_enqueued_total", "Requests enqueued", ["bucket"]) 