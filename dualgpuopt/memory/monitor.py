"""
Core memory monitoring functionality for GPU devices.

This module provides the main MemoryMonitor class responsible for
monitoring GPU memory usage and triggering alerts.
"""

import atexit
import logging
import threading
import time
from typing import Dict, List, Optional, Union

from dualgpuopt.error_handler import ErrorCategory, ErrorHandler, ErrorSeverity, handle_exceptions
from dualgpuopt.memory.alerts import MemoryAlert, MemoryAlertCallback, MemoryAlertLevel
from dualgpuopt.memory.metrics import GPUMemoryStats, MemoryUnit
from dualgpuopt.memory.predictor import MemoryProfile
from dualgpuopt.memory.recovery import RecoveryManager, MemoryRecoveryStrategy

# Initialize module-level logger
logger = logging.getLogger("DualGPUOpt.MemoryMonitor")

# Forward declarations for type hints
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    logger.warning("NVML not available, using mock GPU memory monitoring")
    NVML_AVAILABLE = False


class MemoryMonitor:
    """
    GPU memory monitoring and management system.

    Provides real-time memory monitoring, alerts, projections, and
    OOM prevention strategies for dual-GPU setups.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton implementation"""
        if cls._instance is None:
            cls._instance = super(MemoryMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self,
                update_interval: float = 1.0,
                warning_threshold: float = 80.0,
                critical_threshold: float = 90.0,
                emergency_threshold: float = 95.0):
        """
        Initialize memory monitor

        Args:
            update_interval: Interval between memory checks in seconds
            warning_threshold: Memory usage percentage for WARNING level
            critical_threshold: Memory usage percentage for CRITICAL level
            emergency_threshold: Memory usage percentage for EMERGENCY level
        """
        if self._initialized:
            return

        self._initialized = True
        self._update_interval = update_interval
        self._thresholds = {
            MemoryAlertLevel.WARNING: warning_threshold,
            MemoryAlertLevel.CRITICAL: critical_threshold,
            MemoryAlertLevel.EMERGENCY: emergency_threshold
        }

        # Initialize NVML if available
        self._nvml_initialized = False
        self._mock_mode = not NVML_AVAILABLE
        self._gpu_count = 0
        self._init_nvml()

        # State tracking
        self._memory_stats: Dict[int, GPUMemoryStats] = {}
        self._last_update_time = 0
        self._profiles: Dict[str, MemoryProfile] = {}
        self._active_profile = None

        # Callback registrations
        self._alert_callbacks: Dict[MemoryAlertLevel, List[MemoryAlertCallback]] = {
            level: [] for level in MemoryAlertLevel
        }

        # Recovery manager
        self._recovery_manager = RecoveryManager()

        # Initialize monitoring thread
        self._monitoring_active = False
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()

        # Register cleanup
        atexit.register(self.shutdown)

    @handle_exceptions(component="MemoryMonitor", severity=ErrorSeverity.ERROR)
    def _init_nvml(self):
        """Initialize NVML if available"""
        if self._mock_mode:
            logger.info("Using mock GPU memory monitoring (NVML not available)")
            self._gpu_count = 2  # Default to two GPUs in mock mode
            return

        try:
            pynvml.nvmlInit()
            self._nvml_initialized = True
            self._gpu_count = pynvml.nvmlDeviceGetCount()
            logger.info(f"NVML initialized successfully, found {self._gpu_count} GPU(s)")
        except Exception as e:
            logger.warning(f"Failed to initialize NVML: {e}")
            self._mock_mode = True
            self._gpu_count = 2  # Default to two GPUs in mock mode

    def register_profile(self, profile: MemoryProfile):
        """Register a memory usage profile"""
        self._profiles[profile.name] = profile
        logger.debug(f"Registered memory profile: {profile.name}")

    def set_active_profile(self, profile_name: str) -> bool:
        """Set active memory profile by name"""
        if profile_name in self._profiles:
            self._active_profile = self._profiles[profile_name]
            logger.info(f"Set active memory profile to {profile_name}")
            return True
        else:
            logger.warning(f"Memory profile not found: {profile_name}")
            return False

    def register_alert_callback(self, level: MemoryAlertLevel, callback: MemoryAlertCallback):
        """Register callback for memory alerts"""
        self._alert_callbacks[level].append(callback)
        logger.debug(f"Registered alert callback for level {level.name}")

    def unregister_alert_callback(self, level: MemoryAlertLevel, callback: MemoryAlertCallback) -> bool:
        """Unregister callback for memory alerts"""
        if callback in self._alert_callbacks[level]:
            self._alert_callbacks[level].remove(callback)
            logger.debug(f"Unregistered alert callback for level {level.name}")
            return True
        return False

    def register_recovery_strategy(self, strategy: MemoryRecoveryStrategy, func):
        """Register recovery function for OOM prevention"""
        self._recovery_manager.register_strategy(strategy, func)

    def start_monitoring(self):
        """Start memory monitoring thread"""
        if self._monitoring_active:
            return

        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="MemoryMonitorThread"
        )
        self._monitoring_active = True
        self._monitoring_thread.start()
        logger.info("Memory monitoring started")

    def stop_monitoring(self):
        """Stop memory monitoring thread"""
        if not self._monitoring_active:
            return

        self._stop_monitoring.set()
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=2.0)
        self._monitoring_active = False
        logger.info("Memory monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop that runs in background thread"""
        while not self._stop_monitoring.is_set():
            try:
                # Update memory stats
                self._update_memory_stats()

                # Check for alerts
                self._check_alerts()

                # Sleep until next update
                time.sleep(self._update_interval)
            except Exception as e:
                error_handler = ErrorHandler()
                error_handler.handle_error(
                    exception=e,
                    component="MemoryMonitor",
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.MEMORY_ERROR,
                    message=f"Error in memory monitoring loop: {e}"
                )
                time.sleep(self._update_interval)  # Sleep to avoid tight loop on errors

    @handle_exceptions(component="MemoryMonitor", severity=ErrorSeverity.ERROR)
    def _update_memory_stats(self):
        """Update memory statistics for all GPUs"""
        self._last_update_time = time.time()

        for gpu_id in range(self._gpu_count):
            if self._mock_mode:
                self._memory_stats[gpu_id] = self._get_mock_memory_stats(gpu_id)
            else:
                self._memory_stats[gpu_id] = self._get_real_memory_stats(gpu_id)

            # Update active profile if available
            if self._active_profile:
                self._active_profile.update_history(self._memory_stats[gpu_id].used_memory)

    def _get_real_memory_stats(self, gpu_id: int) -> GPUMemoryStats:
        """Get real memory statistics from NVML"""
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)

            # Get processes using this GPU
            processes = {}
            try:
                for proc in pynvml.nvmlDeviceGetComputeRunningProcesses(handle):
                    processes[proc.pid] = proc.usedGpuMemory
            except:
                # Some driver versions don't support this function
                pass

            return GPUMemoryStats(
                gpu_id=gpu_id,
                total_memory=info.total,
                used_memory=info.used,
                free_memory=info.free,
                process_memory=processes,
                timestamp=time.time()
            )
        except Exception as e:
            logger.error(f"Error getting memory stats for GPU {gpu_id}: {e}")
            return self._get_mock_memory_stats(gpu_id)

    def _get_mock_memory_stats(self, gpu_id: int) -> GPUMemoryStats:
        """Generate mock memory statistics for testing"""
        # If we have previous stats, use them as base
        if gpu_id in self._memory_stats:
            prev_stats = self._memory_stats[gpu_id]
            # Simulate small memory fluctuations
            total = prev_stats.total_memory
            used = max(0, min(total, prev_stats.used_memory + int(total * 0.01 * (0.5 - (0.5 * threading.current_thread().name.__hash__() % 100) / 100))))
            free = total - used
        else:
            # First-time initialization with reasonable values
            total = 8 * 1024 * 1024 * 1024  # 8 GB
            used = int(total * (0.3 + 0.1 * (gpu_id + 1) / 10))  # 30-40% usage
            free = total - used

        return GPUMemoryStats(
            gpu_id=gpu_id,
            total_memory=total,
            used_memory=used,
            free_memory=free,
            process_memory={},  # No process info in mock mode
            timestamp=time.time()
        )

    def _check_alerts(self):
        """Check for memory alerts based on current usage"""
        for gpu_id, stats in self._memory_stats.items():
            usage_percent = stats.usage_percent()

            # Check thresholds from highest to lowest
            if usage_percent >= self._thresholds[MemoryAlertLevel.EMERGENCY]:
                self._trigger_alert(MemoryAlertLevel.EMERGENCY, gpu_id, stats)

            elif usage_percent >= self._thresholds[MemoryAlertLevel.CRITICAL]:
                self._trigger_alert(MemoryAlertLevel.CRITICAL, gpu_id, stats)

            elif usage_percent >= self._thresholds[MemoryAlertLevel.WARNING]:
                self._trigger_alert(MemoryAlertLevel.WARNING, gpu_id, stats)

    def _trigger_alert(self, level: MemoryAlertLevel, gpu_id: int, stats: GPUMemoryStats):
        """Trigger memory alert and call registered callbacks"""
        usage_percent = stats.usage_percent()
        threshold = self._thresholds[level]

        # Create alert message
        if level == MemoryAlertLevel.WARNING:
            message = f"Memory usage on GPU {gpu_id} is high"
            recommendations = ["Consider reducing batch size", "Monitor for further increases"]
        elif level == MemoryAlertLevel.CRITICAL:
            message = f"Memory usage on GPU {gpu_id} is approaching critical level"
            recommendations = ["Reduce batch size", "Clear caches if possible", "Consider terminating non-essential processes"]
        else:  # EMERGENCY
            message = f"Memory usage on GPU {gpu_id} is at emergency level, OOM risk"
            recommendations = ["Immediately reduce workload", "Terminate non-essential processes", "Clear all caches"]
            # Try automatic recovery
            self._attempt_recovery(gpu_id, stats)

        # Create alert object
        alert = MemoryAlert(
            level=level,
            gpu_id=gpu_id,
            message=message,
            current_usage=usage_percent,
            threshold=threshold,
            recommendations=recommendations,
            context={
                "total_memory": stats.total_memory,
                "used_memory": stats.used_memory,
                "free_memory": stats.free_memory
            }
        )

        # Log alert
        log_msg = f"{str(alert)}"
        if level == MemoryAlertLevel.WARNING:
            logger.warning(log_msg)
        elif level == MemoryAlertLevel.CRITICAL:
            logger.error(log_msg)
        else:  # EMERGENCY
            logger.critical(log_msg)

        # Call registered callbacks
        for callback in self._alert_callbacks[level]:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in memory alert callback: {e}")

    def _attempt_recovery(self, gpu_id: int, stats: GPUMemoryStats):
        """Attempt to recover from impending OOM"""
        self._recovery_manager.attempt_recovery(gpu_id, stats.as_dict())

    def get_memory_stats(self, gpu_id: Optional[int] = None,
                        unit: MemoryUnit = MemoryUnit.GB) -> Union[Dict[str, float], Dict[int, Dict[str, float]]]:
        """
        Get current memory statistics

        Args:
            gpu_id: Specific GPU ID or None for all GPUs
            unit: Memory unit for returned values

        Returns:
            Dictionary of memory stats or dictionary of GPU ID to memory stats
        """
        # Update stats if stale (> 2x update interval)
        if time.time() - self._last_update_time > self._update_interval * 2:
            self._update_memory_stats()

        if gpu_id is not None:
            if gpu_id in self._memory_stats:
                return self._memory_stats[gpu_id].get_memory(unit)
            return {}

        return {gpu_id: stats.get_memory(unit) for gpu_id, stats in self._memory_stats.items()}

    def get_all_stats(self) -> Dict[int, Dict[str, any]]:
        """Get complete memory statistics for all GPUs"""
        # Update stats if stale
        if time.time() - self._last_update_time > self._update_interval * 2:
            self._update_memory_stats()

        return {gpu_id: stats.as_dict() for gpu_id, stats in self._memory_stats.items()}

    def estimate_max_batch(self, gpu_id: int, token_count: int, profile_name: Optional[str] = None) -> int:
        """
        Estimate maximum batch size for a GPU

        Args:
            gpu_id: GPU device ID
            token_count: Number of tokens per batch item
            profile_name: Specific profile to use (or active profile if None)

        Returns:
            Maximum batch size estimation
        """
        # Use specified profile or active profile
        profile = None
        if profile_name and profile_name in self._profiles:
            profile = self._profiles[profile_name]
        elif self._active_profile:
            profile = self._active_profile

        if not profile:
            logger.warning("No memory profile available for batch size estimation")
            return 1  # Default to minimum batch size

        # Get current memory stats
        if gpu_id not in self._memory_stats:
            logger.warning(f"No memory stats available for GPU {gpu_id}")
            return 1

        # Calculate available memory with safety buffer
        stats = self._memory_stats[gpu_id]
        safety_factor = 0.9  # 90% of free memory to avoid OOM
        available_memory = int(stats.free_memory * safety_factor)

        # Calculate maximum batch size
        return profile.max_batch_size(available_memory, token_count)

    def project_memory_usage(self, gpu_id: int, seconds_ahead: float = 60.0) -> Optional[float]:
        """
        Project memory usage ahead in time

        Args:
            gpu_id: GPU device ID
            seconds_ahead: Time in seconds to project ahead

        Returns:
            Projected memory usage in percent or None if projection failed
        """
        # Need an active profile with history
        if not self._active_profile:
            return None

        # Project memory usage
        projected_bytes = self._active_profile.project_growth(seconds_ahead)
        if projected_bytes is None:
            return None

        # Convert to percentage
        if gpu_id not in self._memory_stats:
            return None

        total_memory = self._memory_stats[gpu_id].total_memory
        if total_memory <= 0:
            return None

        return (projected_bytes / total_memory) * 100

    def estimate_safe_context_size(self, gpu_id: int, batch_size: int,
                                 buffer_percent: float = 10.0) -> int:
        """
        Estimate safe context size based on available memory

        Args:
            gpu_id: GPU device ID
            batch_size: Batch size
            buffer_percent: Safety buffer percentage

        Returns:
            Safe context size in tokens
        """
        # Need a profile for estimation
        if not self._active_profile:
            logger.warning("No active memory profile for context size estimation")
            return 2048  # Default context size

        # Get current memory stats
        if gpu_id not in self._memory_stats:
            logger.warning(f"No memory stats available for GPU {gpu_id}")
            return 2048

        # Calculate available memory with safety buffer
        stats = self._memory_stats[gpu_id]
        buffer_factor = 1.0 - (buffer_percent / 100.0)
        available_memory = int(stats.free_memory * buffer_factor)

        # Estimate max sequence length
        return self._active_profile.max_sequence_length(available_memory, batch_size)

    def shutdown(self):
        """Clean up resources and stop monitoring"""
        self.stop_monitoring()
        if self._nvml_initialized and not self._mock_mode:
            try:
                pynvml.nvmlShutdown()
                logger.info("NVML shutdown successful")
            except:
                pass


# Singleton accessor
def get_memory_monitor() -> MemoryMonitor:
    """Get singleton memory monitor instance"""
    return MemoryMonitor()