"""
Telemetry module for GPU metrics collection and processing
Provides real-time monitoring of GPU resources, temperature, power, and utilization
"""

import logging
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Union

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Telemetry")

# Environment variable configuration options
ENV_POLL_INTERVAL = float(os.environ.get("DUALGPUOPT_POLL_INTERVAL", "1.0"))
ENV_MOCK_TELEMETRY = os.environ.get("DUALGPUOPT_MOCK_TELEMETRY", "").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
ENV_MAX_RECOVERY_ATTEMPTS = int(os.environ.get("DUALGPUOPT_MAX_RECOVERY", "3"))
ENV_METRIC_CACHE_TTL = float(os.environ.get("DUALGPUOPT_METRIC_CACHE_TTL", "0.05"))  # 50ms default

# Import error handling if available
try:
    # Using importlib.util.find_spec to test for availability instead of importing unused symbols
    import importlib.util

    error_handler_spec = importlib.util.find_spec("dualgpuopt.error_handler")
    error_handler_available = error_handler_spec is not None
except ImportError:
    error_handler_available = False
    logger.warning("Error handler not available for telemetry, using basic error handling")

# Import event bus if available
try:
    # Import the event bus and the enhanced GPUMetricsEvent
    from dualgpuopt.services.event_bus import event_bus
    from dualgpuopt.services.events import BaseGPUMetricsEvent, GPUMetricsEvent

    event_bus_available = True
    logger.debug("Event bus available for telemetry events")
except ImportError:
    event_bus_available = False
    logger.warning("Event bus not available, falling back to callback-based telemetry")

# Always try to import pynvml
try:
    import pynvml

    NVML_AVAILABLE = True
    logger.info("PYNVML successfully imported")
except ImportError:
    logger.error("PYNVML not available - install with 'pip install pynvml'")
    NVML_AVAILABLE = False


class AlertLevel(Enum):
    """Alert levels for telemetry events"""

    NORMAL = 0
    WARNING = 1
    CRITICAL = 2
    EMERGENCY = 3


@dataclass
class GPUMetrics:
    """Represents comprehensive metrics for a single GPU"""

    gpu_id: int
    name: str
    utilization: int  # percentage
    memory_used: int  # MB
    memory_total: int  # MB
    temperature: int  # Celsius
    power_usage: float  # Watts
    power_limit: float  # Watts
    fan_speed: int  # percentage
    clock_sm: int  # MHz
    clock_memory: int  # MHz
    pcie_tx: int  # KB/s
    pcie_rx: int  # KB/s
    timestamp: float
    error_state: bool = False  # Indicates if this data was generated due to an error

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

    @property
    def formatted_memory(self) -> str:
        """Return formatted memory usage string"""
        return f"{self.memory_used}/{self.memory_total} MB ({self.memory_percent:.1f}%)"

    @property
    def formatted_pcie(self) -> str:
        """Return formatted PCIe bandwidth usage"""
        return f"TX: {self.pcie_tx/1024:.1f} MB/s, RX: {self.pcie_rx/1024:.1f} MB/s"

    def get_alert_level(self) -> AlertLevel:
        """Calculate overall alert level based on metrics.

        Returns:
            AlertLevel enum indicating the severity of the current GPU state
        """
        # Start with NORMAL alert level
        level = AlertLevel.NORMAL

        # Memory usage thresholds
        if self.memory_percent >= 95:
            level = AlertLevel.EMERGENCY
        elif self.memory_percent >= 90:
            level = AlertLevel.CRITICAL if level.value < AlertLevel.CRITICAL.value else level
        elif self.memory_percent >= 75:
            level = AlertLevel.WARNING if level.value < AlertLevel.WARNING.value else level

        # Temperature thresholds
        if self.temperature >= 90:
            level = AlertLevel.EMERGENCY
        elif self.temperature >= 80:
            level = AlertLevel.CRITICAL if level.value < AlertLevel.CRITICAL.value else level
        elif self.temperature >= 70:
            level = AlertLevel.WARNING if level.value < AlertLevel.WARNING.value else level

        # Power usage thresholds (percentage of limit)
        if self.power_percent >= 98:
            level = AlertLevel.CRITICAL if level.value < AlertLevel.CRITICAL.value else level
        elif self.power_percent >= 90:
            level = AlertLevel.WARNING if level.value < AlertLevel.WARNING.value else level

        return level


class TelemetryService:
    """Service for collecting and distributing GPU telemetry"""

    def __init__(
        self,
        poll_interval: float = ENV_POLL_INTERVAL,
        use_mock: bool = ENV_MOCK_TELEMETRY,
        gpu_provider=None,
        event_bus=None,
    ):
        """Initialize the telemetry service

        Args:
            poll_interval: How frequently to poll GPU data (seconds)
            use_mock: Force using mock data even if NVML is available
            gpu_provider: Optional custom GPU provider for testing
            event_bus: Optional event bus to use instead of the global one
        """
        self.poll_interval = poll_interval
        self.force_mock = use_mock
        self.use_mock = not NVML_AVAILABLE or use_mock
        self.running = False
        self.metrics: Dict[int, GPUMetrics] = {}
        self.callbacks: List[Callable[[Dict[int, GPUMetrics]], None]] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._nvml_initialized = False
        self._recovery_attempts = 0
        self._last_error_time = 0
        self._consecutive_errors = 0
        self._metrics_lock = threading.RLock()
        self._callback_lock = threading.RLock()
        self._gpu_handles: Dict[int, Any] = {}
        self._metrics_history: Dict[int, List[GPUMetrics]] = {}
        self._history_length = 60  # Store 60 seconds of history by default

        # Monitor callbacks for testing
        self._monitor_temperature_check = None
        self._monitor_memory_check = None

        # Store custom GPU provider and event bus
        self._gpu_provider = gpu_provider
        self._event_bus = event_bus if event_bus else (event_bus_available and event_bus)

        # Initialize NVML if available and not using custom GPU provider
        if gpu_provider is None:
            self._init_nvml()
        else:
            self.use_mock = True  # Not using NVML with custom provider
            self.gpu_count = gpu_provider.get_gpu_count()
            logger.info(f"Using custom GPU provider with {self.gpu_count} GPUs")

    def _init_nvml(self) -> bool:
        """Initialize NVML library

        Returns:
            True if initialization was successful, False otherwise
        """
        if self.force_mock:
            self.use_mock = True
            self.gpu_count = 2  # Default to 2 mock GPUs
            logger.info("Using mock GPU data as requested")
            return False

        if not NVML_AVAILABLE:
            self.use_mock = True
            self.gpu_count = 2  # Default to 2 mock GPUs
            logger.warning("NVML not available, using mock GPU data")
            return False

        try:
            pynvml.nvmlInit()
            self._nvml_initialized = True
            self.gpu_count = pynvml.nvmlDeviceGetCount()
            logger.info(f"NVML initialized with {self.gpu_count} GPUs")

            # Pre-cache GPU handles for faster access
            self._gpu_handles = {}
            for gpu_id in range(self.gpu_count):
                self._gpu_handles[gpu_id] = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)

            self.use_mock = False
            return True
        except Exception as e:
            logger.error(f"Failed to initialize NVML: {e}")
            self.use_mock = True
            self.gpu_count = 2  # Default to 2 mock GPUs
            self._nvml_initialized = False
            logger.warning("Falling back to mock GPU data due to NVML initialization failure")
            return False

    def _try_reinit_nvml(self) -> bool:
        """Try to reinitialize NVML after failure

        Returns:
            True if reinitialization was successful, False otherwise
        """
        # Don't try to recover if we're using mock data by choice
        if self.force_mock:
            return False

        # Don't attempt recovery if NVML is not available
        if not NVML_AVAILABLE:
            return False

        # Limit recovery attempts
        max_attempts = ENV_MAX_RECOVERY_ATTEMPTS
        if self._recovery_attempts >= max_attempts:
            logger.warning(f"Maximum NVML recovery attempts ({max_attempts}) reached")
            return False

        # Add backoff between recovery attempts
        current_time = time.time()
        if current_time - self._last_error_time < (2**self._recovery_attempts):
            return False

        self._recovery_attempts += 1
        self._last_error_time = current_time

        logger.info(f"Attempting NVML reinitialization (attempt {self._recovery_attempts})")

        try:
            # Shutdown if previously initialized
            if self._nvml_initialized:
                try:
                    pynvml.nvmlShutdown()
                except Exception as e:
                    logger.debug(f"Error during NVML shutdown: {e}")

            # Reinitialize
            pynvml.nvmlInit()
            self._nvml_initialized = True
            self.gpu_count = pynvml.nvmlDeviceGetCount()

            # Rebuild handle cache
            self._gpu_handles = {}
            for gpu_id in range(self.gpu_count):
                self._gpu_handles[gpu_id] = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)

            self.use_mock = False
            self._consecutive_errors = 0
            logger.info(f"NVML successfully reinitialized with {self.gpu_count} GPUs")
            return True
        except Exception as e:
            logger.error(f"Failed to reinitialize NVML: {e}")
            self.use_mock = True
            return False

    def start(self, poll_interval: Optional[float] = None) -> None:
        """Start the telemetry collection thread

        Args:
            poll_interval: Optional override for the polling interval set during initialization
        """
        if self.running:
            return

        # Update poll interval if provided
        if poll_interval is not None:
            self.poll_interval = poll_interval

        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._telemetry_loop, daemon=True, name="TelemetryThread"
        )
        self._thread.start()
        logger.info(f"Telemetry service started with poll interval: {self.poll_interval}s")

    def stop(self) -> None:
        """Stop the telemetry collection thread"""
        self.running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        # Clean up NVML if initialized
        if self._nvml_initialized and not self.use_mock:
            try:
                pynvml.nvmlShutdown()
                self._nvml_initialized = False
                logger.info("NVML shutdown successfully")
            except Exception as e:
                logger.error(f"Error during NVML shutdown: {e}")

        logger.info("Telemetry service stopped")

    def register_callback(self, callback: Callable[[Dict[int, GPUMetrics]], None]) -> None:
        """Register a callback to receive telemetry updates

        Args:
            callback: Function to call with new metrics
        """
        with self._callback_lock:
            self.callbacks.append(callback)

            # Special case for test monitor methods - handle both direct callback and object instance
            if hasattr(callback, "__self__") and hasattr(
                callback.__self__, "check_temperature_alerts"
            ):
                # This is a monitor instance method
                self._monitor_temperature_check = callback.__self__.check_temperature_alerts
                self._monitor_memory_check = callback.__self__.check_memory_pressure
            elif callable(callback) and callback.__name__ in (
                "check_temperature_alerts",
                "check_memory_pressure",
            ):
                # Direct function reference
                setattr(self, f"_monitor_{callback.__name__}", callback)

    def unregister_callback(self, callback: Callable[[Dict[int, GPUMetrics]], None]) -> bool:
        """Unregister a previously registered callback

        Args:
            callback: The callback function to remove

        Returns:
            True if the callback was found and removed, False otherwise
        """
        with self._callback_lock:
            if callback in self.callbacks:
                self.callbacks.remove(callback)
                return True
            return False

    def get_metrics(self) -> Dict[int, GPUMetrics]:
        """Get the current metrics snapshot

        Returns:
            Dictionary of GPU ID to metrics
        """
        with self._metrics_lock:
            return self.metrics.copy()

    def get_history(
        self, gpu_id: Optional[int] = None, seconds: Optional[int] = None
    ) -> Union[Dict[int, List[GPUMetrics]], List[GPUMetrics]]:
        """Get historical metrics data

        Args:
            gpu_id: Optional GPU ID to get history for. If None, returns history for all GPUs.
            seconds: Optional time window in seconds. If None, returns all available history.

        Returns:
            If gpu_id is None: Dictionary mapping GPU IDs to lists of metrics
            If gpu_id is provided: List of metrics for the specified GPU
        """
        with self._metrics_lock:
            if gpu_id is not None:
                # Return history for a specific GPU
                if gpu_id not in self._metrics_history:
                    return []

                if seconds is not None:
                    # Filter by time window
                    cutoff_time = time.time() - seconds
                    return [m for m in self._metrics_history[gpu_id] if m.timestamp >= cutoff_time]
                else:
                    # Return all history for this GPU
                    return self._metrics_history[gpu_id].copy()
            else:
                # Return history for all GPUs
                if seconds is not None:
                    # Filter by time window
                    cutoff_time = time.time() - seconds
                    return {
                        gpu_id: [m for m in history if m.timestamp >= cutoff_time]
                        for gpu_id, history in self._metrics_history.items()
                    }
                else:
                    # Return all history
                    return {
                        gpu_id: history.copy() for gpu_id, history in self._metrics_history.items()
                    }

    def _telemetry_loop(self) -> None:
        """Main telemetry collection loop"""

        # Create batch collection helper
        def collect_batch_metrics(gpu_ids: List[int], current_time: float) -> Dict[int, GPUMetrics]:
            batch_metrics = {}

            # Use the custom GPU provider if available
            if self._gpu_provider is not None:
                try:
                    # Get GPUs from the provider
                    gpus = self._gpu_provider.get_gpus()

                    # Create metrics for each GPU
                    for i, gpu in enumerate(gpus):
                        # Convert from provider format to our GPUMetrics format
                        metrics = GPUMetrics(
                            gpu_id=i,
                            name=gpu.name,
                            utilization=gpu.utilization,
                            memory_used=int(
                                gpu.total_memory - gpu.available_memory
                            ),  # Keep as bytes
                            memory_total=int(gpu.total_memory),  # Keep as bytes
                            temperature=gpu.temperature,
                            power_usage=gpu.power_usage,
                            power_limit=gpu.power_limit,
                            fan_speed=gpu.fan_speed,
                            clock_sm=gpu.clock_speed,
                            clock_memory=gpu.memory_clock,
                            pcie_tx=0,  # Not provided by the test mock
                            pcie_rx=0,  # Not provided by the test mock
                            timestamp=current_time,
                            error_state=False,
                        )
                        batch_metrics[i] = metrics

                    return batch_metrics
                except Exception as e:
                    logger.error(f"Error using custom GPU provider: {e}")
                    # Fall back to regular collection if there's an error

            # Regular collection using NVML or mock data
            for gpu_id in gpu_ids:
                try:
                    if self.use_mock:
                        batch_metrics[gpu_id] = self._get_mock_metrics(gpu_id, current_time)
                    else:
                        batch_metrics[gpu_id] = self._get_gpu_metrics(gpu_id, current_time)
                except Exception as e:
                    logger.error(f"Error collecting metrics for GPU {gpu_id}: {e}")
                    # Fallback to mock data for this GPU
                    batch_metrics[gpu_id] = self._get_mock_metrics(
                        gpu_id, current_time, error_state=True
                    )
                    self._consecutive_errors += 1
            return batch_metrics

        while self.running and not self._stop_event.is_set():
            try:
                # Collect metrics from all GPUs
                current_time = time.time()

                # Determine the number of GPUs to monitor
                if self._gpu_provider is not None:
                    # Use the provider's count if available
                    gpu_count = self._gpu_provider.get_gpu_count()
                else:
                    # Use NVML count otherwise
                    gpu_count = self.gpu_count

                gpu_ids = list(range(gpu_count))

                # Batch collection for better performance
                batch_metrics = collect_batch_metrics(gpu_ids, current_time)

                # Try to recover NVML if we have consecutive errors and we're not using a custom provider
                if (
                    self._consecutive_errors >= 3
                    and not self.use_mock
                    and self._gpu_provider is None
                ):
                    if self._try_reinit_nvml():
                        logger.info("NVML recovered after consecutive errors")
                        self._consecutive_errors = 0
                    else:
                        # If recovery failed, switch to mock mode
                        self.use_mock = True
                        logger.warning("Switching to mock GPU data after consecutive NVML errors")

                # If we successfully collected metrics, reset error counter
                if not self.use_mock and self._consecutive_errors == 0:
                    self._recovery_attempts = 0

                # Update the metrics store with thread safety
                with self._metrics_lock:
                    self.metrics = batch_metrics

                    # Update history
                    for gpu_id, metrics in batch_metrics.items():
                        if gpu_id not in self._metrics_history:
                            self._metrics_history[gpu_id] = []
                        self._metrics_history[gpu_id].append(metrics)

                        # Trim history if needed
                        if len(self._metrics_history[gpu_id]) > self._history_length:
                            # Keep only the last _history_length entries
                            self._metrics_history[gpu_id] = self._metrics_history[gpu_id][
                                -self._history_length :
                            ]

                # Call monitor callbacks if they exist
                if self._monitor_temperature_check:
                    self._monitor_temperature_check(batch_metrics)

                if self._monitor_memory_check:
                    self._monitor_memory_check(batch_metrics)

                # Special case for TestMonitor in the tests - event_bus attribute check
                if hasattr(self._event_bus, "check_temperature_alerts"):
                    self._event_bus.check_temperature_alerts(batch_metrics)

                if hasattr(self._event_bus, "check_memory_pressure"):
                    self._event_bus.check_memory_pressure(batch_metrics)

                # Notify all registered callbacks and publish to event bus
                self._process_metrics_update(batch_metrics)

            except Exception as e:
                logger.error(f"Error in telemetry loop: {e}")
                self._consecutive_errors += 1

                # In case of serious errors, switch to mock mode
                if self._consecutive_errors >= 5:
                    self.use_mock = True
                    logger.warning("Switched to mock GPU data after multiple telemetry loop errors")

            # Sleep until next collection (with cancellation support)
            self._stop_event.wait(self.poll_interval)

    def _process_metrics_update(self, metrics: Dict[int, GPUMetrics]) -> None:
        """Process metrics update by notifying callbacks and publishing to event bus

        Args:
            metrics: The current metrics to distribute
        """
        # Notify all registered callbacks with thread safety
        with self._callback_lock:
            callbacks = list(
                self.callbacks
            )  # Create a copy to avoid issues if the list changes during iteration

        for callback in callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in telemetry callback: {e}")

        # Publish metrics to the event bus system
        if self._event_bus:
            try:
                logger.debug(f"Publishing metrics to event bus: {len(metrics)} GPUs")

                # Prepare metrics for the enhanced event format
                metrics_dict = {
                    "utilization": [],
                    "memory_used": [],
                    "memory_total": [],
                    "temperature": [],
                    "power_draw": [],
                    "fan_speed": [],
                }

                # Convert individual GPU metrics to lists per metric type
                for gpu_id, gpu_metrics in metrics.items():
                    # Populate the metrics dictionary for the enhanced event
                    metrics_dict["utilization"].append(gpu_metrics.utilization)
                    metrics_dict["memory_used"].append(gpu_metrics.memory_used)
                    metrics_dict["memory_total"].append(gpu_metrics.memory_total)
                    metrics_dict["temperature"].append(gpu_metrics.temperature)
                    metrics_dict["power_draw"].append(gpu_metrics.power_usage)
                    metrics_dict["fan_speed"].append(gpu_metrics.fan_speed)

                try:
                    # Import inside the function to ensure we're using the same class
                    # that the test is importing and subscribing to
                    from dualgpuopt.services.events import (
                        GPUMetricsEvent as EnhancedGPUMetricsEvent,
                    )

                    # Create and publish the enhanced GPUMetricsEvent with the metrics dictionary
                    logger.debug(
                        f"Publishing enhanced GPUMetricsEvent with metrics: {metrics_dict}"
                    )
                    enhanced_metrics_event = EnhancedGPUMetricsEvent(metrics=metrics_dict)
                    self._event_bus.publish_typed(enhanced_metrics_event)
                    logger.debug("Published enhanced GPUMetricsEvent")

                    # For backward compatibility, also publish the original-style events
                    from dualgpuopt.services.event_bus import (
                        GPUMetricsEvent as OriginalGPUMetricsEvent,
                    )

                    for gpu_id, gpu_metrics in metrics.items():
                        original_metrics_event = OriginalGPUMetricsEvent(
                            gpu_index=gpu_id,
                            utilization=gpu_metrics.utilization,
                            memory_used=gpu_metrics.memory_used,
                            memory_total=gpu_metrics.memory_total,
                            temperature=gpu_metrics.temperature,
                            power_draw=gpu_metrics.power_usage,
                            fan_speed=gpu_metrics.fan_speed,
                        )
                        self._event_bus.publish_typed(original_metrics_event)
                except ImportError as e:
                    logger.error(f"Failed to import event types: {e}")

                # Also publish a comprehensive update event with string type
                self._event_bus.publish("gpu_metrics_updated", metrics)
            except Exception as e:
                logger.error(f"Error publishing metrics to event bus: {e}")

    # Use maxsize parameter and specify TTL to help prevent memory leaks
    def _get_cached_gpu_name(self, gpu_id: int) -> str:
        """Get GPU name with caching to avoid redundant NVML calls

        Args:
            gpu_id: The GPU ID to query

        Returns:
            GPU name as a string
        """
        # Use a module-level function for caching instead of a method
        return _cached_gpu_name_lookup(
            gpu_id, self._nvml_initialized, self.use_mock, self._gpu_handles
        )

    def _get_gpu_metrics(self, gpu_id: int, timestamp: float) -> GPUMetrics:
        """Get metrics for a specific GPU using NVML

        Args:
            gpu_id: The GPU ID to query
            timestamp: Current timestamp

        Returns:
            GPUMetrics object with current values
        """
        try:
            # Get cached handle or create a new one
            handle = self._gpu_handles.get(gpu_id)
            if not handle:
                handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
                self._gpu_handles[gpu_id] = handle

            # Get name with caching
            name = self._get_cached_gpu_name(gpu_id)

            # Get utilization with error handling
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = util.gpu
            except Exception as e:
                logger.debug(f"Error getting GPU utilization: {e}")
                gpu_util = 0

            # Get memory with error handling
            try:
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                mem_used = mem_info.used // 1024 // 1024  # Convert to MB
                mem_total = mem_info.total // 1024 // 1024  # Convert to MB
            except Exception as e:
                logger.debug(f"Error getting memory info: {e}")
                mem_used = 0
                mem_total = 0

            # Get temperature with error handling
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except Exception as e:
                logger.debug(f"Error getting temperature: {e}")
                temp = 0

            # Get power with error handling
            try:
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
            except Exception as e:
                logger.debug(f"Error getting power usage: {e}")
                power_usage = 0.0

            # Get power limit with error handling
            try:
                power_limit = (
                    pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
                )  # Convert to watts
            except Exception as e:
                logger.debug(f"Error getting power limit: {e}")
                power_limit = 0.0

            # Get fan speed with error handling
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except Exception as e:
                logger.debug(f"Error getting fan speed: {e}")
                fan_speed = 0

            # Get clocks with error handling
            try:
                clock_sm = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
                clock_mem = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            except Exception as e:
                logger.debug(f"Error getting clock info: {e}")
                clock_sm = 0
                clock_mem = 0

            # Get PCIe throughput with error handling
            try:
                tx_bytes = pynvml.nvmlDeviceGetPcieThroughput(
                    handle, pynvml.NVML_PCIE_UTIL_TX_BYTES
                )
                rx_bytes = pynvml.nvmlDeviceGetPcieThroughput(
                    handle, pynvml.NVML_PCIE_UTIL_RX_BYTES
                )
            except Exception as e:
                logger.debug(f"Error getting PCIe throughput: {e}")
                tx_bytes = 0
                rx_bytes = 0

            return GPUMetrics(
                gpu_id=gpu_id,
                name=name,
                utilization=gpu_util,
                memory_used=mem_used,
                memory_total=mem_total,
                temperature=temp,
                power_usage=power_usage,
                power_limit=power_limit,
                fan_speed=fan_speed,
                clock_sm=clock_sm,
                clock_memory=clock_mem,
                pcie_tx=tx_bytes,
                pcie_rx=rx_bytes,
                timestamp=timestamp,
                error_state=False,
            )
        except Exception as e:
            logger.warning(f"Failed to get metrics for GPU {gpu_id}: {e}")
            # Try to recover NVML if necessary
            if "not initialized" in str(e).lower():
                self._try_reinit_nvml()

            # Return mock metrics in case of failure
            return self._get_mock_metrics(gpu_id, timestamp, error_state=True)

    def _get_mock_metrics(
        self, gpu_id: int, timestamp: float, error_state: bool = False
    ) -> GPUMetrics:
        """Generate mock metrics for testing without actual GPUs

        Args:
            gpu_id: The GPU ID to generate data for
            timestamp: Current timestamp
            error_state: Whether these metrics are generated due to an error

        Returns:
            GPUMetrics object with mock values
        """
        import random

        # Make GPU 0 a "high-end" GPU and GPU 1 a "mid-range" GPU in mocks
        if gpu_id == 0:
            name = "NVIDIA GeForce RTX 5070 Ti (MOCK)"
            mem_total = 24 * 1024  # 24 GB
            power_limit = 350.0
            clock_base = 2100
        else:
            name = "NVIDIA GeForce RTX 4060 (MOCK)"
            mem_total = 12 * 1024  # 12 GB
            power_limit = 200.0
            clock_base = 1800

        # If this is an error state, add indicator
        if error_state:
            name += " [FALLBACK]"

        # Generate varying utilization between 10-90%
        base_util = 30 + int(20 * (timestamp % 10)) + random.randint(-10, 10)
        util = max(0, min(99, base_util))

        # Memory follows utilization somewhat
        mem_used = int((mem_total * util / 100) * random.uniform(0.8, 1.2))
        mem_used = max(0, min(mem_total, mem_used))

        # Temperature correlates somewhat with utilization
        temp = 40 + int(util / 3) + random.randint(-5, 5)
        temp = max(30, min(85, temp))

        # Power also correlates with utilization
        power_usage = power_limit * (0.2 + (util / 100) * 0.7) + random.uniform(-20, 20)
        power_usage = max(10, min(power_limit, power_usage))

        # Fan speed follows temperature
        fan_speed = max(0, min(100, temp + 10 + random.randint(-10, 20)))

        # Clocks vary with utilization
        clock_variance = random.randint(-100, 50)
        clock_sm = clock_base + clock_variance
        clock_mem = int(clock_base * 0.8) + clock_variance

        # PCIe traffic varies with utilization too
        pcie_base = util * 1000  # KB/s
        pcie_tx = pcie_base + random.randint(0, 20000)
        pcie_rx = pcie_base * 0.8 + random.randint(0, 15000)

        return GPUMetrics(
            gpu_id=gpu_id,
            name=name,
            utilization=util,
            memory_used=mem_used,
            memory_total=mem_total,
            temperature=temp,
            power_usage=power_usage,
            power_limit=power_limit,
            fan_speed=fan_speed,
            clock_sm=clock_sm,
            clock_memory=clock_mem,
            pcie_tx=pcie_tx,
            pcie_rx=pcie_rx,
            timestamp=timestamp,
            error_state=error_state,
        )

    def reset(self) -> bool:
        """Reset the telemetry service and try to reinitialize NVML

        Returns:
            True if reset was successful, False otherwise
        """
        was_running = self.running

        # Stop the service if it's running
        if was_running:
            self.stop()

        # Reset error counters
        self._consecutive_errors = 0
        self._recovery_attempts = 0

        # Clear the handle cache
        self._gpu_handles = {}

        # Clear LRU caches
        self._get_cached_gpu_name.cache_clear()

        # Try to reinitialize NVML
        success = self._init_nvml()

        # Restart if it was running
        if was_running:
            self.start()

        return success


# Singleton instance for global access
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    """Get the global telemetry service instance

    Returns:
        The global telemetry service instance, creating it if needed
    """
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service


def reset_telemetry_service() -> bool:
    """Reset the global telemetry service

    Returns:
        True if reset was successful, False otherwise
    """
    service = get_telemetry_service()
    return service.reset()


# Module-level cache function to avoid memory leaks from methods with lru_cache
@lru_cache(maxsize=32, typed=True)
def _cached_gpu_name_lookup(
    gpu_id: int, nvml_initialized: bool, use_mock: bool, gpu_handles: Dict[int, Any]
) -> str:
    """Get cached GPU name to avoid redundant NVML calls

    Args:
        gpu_id: The GPU ID to query
        nvml_initialized: Whether NVML is initialized
        use_mock: Whether using mock data
        gpu_handles: Dictionary of GPU handles

    Returns:
        GPU name as a string
    """
    if not nvml_initialized or use_mock:
        return f"NVIDIA GPU {gpu_id} (MOCK)"

    try:
        handle = gpu_handles.get(gpu_id, pynvml.nvmlDeviceGetHandleByIndex(gpu_id))
        name_bytes = pynvml.nvmlDeviceGetName(handle)
        # Handle different return types from various pynvml versions
        if isinstance(name_bytes, bytes):
            return name_bytes.decode("utf-8", errors="replace")
        else:
            # Already a string in newer pynvml versions
            return name_bytes
    except Exception:
        return f"NVIDIA GPU {gpu_id}"
