"""
dualgpuopt.telemetry.sample
DataClass for telemetry sample messages with named fields.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(slots=True)
class TelemetrySample:
    """Represents a telemetry metric with its current value and historical data."""

    name: str
    value: float
    series: Tuple[Tuple[float, float], ...]
