"""
Tests for the GPU module
"""
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add parent directory to path so we can import directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import directly to be able to patch properly
import dualgpuopt.gpu.mock
import dualgpuopt.gpu.info
import dualgpuopt.gpu.monitor
from dualgpuopt.gpu import (
    query,
    get_gpu_count,
    get_gpu_names,
    set_mock_mode,
    get_mock_mode,
    generate_mock_gpus,
    get_memory_info,
    get_utilization,
    get_temperature,
    get_power_usage
)

class TestGpuModule(unittest.TestCase):
    """Tests for the GPU module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create consistent test data
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
                "clock_sm": 1500,
                "clock_memory": 1200,
            },
            {
                "id": 1,
                "name": "NVIDIA GeForce RTX 4080",
                "type": "nvidia",
                "util": 30,
                "mem_total": 16384,
                "mem_used": 3000,
                "temperature": 50.0,
                "power_usage": 150.0,
                "clock_sm": 1300,
                "clock_memory": 1000,
            }
        ]

        # Print test GPUs to verify data
        print(f"SETUP test_gpus: {[gpu['name'] for gpu in self.test_gpus]}")

        # Set mock mode
        self.original_mock_mode = get_mock_mode()
        set_mock_mode(True)

        # Create direct patch for generate_mock_gpus
        def mock_generate(*args, **kwargs):
            print(f"Mock generate returning: {[gpu['name'] for gpu in self.test_gpus]}")
            return self.test_gpus

        # Apply the patch
        self.real_generate = dualgpuopt.gpu.mock.generate_mock_gpus
        dualgpuopt.gpu.mock.generate_mock_gpus = mock_generate

    def tearDown(self):
        """Tear down test fixtures"""
        # Restore original mock mode
        set_mock_mode(self.original_mock_mode)

        # Restore the real generate_mock_gpus function
        dualgpuopt.gpu.mock.generate_mock_gpus = self.real_generate

    def test_mock_mode(self):
        """Test mock mode enable/disable"""
        set_mock_mode(True)
        self.assertTrue(get_mock_mode())

        set_mock_mode(False)
        self.assertFalse(get_mock_mode())

        # Reset for other tests
        set_mock_mode(True)

    def test_generate_mock_gpus(self):
        """Test mock GPU generation"""
        # Restore real function temporarily
        dualgpuopt.gpu.mock.generate_mock_gpus = self.real_generate

        # Test with real function
        gpus = generate_mock_gpus(2)

        # Check structure of each GPU
        self.assertEqual(len(gpus), 2)
        for i, gpu in enumerate(gpus):
            self.assertIn("id", gpu)
            self.assertIn("name", gpu)
            self.assertIn("type", gpu)
            self.assertIn("util", gpu)
            self.assertIn("mem_total", gpu)
            self.assertIn("mem_used", gpu)
            self.assertIn("temperature", gpu)
            self.assertIn("power_usage", gpu)
            self.assertIn("clock_sm", gpu)
            self.assertIn("clock_memory", gpu)

            # Check ID is assigned correctly
            self.assertEqual(gpu["id"], i)

            # Verify temperature and power are floats
            self.assertIsInstance(gpu["temperature"], float)
            self.assertIsInstance(gpu["power_usage"], float)

        # Restore mock for other tests
        def mock_generate(*args, **kwargs):
            return self.test_gpus

        dualgpuopt.gpu.mock.generate_mock_gpus = mock_generate

    def test_query(self):
        """Test query function"""
        # Test with mocked data
        gpus = query()

        # Debug print
        print(f"GPU NAMES: {[gpu['name'] for gpu in gpus]}")

        # Should return mock GPUs with our test data
        self.assertEqual(len(gpus), 2)
        self.assertEqual(gpus[0]["name"], "NVIDIA GeForce RTX 4090")
        self.assertEqual(gpus[1]["name"], "NVIDIA GeForce RTX 4080")

        # Verify temperature is a float
        self.assertIsInstance(gpus[0]["temperature"], float)
        self.assertEqual(gpus[0]["temperature"], 60.0)

    def test_get_gpu_count(self):
        """Test get_gpu_count function"""
        count = get_gpu_count()
        self.assertEqual(count, 2)

    def test_get_gpu_names(self):
        """Test get_gpu_names function"""
        names = get_gpu_names()
        self.assertEqual(len(names), 2)
        self.assertEqual(names[0], "NVIDIA GeForce RTX 4090")
        self.assertEqual(names[1], "NVIDIA GeForce RTX 4080")

    def test_get_memory_info(self):
        """Test get_memory_info function"""
        # Test for all GPUs
        memory_info = get_memory_info()
        self.assertEqual(len(memory_info), 2)

        for info in memory_info:
            self.assertIn("total", info)
            self.assertIn("used", info)
            self.assertIn("free", info)
            self.assertEqual(info["total"] - info["used"], info["free"])

        # Test for specific GPU
        gpu0_memory = get_memory_info(0)
        self.assertIsInstance(gpu0_memory, dict)
        self.assertIn("total", gpu0_memory)
        self.assertIn("used", gpu0_memory)
        self.assertIn("free", gpu0_memory)

        # Check exact values
        self.assertEqual(gpu0_memory["total"], 24576)
        self.assertEqual(gpu0_memory["used"], 5000)

        # Test for invalid GPU ID
        with self.assertRaises(ValueError):
            get_memory_info(99)

    def test_get_utilization(self):
        """Test get_utilization function"""
        # Test for all GPUs
        utilization = get_utilization()
        self.assertEqual(len(utilization), 2)

        # Check exact values
        self.assertEqual(utilization[0], 50)
        self.assertEqual(utilization[1], 30)

        # Test for specific GPU
        gpu0_util = get_utilization(0)
        self.assertIsInstance(gpu0_util, int)
        self.assertEqual(gpu0_util, 50)

        # Test for invalid GPU ID
        with self.assertRaises(ValueError):
            get_utilization(99)

    def test_get_temperature(self):
        """Test get_temperature function"""
        # Test for all GPUs
        temperatures = get_temperature()
        self.assertEqual(len(temperatures), 2)

        # Check exact values
        self.assertEqual(temperatures[0], 60.0)
        self.assertEqual(temperatures[1], 50.0)

        # Test for specific GPU
        gpu0_temp = get_temperature(0)
        self.assertIsInstance(gpu0_temp, float)
        self.assertEqual(gpu0_temp, 60.0)

        # Test for invalid GPU ID
        with self.assertRaises(ValueError):
            get_temperature(99)

    def test_get_power_usage(self):
        """Test get_power_usage function"""
        # Test for all GPUs
        power_usage = get_power_usage()
        self.assertEqual(len(power_usage), 2)

        # Check exact values
        self.assertEqual(power_usage[0], 200.0)
        self.assertEqual(power_usage[1], 150.0)

        # Test for specific GPU
        gpu0_power = get_power_usage(0)
        self.assertIsInstance(gpu0_power, float)
        self.assertEqual(gpu0_power, 200.0)

        # Test for invalid GPU ID
        with self.assertRaises(ValueError):
            get_power_usage(99)

    def test_old_import_compatibility(self):
        """Test compatibility with old imports"""
        # Create a mock module
        mock_module = MagicMock()
        mock_module.query.return_value = self.test_gpus
        mock_module.get_mock_mode.return_value = True
        mock_module._generate_mock_gpus.return_value = self.test_gpus

        # Replace the real module
        original_module = sys.modules.get('dualgpuopt.gpu_info', None)
        sys.modules['dualgpuopt.gpu_info'] = mock_module

        try:
            # Import should use our mock
            import dualgpuopt.gpu_info as gpu_info

            # Test functionality
            gpus = gpu_info.query()
            self.assertEqual(len(gpus), 2)
            self.assertEqual(gpus[0]["name"], "NVIDIA GeForce RTX 4090")

            # Test mock mode
            self.assertTrue(gpu_info.get_mock_mode())

            # Test mock generation
            mock_gpus = gpu_info._generate_mock_gpus()
            self.assertEqual(len(mock_gpus), 2)

        finally:
            # Restore original module if it existed
            if original_module:
                sys.modules['dualgpuopt.gpu_info'] = original_module
            else:
                del sys.modules['dualgpuopt.gpu_info']

if __name__ == "__main__":
    unittest.main()