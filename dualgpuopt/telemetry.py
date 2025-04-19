"""
Telemetry module for GPU metrics collection and processing
Provides real-time monitoring of GPU resources, temperature, power, and utilization
"""
from typing import Dict, List, Optional, Callable, Any, Tuple
import threading
import time
import logging
from dataclasses import dataclass
from enum import Enum

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Telemetry")

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    logger.warning("PYNVML not available, using mock GPU data")
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
    
    def __init__(self, poll_interval: float = 1.0, use_mock: bool = False):
        """Initialize the telemetry service
        
        Args:
            poll_interval: How frequently to poll GPU data (seconds)
            use_mock: Force using mock data even if NVML is available
        """
        self.poll_interval = poll_interval
        self.use_mock = use_mock or not NVML_AVAILABLE
        self.running = False
        self.metrics: Dict[int, GPUMetrics] = {}
        self.callbacks: List[Callable[[Dict[int, GPUMetrics]], None]] = []
        self._thread: Optional[threading.Thread] = None
        
        if not self.use_mock:
            try:
                pynvml.nvmlInit()
                self.gpu_count = pynvml.nvmlDeviceGetCount()
                logger.info(f"NVML initialized with {self.gpu_count} GPUs")
            except Exception as e:
                logger.error(f"Failed to initialize NVML: {e}")
                self.use_mock = True
        
        if self.use_mock:
            self.gpu_count = 2  # Mock 2 GPUs
            logger.info("Using mock GPU data with 2 virtual GPUs")
    
    def start(self) -> None:
        """Start the telemetry collection thread"""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._telemetry_loop, daemon=True)
        self._thread.start()
        logger.info("Telemetry service started")
    
    def stop(self) -> None:
        """Stop the telemetry collection thread"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Telemetry service stopped")
    
    def register_callback(self, callback: Callable[[Dict[int, GPUMetrics]], None]) -> None:
        """Register a callback to receive telemetry updates
        
        Args:
            callback: Function to call with new metrics
        """
        self.callbacks.append(callback)
    
    def get_metrics(self) -> Dict[int, GPUMetrics]:
        """Get the current metrics snapshot
        
        Returns:
            Dictionary of GPU ID to metrics
        """
        return self.metrics.copy()
    
    def _telemetry_loop(self) -> None:
        """Main telemetry collection loop"""
        while self.running:
            try:
                # Collect metrics from all GPUs
                metrics = {}
                current_time = time.time()
                
                for gpu_id in range(self.gpu_count):
                    if self.use_mock:
                        metrics[gpu_id] = self._get_mock_metrics(gpu_id, current_time)
                    else:
                        metrics[gpu_id] = self._get_gpu_metrics(gpu_id, current_time)
                
                # Update the metrics store
                self.metrics = metrics
                
                # Notify all registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(self.metrics)
                    except Exception as e:
                        logger.error(f"Error in telemetry callback: {e}")
                
            except Exception as e:
                logger.error(f"Error collecting telemetry: {e}")
            
            # Sleep until next collection
            time.sleep(self.poll_interval)
    
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
            name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
            
            # Get utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = util.gpu
            
            # Get memory
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            mem_used = mem_info.used // 1024 // 1024  # Convert to MB
            mem_total = mem_info.total // 1024 // 1024  # Convert to MB
            
            # Get temperature, power, fan
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
            power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0  # Convert to watts
            
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except pynvml.NVMLError:
                fan_speed = 0  # Some GPUs don't have fans or don't report fan speed
            
            # Get clocks
            try:
                clock_sm = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
                clock_mem = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            except pynvml.NVMLError:
                clock_sm = 0
                clock_mem = 0
            
            # Get PCIe throughput
            try:
                tx_bytes = pynvml.nvmlDeviceGetPcieThroughput(handle, pynvml.NVML_PCIE_UTIL_TX_BYTES)
                rx_bytes = pynvml.nvmlDeviceGetPcieThroughput(handle, pynvml.NVML_PCIE_UTIL_RX_BYTES)
            except pynvml.NVMLError:
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
                timestamp=timestamp
            )
        except Exception as e:
            logger.error(f"Error getting metrics for GPU {gpu_id}: {e}")
            # Return mock metrics in case of failure
            return self._get_mock_metrics(gpu_id, timestamp)
    
    def _get_mock_metrics(self, gpu_id: int, timestamp: float) -> GPUMetrics:
        """Generate mock metrics for testing without actual GPUs
        
        Args:
            gpu_id: The GPU ID to generate data for
            timestamp: Current timestamp
            
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
            timestamp=timestamp
        )


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