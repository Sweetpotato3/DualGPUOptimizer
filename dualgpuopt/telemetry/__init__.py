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

    # Check if the module exists and import it only if needed
    metrics_spec = importlib.util.find_spec("dualgpuopt.telemetry.metrics")
    if metrics_spec is not None:
        # Import is available but we'll only use it through __all__
        __all__.append("GPUMetrics")
except ImportError:
    # If importlib.util is not available or other import errors occur
    pass

__all__ = ["TelemetrySample", "get_telemetry_service"]
