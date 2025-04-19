"""
Test configuration for pytest with mocks for external dependencies.
"""
import sys
from unittest import mock

import pytest


# Mock pynvml module to avoid requiring real GPU hardware
class MockNVMLError(Exception):
    """Mock NVML Error class."""
    pass


@pytest.fixture(autouse=True, scope="session")
def mock_pynvml():
    """Mock the pynvml module for all tests."""
    mock_module = mock.MagicMock()
    mock_module.NVMLError = MockNVMLError
    
    # Mock device attributes
    mock_device = mock.MagicMock()
    mock_device.return_value = mock_device
    mock_device.total = 24 * 1024 * 1024 * 1024  # 24GB
    mock_device.free = 20 * 1024 * 1024 * 1024   # 20GB
    mock_device.gpu = 30  # 30% utilization
    
    # Set up mock methods
    mock_module.nvmlInit.return_value = None
    mock_module.nvmlDeviceGetCount.return_value = 2
    mock_module.nvmlDeviceGetHandleByIndex.return_value = mock_device
    mock_module.nvmlDeviceGetMemoryInfo.return_value = mock_device
    mock_module.nvmlDeviceGetName.return_value = b"NVIDIA GeForce RTX 3090"
    mock_module.nvmlDeviceGetUtilizationRates.return_value = mock_device
    mock_module.nvmlDeviceGetPcieThroughput.return_value = 1000  # 1000 KB/s
    mock_module.nvmlShutdown.return_value = None
    
    # Constants
    mock_module.NVML_PCIE_UTIL_RX_BYTES = 0
    mock_module.NVML_PCIE_UTIL_TX_BYTES = 1
    
    # Apply the mock
    sys.modules["pynvml"] = mock_module
    yield mock_module 