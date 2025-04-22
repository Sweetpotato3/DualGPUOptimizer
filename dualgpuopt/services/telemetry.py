"""
Thread-safe GPU telemetry collector that emits Qt signals
instead of using polling.
"""
from __future__ import annotations
import time
import threading
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal

# Placeholder for the actual GPU query function
# Replace with: from dualgpuopt.gpu_info import query_gpus
def query_gpus():
    import random
    # Simulate two GPUs
    return {
        0: {
            "util": random.uniform(20, 80),
            "memory_percent": random.uniform(30, 90),
            "temp": random.uniform(40, 75),
            "power_percent": random.uniform(30, 90)
        },
        1: {
            "util": random.uniform(20, 80),
            "memory_percent": random.uniform(30, 90),
            "temp": random.uniform(40, 75),
            "power_percent": random.uniform(30, 90)
        }
    }

class GPUMetrics:
    """Container for GPU metrics"""
    def __init__(self, 
                 utilization: float = 0.0, 
                 memory_percent: float = 0.0,
                 temperature: float = 0.0,
                 power_percent: float = 0.0):
        self.utilization = utilization
        self.memory_percent = memory_percent
        self.temperature = temperature
        self.power_percent = power_percent

class TelemetryWorker(QObject):
    """Worker that collects GPU metrics and emits signals"""
    # Signal emitted when metrics are updated
    metrics_updated = Signal(dict)  # Dict[int, GPUMetrics]
    
    # Signal for specific metric types
    util_updated = Signal(float)    # Overall utilization average
    vram_updated = Signal(float)    # Overall memory usage percentage  
    temp_updated = Signal(float)    # Overall temperature average
    power_updated = Signal(float)   # Overall power percentage
    
    def __init__(self, poll_interval: float = 1.0, use_mock: bool = False):
        super().__init__()
        self.poll_interval = poll_interval
        self.use_mock = use_mock
        self.running = False
        self._thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the telemetry worker thread"""
        if self._thread is not None:
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the telemetry worker thread"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
            
    def _run(self):
        """Thread worker function"""
        while self.running:
            try:
                # Get raw GPU data (real or mock)
                gpu_data = self._get_gpu_data()
                
                if gpu_data:
                    # Convert to GPUMetrics objects
                    metrics = {}
                    for gpu_id, data in gpu_data.items():
                        metrics[gpu_id] = GPUMetrics(
                            utilization=data.get("util", 0.0),
                            memory_percent=data.get("memory_percent", 0.0),
                            temperature=data.get("temp", 0.0),
                            power_percent=data.get("power_percent", 0.0)
                        )
                    
                    # Emit full metrics
                    self.metrics_updated.emit(metrics)
                    
                    # Calculate and emit overall metrics
                    if metrics:
                        util_avg = sum(m.utilization for m in metrics.values()) / len(metrics)
                        vram_avg = sum(m.memory_percent for m in metrics.values()) / len(metrics)
                        temp_avg = sum(m.temperature for m in metrics.values()) / len(metrics)
                        power_avg = sum(m.power_percent for m in metrics.values()) / len(metrics)
                        
                        self.util_updated.emit(util_avg)
                        self.vram_updated.emit(vram_avg)
                        self.temp_updated.emit(temp_avg)
                        self.power_updated.emit(power_avg)
            
            except Exception as e:
                print(f"Telemetry error: {e}")
                
            time.sleep(self.poll_interval)
                
    def _get_gpu_data(self) -> Dict[int, Dict[str, Any]]:
        """Get GPU data (real or mock)"""
        if self.use_mock:
            return self._get_mock_data()
        # Use the actual query function
        # Make sure dualgpuopt.gpu_info exists and is importable
        try:
            from dualgpuopt.gpu_info import query_gpus as actual_query
            return actual_query()
        except ImportError:
            print("Warning: dualgpuopt.gpu_info not found, using mock data.")
            return self._get_mock_data()
            
    def _get_mock_data(self) -> Dict[int, Dict[str, Any]]:
        """Generate mock GPU data for testing"""
        import random
        
        # Two simulated GPUs
        mock_data = {
            0: {
                "util": random.uniform(20, 80),
                "memory_percent": random.uniform(30, 90),
                "temp": random.uniform(40, 75),
                "power_percent": random.uniform(30, 90)
            },
            1: {
                "util": random.uniform(20, 80),
                "memory_percent": random.uniform(30, 90),
                "temp": random.uniform(40, 75),
                "power_percent": random.uniform(30, 90)
            }
        }
        
        return mock_data

# Singleton instance
telemetry_worker = TelemetryWorker() 