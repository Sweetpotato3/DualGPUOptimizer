"""
GPU information module for querying GPU details
"""
from __future__ import annotations

from typing import Any

from dualgpuopt.gpu.common import IS_NVIDIA, MOCK_MODE, NVML_INITIALIZED, logger
from dualgpuopt.gpu.mock import generate_mock_gpus


def query() -> list[dict[str, Any]]:
    """
    Query GPU information with platform detection

    Returns
    -------
        List of dictionaries with GPU information
    """
    if MOCK_MODE:
        print("Query: Using MOCK_MODE")
        result = generate_mock_gpus()
        print(f"Query: Mock GPUs: {[gpu['name'] for gpu in result]}")
        return result

    if IS_NVIDIA:
        return _query_nvidia()
    return _query_mac()


def get_gpu_count() -> int:
    """
    Get the number of available GPUs

    Returns
    -------
        Number of available GPUs
    """
    return len(query())


def get_gpu_names() -> list[str]:
    """
    Get the names of available GPUs

    Returns
    -------
        List of GPU names
    """
    return [gpu["name"] for gpu in query()]


def _query_nvidia() -> list[dict[str, Any]]:
    """
    Query NVIDIA GPUs using NVML

    Returns
    -------
        List of dictionaries with NVIDIA GPU information
    """
    if MOCK_MODE or not NVML_INITIALIZED:
        return generate_mock_gpus()

    try:
        import pynvml

        gpus: list[dict[str, Any]] = []

        for idx in range(pynvml.nvmlDeviceGetCount()):
            h = pynvml.nvmlDeviceGetHandleByIndex(idx)
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(h) / 1000.0  # Convert from mW to W

            # Get GPU name with proper string handling
            device_name = pynvml.nvmlDeviceGetName(h)
            if isinstance(device_name, bytes):
                device_name = device_name.decode("utf-8")

            gpus.append(
                {
                    "id": idx,
                    "name": device_name,
                    "type": "nvidia",
                    "util": util.gpu,
                    "mem_total": mem.total // 1_048_576,
                    "mem_used": (mem.total - mem.free) // 1_048_576,
                    "temperature": temp,
                    "power_usage": power,
                    "clock_sm": pynvml.nvmlDeviceGetClockInfo(h, pynvml.NVML_CLOCK_SM),
                    "clock_memory": pynvml.nvmlDeviceGetClockInfo(h, pynvml.NVML_CLOCK_MEM),
                },
            )
        return gpus
    except Exception as e:
        logger.error(f"Error querying NVIDIA GPUs: {e}")
        return generate_mock_gpus()


def _query_mac() -> list[dict[str, Any]]:
    """
    Query Apple GPUs using powermetrics

    Returns
    -------
        List of dictionaries with Apple GPU information
    """
    if MOCK_MODE:
        return generate_mock_gpus()

    try:
        import json
        import shutil
        import subprocess

        import psutil

        if not shutil.which("powermetrics"):
            logger.debug("powermetrics not found; returning CPU stats only")
            return []

        out = subprocess.check_output(
            ["powermetrics", "-n", "1", "-i", "200", "--json"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        data = json.loads(out)
        gpu = data["gpu_status"]["activeGPU"]
        return [
            {
                "id": 0,
                "name": gpu["modelName"],
                "type": "apple",
                "util": gpu.get("utilisationPercent", 0),
                "mem_total": psutil.virtual_memory().total // 1_048_576,
                "mem_used": psutil.virtual_memory().used // 1_048_576,
                "temperature": None,  # powermetrics doesn't provide GPU temp
                "power_usage": 0.0,  # Not available on Mac
                "clock_sm": 0,
                "clock_memory": 0,
            },
        ]
    except Exception as e:
        logger.warning(f"powermetrics failed: {e}")
        return generate_mock_gpus()
