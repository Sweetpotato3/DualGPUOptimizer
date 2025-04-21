"""
dualgpuopt.telemetry_history
Thread-safe, in-memory time-series buffer for rolling 60 s telemetry.
"""
from __future__ import annotations
from collections import deque
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
import threading
import time
from typing import Deque, Tuple, Dict

SECONDS = 60


@dataclass(slots=True)
class SampleSeries:
    """Holds (timestamp, value) pairs, drops data older than SECONDS."""
    data: Deque[Tuple[float, float]] = field(default_factory=deque)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def push(self, value: float) -> None:
        now = time.monotonic()
        with self.lock:
            self.data.append((now, value))
            cutoff = now - SECONDS
            while self.data and self.data[0][0] < cutoff:
                self.data.popleft()

    def snapshot(self) -> Tuple[Tuple[float, float], ...]:
        now = time.monotonic()
        with self.lock:
            cutoff = now - SECONDS
            while self.data and self.data[0][0] < cutoff:
                self.data.popleft()
            return tuple(self.data)  # zero-copy immutable


class HistoryBuffer:
    """
    Global container mapping metric name -> SampleSeries.
    """
    def __init__(self) -> None:
        self._buf: Dict[str, SampleSeries] = defaultdict(SampleSeries)

    def push(self, metric: str, value: float) -> None:
        self._buf[metric].push(value)

    def snapshot(self, metric: str) -> Tuple[Tuple[float, float], ...]:
        return self._buf[metric].snapshot() 