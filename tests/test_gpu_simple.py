"""
Simplified tests for the GPU module
"""
import unittest
from unittest.mock import patch
import sys
import os

# Add parent directory to path so we can import directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestGpuModuleSimple(unittest.TestCase):
    """Simplified tests for the GPU module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create test data
        self.test_gpus = [
            {
                "id": 0,
                "name": "NVIDIA GeForce RTX 4090",
                "type": "nvidia",
                "util": 50,
                "mem_total": 24576,
                "mem_used": 5000,
                "temperature": 60.0,
                "power_usage": 200.0,
            }
        ]

    def test_mock_gpu_functions(self):
        """Test that mock GPU functions work correctly"""
        # Import and test the mock module
        with patch('dualgpuopt.gpu.mock.generate_mock_gpus', return_value=self.test_gpus):
            from dualgpuopt.gpu.mock import generate_mock_gpus

            # Test the function
            gpus = generate_mock_gpus()
            self.assertEqual(len(gpus), 1)
            self.assertEqual(gpus[0]["name"], "NVIDIA GeForce RTX 4090")
            self.assertEqual(gpus[0]["temperature"], 60.0)

    def test_gpu_info_query(self):
        """Test that query function returns expected data"""
        # Import and test the info module
        with patch('dualgpuopt.gpu.mock.generate_mock_gpus', return_value=self.test_gpus):
            with patch('dualgpuopt.gpu.common.MOCK_MODE', True):
                from dualgpuopt.gpu.info import query

                # Test the function
                gpus = query()
                self.assertEqual(len(gpus), 1)
                self.assertEqual(gpus[0]["name"], "NVIDIA GeForce RTX 4090")
                self.assertEqual(gpus[0]["temperature"], 60.0)

    def test_gpu_monitoring(self):
        """Test that monitoring functions work correctly"""
        # Import and test the monitor module
        with patch('dualgpuopt.gpu.info.query', return_value=self.test_gpus):
            from dualgpuopt.gpu.monitor import get_temperature, get_utilization, get_memory_info

            # Test temperature function
            temp = get_temperature(0)
            self.assertIsInstance(temp, float)
            self.assertEqual(temp, 60.0)

            # Test utilization function
            util = get_utilization(0)
            self.assertIsInstance(util, int)
            self.assertEqual(util, 50)

            # Test memory info function
            mem = get_memory_info(0)
            self.assertEqual(mem["total"], 24576)
            self.assertEqual(mem["used"], 5000)
            self.assertEqual(mem["free"], 19576)

    def test_public_api(self):
        """Test that the public API works correctly"""
        # Mock the internals
        with patch('dualgpuopt.gpu.info.query', return_value=self.test_gpus):
            # Import from public API
            from dualgpuopt.gpu import get_gpu_names, get_gpu_count, get_temperature

            # Test functions
            self.assertEqual(get_gpu_count(), 1)
            self.assertEqual(get_gpu_names(), ["NVIDIA GeForce RTX 4090"])
            self.assertEqual(get_temperature(0), 60.0)

if __name__ == "__main__":
    unittest.main()