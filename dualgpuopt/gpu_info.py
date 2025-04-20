"""
GPU info module with platform-independent GPU detection
"""
from __future__ import annotations
import platform, logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("DualGPUOpt.GPUInfo")

IS_MAC = platform.system() == "Darwin"
IS_NVIDIA = not IS_MAC

# Global flag for mock mode
MOCK_MODE = False

try:
    if IS_NVIDIA:
        import pynvml
        pynvml.nvmlInit()
except (ImportError, Exception) as e:
    logger.warning(f"Failed to initialize NVML: {e}")
    MOCK_MODE = True

def set_mock_mode(enabled: bool) -> None:
    """Enable or disable mock GPU mode"""
    global MOCK_MODE
    MOCK_MODE = enabled
    logger.info(f"Mock GPU mode {'enabled' if enabled else 'disabled'}")

def get_mock_mode() -> bool:
    """Get current mock mode status"""
    return MOCK_MODE

def _query_nvidia() -> list[dict]:
    """Query NVIDIA GPUs using NVML"""
    if MOCK_MODE:
        return _generate_mock_gpus()
    
    try:
        gpus: list[dict] = []
        for idx in range(pynvml.nvmlDeviceGetCount()):
            h = pynvml.nvmlDeviceGetHandleByIndex(idx)
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(h) / 1000.0  # Convert from mW to W
            
            # Get GPU name with proper string handling
            device_name = pynvml.nvmlDeviceGetName(h)
            if isinstance(device_name, bytes):
                device_name = device_name.decode('utf-8')
            
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
                }
            )
        return gpus
    except Exception as e:
        logger.error(f"Error querying NVIDIA GPUs: {e}")
        return _generate_mock_gpus()

def _query_mac() -> list[dict]:
    """Query Apple GPUs using powermetrics"""
    if MOCK_MODE:
        return _generate_mock_gpus()
    
    import subprocess, json, shutil, psutil

    if not shutil.which("powermetrics"):
        logger.debug("powermetrics not found; returning CPU stats only")
        return []

    try:
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
                "power_usage": 0.0,   # Not available on Mac
                "clock_sm": 0,
                "clock_memory": 0,
            }
        ]
    except Exception as e:
        logger.warning(f"powermetrics failed: {e}")
        return _generate_mock_gpus()

def _generate_mock_gpus() -> list[dict]:
    """Generate mock GPU data for testing"""
    import random
    
    # Generate 1-2 GPUs with realistic specs
    gpu_count = 2  # Fixed at 2 for dual GPU optimization
    
    mock_gpus = []
    
    gpu_templates = [
        {
            "name": "NVIDIA GeForce RTX 4090",
            "mem_total": 24576,  # 24 GB
            "mem_base_used": 1024,  # Base memory usage (1 GB)
            "max_util": 98,
            "max_temp": 85,
            "power_range": (30, 450),  # Min/max power in W
        },
        {
            "name": "NVIDIA GeForce RTX 4080",
            "mem_total": 16384,  # 16 GB
            "mem_base_used": 768,  # Base memory usage
            "max_util": 98,
            "max_temp": 83,
            "power_range": (25, 320),  # Min/max power in W
        },
    ]
    
    for i in range(gpu_count):
        # Use the template for this index, or repeat the last one if out of templates
        template_idx = min(i, len(gpu_templates) - 1)
        template = gpu_templates[template_idx]
        
        # Random utilization between 1-max_util
        util = random.randint(1, template["max_util"])
        
        # Memory usage correlates somewhat with utilization
        mem_used = template["mem_base_used"] + int(util / 100 * (template["mem_total"] * 0.4))
        
        # Temperature correlates with utilization
        temp_base = 35
        temp_range = template["max_temp"] - temp_base
        temp = temp_base + (util / 100 * temp_range)
        
        # Power usage correlates with utilization
        pmin, pmax = template["power_range"]
        power = pmin + (util / 100 * (pmax - pmin))
        
        # Clock speeds correlate with utilization
        clock_base = 500
        clock_max = 2500
        clock = clock_base + (util / 100 * (clock_max - clock_base))
        
        mock_gpus.append({
            "id": i,
            "name": template["name"],
            "type": "nvidia",
            "util": util,
            "mem_total": template["mem_total"],
            "mem_used": mem_used,
            "temperature": temp,
            "power_usage": power,
            "clock_sm": int(clock),
            "clock_memory": int(clock * 0.75),  # Memory clock is typically lower
        })
    
    return mock_gpus

def query() -> list[dict]:
    """Query GPU information with platform detection"""
    if MOCK_MODE:
        return _generate_mock_gpus()
    
    if IS_NVIDIA:
        return _query_nvidia()
    return _query_mac() 