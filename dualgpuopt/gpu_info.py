"""
GPU info module with platform-independent GPU detection
(Compatibility layer for refactored gpu module)
"""
from __future__ import annotations

import ctypes.util
import logging
import os
from typing import Any

# Set up the logger
logger = logging.getLogger("DualGPUOpt.GPUInfo")

# Check environment variables for configuration
ENV_MOCK_GPU = os.environ.get("DUALGPUOPT_MOCK_GPU", "").lower() in ("1", "true", "yes", "on")
ENV_GPU_COUNT = int(os.environ.get("DUALGPUOPT_GPU_COUNT", "0"))

# Import from refactored GPU module
try:
    # Import the core functionality from the refactored modules
    from dualgpuopt.gpu.common import IS_MAC, IS_NVIDIA, MOCK_MODE, NVML_INITIALIZED
    from dualgpuopt.gpu.info import get_gpu_count, get_gpu_names, query
    from dualgpuopt.gpu.mock import generate_mock_gpus, get_mock_mode, set_mock_mode
    from dualgpuopt.gpu.monitor import (
        get_memory_info,
        get_power_usage,
        get_temperature,
        get_utilization,
    )

    # Override with environment variables if set
    if ENV_MOCK_GPU:
        set_mock_mode(True)
        logger.info("Mock GPU mode enabled via environment variable")

    # Use environment-specified GPU count if provided
    if ENV_GPU_COUNT > 0:
        logger.info(f"Using environment-specified GPU count: {ENV_GPU_COUNT}")

    logger.info("Successfully imported refactored GPU module")
except ImportError as e:
    logger.error(f"Failed to import refactored GPU module: {e}")
    # Keep basic functionality working if refactored modules fail to import
    IS_NVIDIA = True
    IS_MAC = False
    MOCK_MODE = ENV_MOCK_GPU or True
    NVML_INITIALIZED = False

    def query() -> list[dict[str, Any]]:
        """Fallback query function that returns mock data"""
        return _generate_mock_gpus(ENV_GPU_COUNT if ENV_GPU_COUNT > 0 else 2)

    def get_gpu_count() -> int:
        """Fallback GPU count function"""
        return ENV_GPU_COUNT if ENV_GPU_COUNT > 0 else len(query())

    def get_gpu_names() -> list[str]:
        """Fallback GPU names function"""
        return [gpu["name"] for gpu in query()]

    def set_mock_mode(enabled: bool) -> None:
        """Fallback to enable/disable mock mode"""
        global MOCK_MODE
        MOCK_MODE = enabled
        logger.info(f"Mock GPU mode {'enabled' if enabled else 'disabled'}")

    def get_mock_mode() -> bool:
        """Get current mock mode status"""
        return MOCK_MODE

    def get_memory_info(gpu_id: int = 0) -> dict[str, int]:
        """Fallback memory info function"""
        try:
            gpus = query()
            if gpu_id < len(gpus):
                gpu = gpus[gpu_id]
                return {
                    "total": gpu["mem_total"],
                    "used": gpu["mem_used"],
                    "free": gpu["mem_total"] - gpu["mem_used"],
                }
        except Exception as e:
            logger.error(f"Error getting memory info (fallback): {e}")

        # Default safe values
        return {"total": 8192, "used": 0, "free": 8192}

    def get_utilization(gpu_id: int = 0) -> int:
        """Fallback utilization function"""
        try:
            gpus = query()
            if gpu_id < len(gpus):
                return gpus[gpu_id]["util"]
        except Exception as e:
            logger.error(f"Error getting utilization (fallback): {e}")
        return 0

    def get_temperature(gpu_id: int = 0) -> float:
        """Fallback temperature function"""
        try:
            gpus = query()
            if gpu_id < len(gpus):
                return gpus[gpu_id]["temperature"]
        except Exception as e:
            logger.error(f"Error getting temperature (fallback): {e}")
        return 0.0

    def get_power_usage(gpu_id: int = 0) -> float:
        """Fallback power usage function"""
        try:
            gpus = query()
            if gpu_id < len(gpus):
                return gpus[gpu_id]["power_usage"]
        except Exception as e:
            logger.error(f"Error getting power usage (fallback): {e}")
        return 0.0

# Add detailed NVML initialization check
def check_nvml_availability() -> tuple[bool, str]:
    """
    Check detailed availability of NVML and provide diagnostic information.
    
    Returns:
        tuple[bool, str]: (success, message) where success indicates if NVML is available
                          and message contains diagnostic information.

    """
    try:
        # Try to find nvidia-ml library
        nvml_path = ctypes.util.find_library("nvidia-ml")

        if not nvml_path:
            return False, "NVIDIA Management Library (NVML) not found on system path"

        # Try to import pynvml and initialize it
        import pynvml
        pynvml.nvmlInit()

        # If we got here, it's successfully initialized
        driver_version = pynvml.nvmlSystemGetDriverVersion().decode()
        device_count = pynvml.nvmlDeviceGetCount()

        return True, f"NVML initialized successfully: Driver {driver_version}, {device_count} GPUs found"

    except ImportError:
        return False, "pynvml module not installed or not importable"
    except Exception as e:
        # This provides more detailed error for specific NVML failures
        error_msg = str(e)
        if "library not found" in error_msg.lower():
            return False, f"NVML library found at {nvml_path} but could not be loaded (CUDA missing?)"
        if "function not found" in error_msg.lower():
            return False, "NVML found but required functions missing (outdated driver?)"
        return False, f"NVML initialization failed: {error_msg}"

# Add a function to re-probe for GPUs
def reprobe() -> tuple[int, str]:
    """
    Re-detect GPUs and reset GPU detection.
    
    Returns:
        tuple[int, str]: (gpu_count, message) where gpu_count is the number of GPUs detected
                         and message contains driver version or error information.

    """
    global NVML_INITIALIZED

    try:
        # Clear any mock mode flag unless explicitly set
        env_mock = os.environ.get("DUALGPUOPT_MOCK_GPU", "").lower() in ("1", "true", "yes", "on")
        if not env_mock:
            set_mock_mode(False)

        # Try to initialize NVML if not already
        if not NVML_INITIALIZED:
            success, message = check_nvml_availability()
            if success:
                # Update the global flag if we're running in the original module
                if "dualgpuopt.gpu.common" in globals():
                    import dualgpuopt.gpu.common
                    dualgpuopt.gpu.common.NVML_INITIALIZED = True
                NVML_INITIALIZED = True
            else:
                logger.warning(f"GPU re-probe failed: {message}")
                return 0, message

        # Get updated GPU information
        count = get_gpu_count()

        # Get driver version
        try:
            import pynvml
            driver_version = pynvml.nvmlSystemGetDriverVersion().decode()
        except Exception:
            driver_version = "Unknown"

        return count, f"Driver {driver_version}"

    except Exception as e:
        logger.error(f"Error during GPU re-probe: {e}")
        return 0, f"Error: {e!s}"

# Import error handling
try:
    from dualgpuopt.error_handler import ErrorCategory, ErrorSeverity, handle_exceptions

    error_handler_available = True
except ImportError:
    error_handler_available = False
    logger.warning("Error handler not available, using simplified error handling")


# Apply error handling decorator if available
def _apply_error_handler(component="GPUInfo", category=ErrorCategory.GPU_ERROR):
    """Apply error handling decorator if available"""

    def decorator(func):
        if error_handler_available:
            return handle_exceptions(
                component=component, severity=ErrorSeverity.ERROR, reraise=False
            )(func)
        # Simple error handling if dedicated error handler isn't available
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                # Return appropriate default values based on function name
                if "count" in func.__name__:
                    return 0
                if "names" in func.__name__:
                    return []
                if "memory" in func.__name__:
                    return {"total": 8192, "used": 0, "free": 8192}
                if any(x in func.__name__ for x in ["temperature", "power", "util"]):
                    return 0
                return None

        return wrapper

    return decorator


# Compatibility function for code expecting get_gpu_info
@_apply_error_handler()
def get_gpu_info() -> list[dict[str, Any]]:
    """Get GPU information (compatibility function)"""
    return query()


# Generate mock GPU data with configurable count
def _generate_mock_gpus(count: int = 2) -> list[dict[str, Any]]:
    """
    Generate mock GPU data for testing

    Args:
    ----
        count: Number of mock GPUs to generate

    Returns:
    -------
        List of GPU dictionaries with mock data

    """
    import random

    gpus = []
    for i in range(count):
        # Create different tiers of GPUs
        if i == 0:
            # High-end GPU
            name = "NVIDIA GeForce RTX 5090 (MOCK)"
            mem_total = 24 * 1024  # 24 GB
            mem_used = random.randint(2 * 1024, 8 * 1024)  # 2-8 GB used
            power_limit = 450
        elif i == 1:
            # Mid-range GPU
            name = "NVIDIA GeForce RTX 4080 (MOCK)"
            mem_total = 16 * 1024  # 16 GB
            mem_used = random.randint(1 * 1024, 6 * 1024)  # 1-6 GB used
            power_limit = 320
        else:
            # Low-end GPU
            name = f"NVIDIA GeForce RTX 3060 #{i} (MOCK)"
            mem_total = 12 * 1024  # 12 GB
            mem_used = random.randint(1 * 1024, 4 * 1024)  # 1-4 GB used
            power_limit = 170

        # Generate other values
        utilization = random.randint(5, 80)
        temperature = 40 + int(utilization / 2)
        power_usage = (power_limit * utilization / 100) + random.randint(-20, 20)

        gpus.append(
            {
                "id": i,
                "name": name,
                "type": "cuda",
                "mem_total": mem_total,
                "mem_used": mem_used,
                "util": utilization,
                "temperature": temperature,
                "power_usage": power_usage,
                "power_limit": power_limit,
                "clock_sm": random.randint(1500, 2000),
                "clock_memory": random.randint(8000, 10000),
            }
        )

    return gpus


# Mock GPU class for compatibility
class GPU:
    """GPU class for backward compatibility"""

    def __init__(self, gpu_data: dict[str, Any]):
        self.id = gpu_data.get("id", 0)
        self.name = gpu_data.get("name", "Unknown GPU")
        self.type = gpu_data.get("type", "unknown")
        self.mem_total = gpu_data.get("mem_total", 0)
        self.mem_used = gpu_data.get("mem_used", 0)
        self.util = gpu_data.get("util", 0)
        self.temperature = gpu_data.get("temperature", 0.0)
        self.power_usage = gpu_data.get("power_usage", 0.0)
        self.clock_sm = gpu_data.get("clock_sm", 0)
        self.clock_memory = gpu_data.get("clock_memory", 0)

    @property
    def mem_free(self) -> int:
        """Get free memory in MB"""
        return self.mem_total - self.mem_used

    def get_memory_info(self) -> dict[str, int]:
        """Get memory information"""
        return {
            "total": self.mem_total,
            "used": self.mem_used,
            "free": self.mem_free,
        }

    def get_utilization(self) -> int:
        """Get GPU utilization"""
        return self.util

    def get_temperature(self) -> float:
        """Get GPU temperature"""
        return self.temperature

    def get_power_usage(self) -> float:
        """Get power usage in watts"""
        return self.power_usage

    @classmethod
    @_apply_error_handler()
    def get_gpus(cls) -> list[GPU]:
        """Get list of GPU objects"""
        try:
            return [cls(gpu_data) for gpu_data in query()]
        except Exception as e:
            logger.error(f"Error getting GPU objects: {e}")
            # Return at least one mock GPU as fallback
            return [cls(_generate_mock_gpus(1)[0])]

    @classmethod
    @_apply_error_handler()
    def get_gpu_count(cls) -> int:
        """Get number of GPUs"""
        return get_gpu_count()

    @classmethod
    @_apply_error_handler()
    def get_gpu_names(cls) -> list[str]:
        """Get list of GPU names"""
        return get_gpu_names()


# For backward compatibility - re-export the _generate_mock_gpus function
generate_mock_gpus = _generate_mock_gpus
