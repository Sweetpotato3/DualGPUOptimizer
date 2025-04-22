"""
dualgpuopt.telemetry module
Provides telemetry and history tracking for GPU metrics.
"""

# Import GPUMetrics from the parent module
from dualgpuopt.telemetry import get_telemetry_service
from dualgpuopt.telemetry.sample import TelemetrySample

# Import GPUMetrics directly - this is required by several modules
__all__ = ["TelemetrySample", "get_telemetry_service"]
try:
    # Check if the module exists before importing
    import importlib.util
    if importlib.util.find_spec("dualgpuopt.telemetry.metrics"):
        from dualgpuopt.telemetry.metrics import GPUMetrics
        __all__.append("GPUMetrics")
except ImportError:
    # If GPUMetrics doesn't exist in metrics module, this is a no-op
    pass

__all__ = ["TelemetrySample", "get_telemetry_service"]
