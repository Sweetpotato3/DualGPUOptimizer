#!/usr/bin/env python3
"""
NVML‑based polling generator: yield dict every `interval` seconds.
"""
from __future__ import annotations
import time
import dataclasses as dc
import queue
import threading
import logging
from typing import Dict, List, Callable, Protocol, Optional, Any

# Import from our reorganized modules
from dualgpuopt.gpu_info import probe_gpus, GPU
from dualgpuopt.services.event_bus import event_bus, GPUMetricsEvent


@dc.dataclass(slots=True)
class Telemetry:
    """Container for telemetry data."""
    ts: float
    load: List[int]           # GPU utilization %
    mem_used: List[int]       # MiB
    pcie_rx: List[int]        # KiB/s
    pcie_tx: List[int]        # KiB/s
    temperature: List[int]    # °C
    power_usage: List[float]  # Watts
    memory_util: List[int]    # Memory utilization %
    fan_speed: List[int]      # Fan speed %
    graphics_clock: List[int] # MHz
    memory_clock: List[int]   # MHz


class TelemetryMiddleware(Protocol):
    """Protocol for telemetry middleware components."""

    def process(self, telemetry: Telemetry) -> None:
        """Process telemetry data."""
        ...


class EventBusMiddleware:
    """Middleware that publishes telemetry data to the event bus."""

    def __init__(self) -> None:
        """Initialize the middleware."""
        self.logger = logging.getLogger("dualgpuopt.telemetry.middleware")

    def process(self, telemetry: Telemetry) -> None:
        """Publish telemetry data to the event bus."""
        try:
            for i, (load, mem, temp, power, fan) in enumerate(zip(
                telemetry.load,
                telemetry.mem_used,
                telemetry.temperature,
                telemetry.power_usage,
                telemetry.fan_speed
            )):
                # We need to determine memory total, but it's not in the telemetry
                # object. This is an imperfect solution as we may not get the exact
                # total that was used to calculate, but it should be close enough
                gpus = probe_gpus()
                mem_total = 0
                if i < len(gpus):
                    mem_total = gpus[i].mem_total

                # Create and publish the GPU metrics event
                event = GPUMetricsEvent(
                    gpu_index=i,
                    utilization=float(load),
                    memory_used=mem,
                    memory_total=mem_total,
                    temperature=float(temp),
                    power_draw=power,
                    fan_speed=fan
                )
                event_bus.publish_typed(event)
        except Exception as e:
            self.logger.error(f"Error publishing telemetry to event bus: {e}")


class LoggingMiddleware:
    """Middleware that logs telemetry data for debugging."""

    def __init__(self) -> None:
        """Initialize the middleware."""
        self.logger = logging.getLogger("dualgpuopt.telemetry.logging")

    def process(self, telemetry: Telemetry) -> None:
        """Log telemetry data."""
        try:
            self.logger.debug(f"GPU metrics: load={telemetry.load}, temp={telemetry.temperature}")
        except Exception as e:
            self.logger.error(f"Error logging telemetry: {e}")


def _collect() -> Telemetry:
    """Collect telemetry data from all GPUs."""
    gpus = probe_gpus()
    load, mem = [], []
    rx, tx = [], []
    temperature = []
    power_usage = []
    memory_util = []
    fan_speed = []
    graphics_clock = []
    memory_clock = []

    try:
        import pynvml as nv
        nv.nvmlInit()

        try:
            for g in gpus:
                h = nv.nvmlDeviceGetHandleByIndex(g.index)

                # Basic metrics (always collected)
                util = nv.nvmlDeviceGetUtilizationRates(h)
                load.append(util.gpu)
                mem.append(g.mem_used)
                memory_util.append(util.memory)

                # PCIe throughput
                try:
                    bw = nv.nvmlDeviceGetPcieThroughput(h, nv.NVML_PCIE_UTIL_RX_BYTES)
                    bw2 = nv.nvmlDeviceGetPcieThroughput(h, nv.NVML_PCIE_UTIL_TX_BYTES)
                    rx.append(bw)
                    tx.append(bw2)
                except Exception:
                    rx.append(0)
                    tx.append(0)

                # Temperature
                try:
                    temp = nv.nvmlDeviceGetTemperature(h, nv.NVML_TEMPERATURE_GPU)
                    temperature.append(temp)
                except Exception:
                    temperature.append(0)

                # Power usage
                try:
                    power = nv.nvmlDeviceGetPowerUsage(h) / 1000.0  # Convert from mW to W
                    power_usage.append(round(power, 1))
                except Exception:
                    power_usage.append(0.0)

                # Fan speed
                try:
                    fan = nv.nvmlDeviceGetFanSpeed(h)
                    fan_speed.append(fan)
                except Exception:
                    fan_speed.append(0)

                # Clock speeds
                try:
                    g_clock = nv.nvmlDeviceGetClockInfo(h, nv.NVML_CLOCK_GRAPHICS)
                    graphics_clock.append(g_clock)

                    m_clock = nv.nvmlDeviceGetClockInfo(h, nv.NVML_CLOCK_MEM)
                    memory_clock.append(m_clock)
                except Exception:
                    graphics_clock.append(0)
                    memory_clock.append(0)
        finally:
            nv.nvmlShutdown()
    except Exception as e:
        # In case of any error with NVML, log it and continue with mock data
        logging.getLogger("dualgpuopt.telemetry").error(f"Error in telemetry collection: {e}")

        # If we have no data yet, add mock data for each GPU
        if not load and gpus:
            for _ in range(len(gpus)):
                load.append(10)
                mem.append(1024)
                rx.append(0)
                tx.append(0)
                temperature.append(50)
                power_usage.append(100.0)
                memory_util.append(5)
                fan_speed.append(30)
                graphics_clock.append(1500)
                memory_clock.append(7000)

    return Telemetry(
        time.time(),
        load,
        mem,
        rx,
        tx,
        temperature,
        power_usage,
        memory_util,
        fan_speed,
        graphics_clock,
        memory_clock
    )


# Global middleware registry
_middleware: List[TelemetryMiddleware] = []


def register_middleware(middleware: TelemetryMiddleware) -> None:
    """Register a middleware component to process telemetry data."""
    _middleware.append(middleware)


def unregister_middleware(middleware: TelemetryMiddleware) -> None:
    """Unregister a middleware component."""
    if middleware in _middleware:
        _middleware.remove(middleware)


def clear_middleware() -> None:
    """Clear all middleware components."""
    _middleware.clear()


def start_stream(interval: float=1.0) -> queue.Queue[Telemetry]:
    """
    Start collecting telemetry at the specified interval.

    Args:
        interval: Polling interval in seconds

    Returns:
        Queue of telemetry objects
    """
    q: queue.Queue[Telemetry] = queue.Queue()

    def run() -> None:
        while True:
            try:
                # Collect telemetry
                telemetry = _collect()

                # Put in queue for consumers
                q.put(telemetry)

                # Process through middleware pipeline
                for mw in _middleware:
                    try:
                        mw.process(telemetry)
                    except Exception as e:
                        logging.getLogger("dualgpuopt.telemetry").error(
                            f"Middleware error: {e}", exc_info=True
                        )
            except Exception as e:
                logging.getLogger("dualgpuopt.telemetry").error(
                    f"Telemetry collection error: {e}", exc_info=True
                )
            finally:
                time.sleep(interval)

    th = threading.Thread(target=run, daemon=True)
    th.start()
    return q


# Register default middleware
register_middleware(EventBusMiddleware())