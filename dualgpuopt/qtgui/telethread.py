"""
Thread-safe telemetry worker for Qt.

This module provides a QThread-based worker for collecting and distributing
telemetry data in a thread-safe manner, using Qt signals to communicate
with the UI thread.
"""

from __future__ import annotations

import logging
import time

from PySide6.QtCore import QObject, QThread, Signal, Slot

# Import GPUMetrics class directly from the module where it's defined
# This is a more reliable approach than depending on __init__.py exports
import dualgpuopt.telemetry as telemetry_module

# Import existing telemetry components
# Fix the import for GPUMetrics - it's directly in telemetry.py, not in telemetry/__init__.py
from dualgpuopt.telemetry import get_telemetry_service
from dualgpuopt.telemetry_history import hist

# If the above import fails, try direct import from the file
if not hasattr(telemetry_module, "GPUMetrics"):
    # Get the directory containing the dualgpuopt package
    import importlib.util
    import os

    # Try to import GPUMetrics directly from telemetry.py
    telemetry_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "telemetry.py"
    )
    if os.path.exists(telemetry_path):
        spec = importlib.util.spec_from_file_location("telemetry_direct", telemetry_path)
        telemetry_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(telemetry_module)

# Define GPUMetrics locally as a fallback if all else fails
if not hasattr(telemetry_module, "GPUMetrics"):
    from dataclasses import dataclass

    @dataclass
    class GPUMetrics:
        """Fallback GPUMetrics class if import fails"""

        gpu_id: int
        name: str = "Unknown"
        utilization: int = 0
        memory_used: int = 0
        memory_total: int = 0
        temperature: int = 0
        power_usage: float = 0.0
        power_limit: float = 0.0
        fan_speed: int = 0
        clock_sm: int = 0
        clock_memory: int = 0
        pcie_tx: int = 0
        pcie_rx: int = 0
        timestamp: float = 0.0
        error_state: bool = True

        @property
        def memory_percent(self) -> float:
            """Return memory usage as percentage"""
            if self.memory_total == 0:
                return 0.0
            return (self.memory_used / self.memory_total) * 100.0

        @property
        def power_percent(self) -> float:
            """Return power usage as percentage of limit"""
            if self.power_limit == 0:
                return 0.0
            return (self.power_usage / self.power_limit) * 100.0
else:
    GPUMetrics = telemetry_module.GPUMetrics

# Configure logger
logger = logging.getLogger(__name__)


class TeleWorker(QObject):
    """
    Worker that collects telemetry data and emits signals when updates occur.

    This runs in a separate thread and converts the telemetry data into
    signals that can be safely consumed by Qt widgets in the main thread.
    """

    # Signals
    gpu_metrics_updated = Signal(dict)  # Full GPU metrics dict
    metric_updated = Signal(str, float)  # Single metric update (name, value)
    alert_triggered = Signal(str, str)  # Alert (level, message)

    def __init__(self, interval: float = 0.8):
        """
        Initialize the telemetry worker.

        Args:
        ----
            interval: Polling interval in seconds
        """
        super().__init__()
        self.interval = interval
        self.running = False
        self._telemetry = None  # Will be initialized in run()

    @Slot()
    def start_collection(self):
        """Start collecting telemetry data in a loop."""
        self.running = True

        # Initialize telemetry service
        try:
            self._telemetry = get_telemetry_service()
            if not self._telemetry:
                logger.error("Failed to initialize telemetry service")
                return
        except Exception as e:
            logger.error(f"Error initializing telemetry service: {e}")
            return

        logger.info(f"Telemetry worker started with interval: {self.interval}s")

        while self.running:
            try:
                # Get latest metrics
                metrics = self._telemetry.get_metrics()
                if metrics:
                    # Emit the full metrics update
                    self.gpu_metrics_updated.emit(metrics)

                    # Process metrics for each GPU and maintain history
                    self._process_metrics(metrics)

                # Sleep for the specified interval
                time.sleep(self.interval)

            except Exception as e:
                logger.error(f"Error in telemetry collection: {e}")
                time.sleep(self.interval * 2)  # Back off on error

    def _process_metrics(self, metrics: dict[int, GPUMetrics]):
        """Process metrics and emit individual updates."""
        if not metrics:
            return

        # Process metrics for each GPU
        for gpu_id, gpu_metrics in metrics.items():
            # Add to history and emit individual metrics
            for name, value in [
                (f"util_{gpu_id}", gpu_metrics.utilization),
                (f"vram_{gpu_id}", gpu_metrics.memory_percent),
                (f"temp_{gpu_id}", gpu_metrics.temperature),
                (f"power_{gpu_id}", gpu_metrics.power_percent),
            ]:
                # Update history buffer
                hist.push(name, value)

                # Emit signal for this metric
                self.metric_updated.emit(name, value)

            # Check for alerts based on GPU metrics
            self._check_alerts(gpu_id, gpu_metrics)

        # Also calculate and emit aggregate metrics
        if len(metrics) > 0:
            # Average utilization across all GPUs
            avg_util = sum(m.utilization for m in metrics.values()) / len(metrics)
            hist.push("util_avg", avg_util)
            self.metric_updated.emit("util_avg", avg_util)

            # Average memory usage across all GPUs
            avg_mem = sum(m.memory_percent for m in metrics.values()) / len(metrics)
            hist.push("vram_avg", avg_mem)
            self.metric_updated.emit("vram_avg", avg_mem)

    def _check_alerts(self, gpu_id: int, metrics: GPUMetrics):
        """Check metrics against thresholds and emit alerts if needed."""
        # EMERGENCY alerts (highest priority)
        if metrics.memory_percent >= 95 or metrics.temperature >= 90:
            msg = f"EMERGENCY: GPU {gpu_id} - "
            if metrics.memory_percent >= 95:
                msg += f"Memory at {metrics.memory_percent:.1f}% "
            if metrics.temperature >= 90:
                msg += f"Temperature at {metrics.temperature}°C "
            self.alert_triggered.emit("EMERGENCY", msg.strip())

        # CRITICAL alerts
        elif (
            metrics.memory_percent >= 90 or metrics.temperature >= 80 or metrics.power_percent >= 98
        ):
            msg = f"CRITICAL: GPU {gpu_id} - "
            if metrics.memory_percent >= 90:
                msg += f"Memory at {metrics.memory_percent:.1f}% "
            if metrics.temperature >= 80:
                msg += f"Temperature at {metrics.temperature}°C "
            if metrics.power_percent >= 98:
                msg += f"Power at {metrics.power_percent:.1f}% "
            self.alert_triggered.emit("CRITICAL", msg.strip())

        # WARNING alerts
        elif (
            metrics.memory_percent >= 75 or metrics.temperature >= 70 or metrics.power_percent >= 90
        ):
            msg = f"WARNING: GPU {gpu_id} - "
            if metrics.memory_percent >= 75:
                msg += f"Memory at {metrics.memory_percent:.1f}% "
            if metrics.temperature >= 70:
                msg += f"Temperature at {metrics.temperature}°C "
            if metrics.power_percent >= 90:
                msg += f"Power at {metrics.power_percent:.1f}% "
            self.alert_triggered.emit("WARNING", msg.strip())

    def stop(self):
        """Stop the telemetry collection."""
        self.running = False
        logger.info("Telemetry worker stopping")


def create_telemetry_thread() -> tuple[QThread, TeleWorker]:
    """
    Create and start a telemetry thread with worker.

    Returns
    -------
        Tuple containing (QThread, TeleWorker)
    """
    # Create thread and worker
    thread = QThread()
    worker = TeleWorker()

    # Move worker to thread
    worker.moveToThread(thread)

    # Connect signals and slots
    thread.started.connect(worker.start_collection)

    # Start the thread
    thread.start()

    return thread, worker
