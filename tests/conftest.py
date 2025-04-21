"""
Test configuration for pytest with mocks for external dependencies.
"""
import sys
from unittest import mock

import pytest


# Mock pynvml module to avoid requiring real GPU hardware
class MockNVMLError(Exception):
    """Mock NVML Error class."""


@pytest.fixture(autouse=True, scope="session")
def mock_pynvml():
    """Mock the pynvml module for all tests."""
    mock_module = mock.MagicMock()
    mock_module.NVMLError = MockNVMLError

    # Mock device attributes for GPU 0
    mock_device_0 = mock.MagicMock()
    mock_device_0.return_value = mock_device_0
    mock_device_0.total = 24 * 1024 * 1024 * 1024  # 24GB
    mock_device_0.free = 19 * 1024 * 1024 * 1024   # 19GB to give ~5GB used (5000MB) as tests expect
    mock_device_0.gpu = 50  # 50% utilization as tests expect

    # Mock device attributes for GPU 1
    mock_device_1 = mock.MagicMock()
    mock_device_1.return_value = mock_device_1
    mock_device_1.total = 16 * 1024 * 1024 * 1024  # 16GB
    mock_device_1.free = 13 * 1024 * 1024 * 1024   # 13GB to give ~3GB used (3000MB) as tests expect
    mock_device_1.gpu = 30  # 30% utilization as tests expect

    # Set up mock methods
    mock_module.nvmlInit.return_value = None
    mock_module.nvmlDeviceGetCount.return_value = 2

    # Use side_effect to return different values based on the GPU index
    def get_handle_by_index(idx):
        return [mock_device_0, mock_device_1][idx]
    mock_module.nvmlDeviceGetHandleByIndex.side_effect = get_handle_by_index

    # Memory info differs by GPU
    def get_memory_info(handle):
        return handle
    mock_module.nvmlDeviceGetMemoryInfo.side_effect = get_memory_info

    # GPU name differs by GPU
    def get_name(handle):
        if handle == mock_device_0:
            return b"NVIDIA GeForce RTX 4090"
        return b"NVIDIA GeForce RTX 4080"
    mock_module.nvmlDeviceGetName.side_effect = get_name

    # Utilization differs by GPU
    def get_utilization(handle):
        return handle
    mock_module.nvmlDeviceGetUtilizationRates.side_effect = get_utilization

    # Temperature differs by GPU
    def get_temperature(handle, _):
        if handle == mock_device_0:
            return 60.0
        return 50.0
    mock_module.nvmlDeviceGetTemperature.side_effect = get_temperature

    # Power usage differs by GPU
    def get_power_usage(handle):
        if handle == mock_device_0:
            return 200000.0  # 200W in mW
        return 150000.0  # 150W in mW
    mock_module.nvmlDeviceGetPowerUsage.side_effect = get_power_usage

    # Clock speed differs by GPU
    def get_clock_info(handle, _):
        if handle == mock_device_0:
            return 1500
        return 1300
    mock_module.nvmlDeviceGetClockInfo.side_effect = get_clock_info

    # Other mocks
    mock_module.nvmlDeviceGetPcieThroughput.return_value = 1000  # 1000 KB/s
    mock_module.nvmlShutdown.return_value = None

    # Constants
    mock_module.NVML_PCIE_UTIL_RX_BYTES = 0
    mock_module.NVML_PCIE_UTIL_TX_BYTES = 1
    mock_module.NVML_TEMPERATURE_GPU = 0

    # Apply the mock
    sys.modules["pynvml"] = mock_module
    yield mock_module