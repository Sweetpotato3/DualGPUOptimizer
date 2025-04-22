"""
dualgpuopt.telemetry module
Provides telemetry and history tracking for GPU metrics.
"""

# Import GPUMetrics from the parent module
from dualgpuopt.telemetry import get_telemetry_service
from dualgpuopt.telemetry.sample import TelemetrySample

# Import GPUMetrics directly - this is required by several modules
try:
    from dualgpuopt.telemetry import GPUMetrics  # Direct import attempt
except ImportError:
    # If GPUMetrics doesn't exist in telemetry module directly, this is a no-op
    pass

__all__ = ["TelemetrySample", "get_telemetry_service"]
