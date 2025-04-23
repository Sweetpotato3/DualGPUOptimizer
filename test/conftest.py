import os
import sys
from unittest.mock import MagicMock

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Mock GPU fixtures
@pytest.fixture()
def mock_gpu_info():
    """Create a mock GPU info object with standard testing properties."""
    mock_gpu = MagicMock()
    mock_gpu.name = "NVIDIA Test GPU"
    mock_gpu.total_memory = 8 * 1024 * 1024 * 1024  # 8GB
    mock_gpu.available_memory = 6 * 1024 * 1024 * 1024  # 6GB
    mock_gpu.temperature = 65
    mock_gpu.utilization = 30
    mock_gpu.power_usage = 100
    mock_gpu.power_limit = 250
    mock_gpu.fan_speed = 40
    mock_gpu.clock_speed = 1500
    mock_gpu.memory_clock = 7000
    return mock_gpu


@pytest.fixture()
def mock_gpu_list():
    """Create a list of mock GPUs for testing multi-GPU scenarios."""
    gpu1 = MagicMock()
    gpu1.name = "NVIDIA Test GPU 1"
    gpu1.total_memory = 8 * 1024 * 1024 * 1024  # 8GB
    gpu1.available_memory = 6 * 1024 * 1024 * 1024  # 6GB

    gpu2 = MagicMock()
    gpu2.name = "NVIDIA Test GPU 2"
    gpu2.total_memory = 12 * 1024 * 1024 * 1024  # 12GB
    gpu2.available_memory = 10 * 1024 * 1024 * 1024  # 10GB

    return [gpu1, gpu2]


# Event bus fixture
@pytest.fixture()
def mock_event_bus():
    """Create a mock event bus for testing event-driven components."""
    event_bus = MagicMock()
    event_bus.subscribe = MagicMock()
    event_bus.publish = MagicMock()
    return event_bus


# Mock telemetry fixture
@pytest.fixture()
def mock_telemetry():
    """Create a mock telemetry service for testing."""
    telemetry = MagicMock()
    telemetry.get_metrics = MagicMock(
        return_value={
            "memory_used": [4 * 1024 * 1024 * 1024, 6 * 1024 * 1024 * 1024],
            "memory_total": [8 * 1024 * 1024 * 1024, 12 * 1024 * 1024 * 1024],
            "utilization": [30, 40],
            "temperature": [65, 70],
            "power_usage": [100, 150],
            "power_limit": [250, 300],
            "clock_speed": [1500, 1600],
        }
    )
    return telemetry


# Environment variable fixture
@pytest.fixture()
def clean_env():
    """Provide a clean environment by temporarily clearing relevant env vars."""
    preserved = {}
    prefixes = ["DUALGPUOPT_", "CUDA_", "NVIDIA_"]

    for key in os.environ:
        for prefix in prefixes:
            if key.startswith(prefix):
                preserved[key] = os.environ[key]
                del os.environ[key]
                break

    yield

    # Restore environment
    for key, value in preserved.items():
        os.environ[key] = value
