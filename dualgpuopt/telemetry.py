"""
Telemetry module for GPU metrics collection and processing
Provides real-time monitoring of GPU resources, temperature, power, and utilization
"""
from typing import Dict, List, Optional, Callable, Any, Tuple
import threading
import time
import logging
import os
from dataclasses import dataclass
from enum import Enum

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Telemetry")

# Environment variable configuration options
ENV_POLL_INTERVAL = float(os.environ.get("DUALGPUOPT_POLL_INTERVAL", "1.0"))
ENV_MOCK_TELEMETRY = os.environ.get("DUALGPUOPT_MOCK_TELEMETRY", "").lower() in ("1", "true", "yes", "on")
ENV_MAX_RECOVERY_ATTEMPTS = int(os.environ.get("DUALGPUOPT_MAX_RECOVERY", "3"))

# Import error handling if available
try:
    from dualgpuopt.error_handler import handle_exceptions, ErrorCategory, ErrorSeverity
    error_handler_available = True
except ImportError:
    error_handler_available = False
    logger.warning("Error handler not available for telemetry, using basic error handling")

# Import event bus if available
try:
    from dualgpuopt.services.event_bus import event_bus, GPUMetricsEvent
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


class TelemetryService:
    """Service for collecting and distributing GPU telemetry"""

    def __init__(self, poll_interval: float = ENV_POLL_INTERVAL, use_mock: bool = ENV_MOCK_TELEMETRY):
        """Initialize the telemetry service

        Args:
            poll_interval: How frequently to poll GPU data (seconds)
            use_mock: Force using mock data even if NVML is available
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

        # Initialize NVML if available
        self._init_nvml()

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
        if current_time - self._last_error_time < (2 ** self._recovery_attempts):
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
            self.use_mock = False
            self._consecutive_errors = 0
            logger.info(f"NVML successfully reinitialized with {self.gpu_count} GPUs")
            return True
        except Exception as e:
            logger.error(f"Failed to reinitialize NVML: {e}")
            self.use_mock = True
            return False

    def start(self) -> None:
        """Start the telemetry collection thread"""
        if self.running:
            return

        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._telemetry_loop, daemon=True)
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
        self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[Dict[int, GPUMetrics]], None]) -> bool:
        """Unregister a previously registered callback

        Args:
            callback: The callback function to remove

        Returns:
            True if the callback was found and removed, False otherwise
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True
        return False

    def get_metrics(self) -> Dict[int, GPUMetrics]:
        """Get the current metrics snapshot

        Returns:
            Dictionary of GPU ID to metrics
        """
        return self.metrics.copy()

    def _telemetry_loop(self) -> None:
        """Main telemetry collection loop"""
        while self.running and not self._stop_event.is_set():
            try:
                # Collect metrics from all GPUs
                metrics = {}
                current_time = time.time()

                # Determine the number of GPUs to monitor
                gpu_count = self.gpu_count

                for gpu_id in range(gpu_count):
                    try:
                        if self.use_mock:
                            metrics[gpu_id] = self._get_mock_metrics(gpu_id, current_time)
                        else:
                            metrics[gpu_id] = self._get_gpu_metrics(gpu_id, current_time)
                    except Exception as e:
                        logger.error(f"Error collecting metrics for GPU {gpu_id}: {e}")
                        # Fallback to mock data for this GPU
                        metrics[gpu_id] = self._get_mock_metrics(gpu_id, current_time, error_state=True)
                        self._consecutive_errors += 1

                        # Try to recover NVML if we have consecutive errors
                        if self._consecutive_errors >= 3 and not self.use_mock:
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

                # Update the metrics store
                self.metrics = metrics

                # Notify all registered callbacks
                self._notify_callbacks(metrics)

                # Publish metrics via event bus if available
                if event_bus_available:
                    self._publish_to_event_bus(metrics)

            except Exception as e:
                logger.error(f"Error in telemetry loop: {e}")
                self._consecutive_errors += 1

                # In case of serious errors, switch to mock mode
                if self._consecutive_errors >= 5:
                    self.use_mock = True
                    logger.warning("Switched to mock GPU data after multiple telemetry loop errors")

            # Sleep until next collection (with cancellation support)
            self._stop_event.wait(self.poll_interval)

    def _notify_callbacks(self, metrics: Dict[int, GPUMetrics]) -> None:
        """Notify all registered callbacks with new metrics

        Args:
            metrics: The current metrics to send to callbacks
        """
        # Make a copy of callbacks to avoid issues if the list changes during iteration
        callbacks = self.callbacks.copy()

        for callback in callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in telemetry callback: {e}")
                # Don't remove the callback automatically, let the client handle it
    
    def _publish_to_event_bus(self, metrics: Dict[int, GPUMetrics]) -> None:
        """Publish metrics to the event bus system

        Args:
            metrics: The current metrics to publish
        """
        if not event_bus_available:
            return
        
        try:
            for gpu_id, gpu_metrics in metrics.items():
                # Create and publish a GPUMetricsEvent for each GPU
                metrics_event = GPUMetricsEvent(
                    gpu_index=gpu_id,
                    utilization=gpu_metrics.utilization,
                    memory_used=gpu_metrics.memory_used,
                    memory_total=gpu_metrics.memory_total,
                    temperature=gpu_metrics.temperature,
                    power_draw=gpu_metrics.power_usage,
                    fan_speed=gpu_metrics.fan_speed
                )
                event_bus.publish_typed(metrics_event)
                
            # Also publish a comprehensive update event with string type
            event_bus.publish("gpu_metrics_updated", metrics)
        except Exception as e:
            logger.error(f"Error publishing metrics to event bus: {e}")

    def _get_gpu_metrics(self, gpu_id: int, timestamp: float) -> GPUMetrics:
        """Get metrics for a specific GPU using NVML

        Args:
            gpu_id: The GPU ID to query
            timestamp: Current timestamp

        Returns:
            GPUMetrics object with current values
        """
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
            name_bytes = pynvml.nvmlDeviceGetName(handle)
            # Handle different return types from various pynvml versions
            if isinstance(name_bytes, bytes):
                name = name_bytes.decode('utf-8', errors='replace')
            else:
                # Already a string in newer pynvml versions
                name = name_bytes

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
                power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0  # Convert to watts
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
                tx_bytes = pynvml.nvmlDeviceGetPcieThroughput(handle, pynvml.NVML_PCIE_UTIL_TX_BYTES)
                rx_bytes = pynvml.nvmlDeviceGetPcieThroughput(handle, pynvml.NVML_PCIE_UTIL_RX_BYTES)
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
                error_state=False
            )
        except Exception as e:
            logger.warning(f"Failed to get metrics for GPU {gpu_id}: {e}")
            # Try to recover NVML if necessary
            if "not initialized" in str(e).lower():
                self._try_reinit_nvml()

            # Return mock metrics in case of failure
            return self._get_mock_metrics(gpu_id, timestamp, error_state=True)

    def _get_mock_metrics(self, gpu_id: int, timestamp: float, error_state: bool = False) -> GPUMetrics:
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
            error_state=error_state
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