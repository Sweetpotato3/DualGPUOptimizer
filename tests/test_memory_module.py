"""
Tests for the Memory module
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path so we can import directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dualgpuopt.memory import (
    monitor,
    metrics,
    alerts,
    recovery,
    predictor
)

class TestMemoryMonitor(unittest.TestCase):
    """Tests for the Memory Monitor module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a test monitor instance with mocked GPU info
        self.mock_gpu_info = MagicMock()
        self.mock_gpu_info.query.return_value = [
            {
                "id": 0,
                "name": "Test GPU 0",
                "type": "nvidia",
                "util": 50,
                "mem_total": 16384,  # 16 GB
                "mem_used": 8192,     # 8 GB (50% usage)
                "temperature": 70.0,
                "power_usage": 200.0,
            },
            {
                "id": 1,
                "name": "Test GPU 1",
                "type": "nvidia",
                "util": 30,
                "mem_total": 24576,  # 24 GB
                "mem_used": 4096,     # 4 GB (~16% usage)
                "temperature": 60.0,
                "power_usage": 150.0,
            }
        ]

        # Apply the mock
        self.patcher = patch('dualgpuopt.memory.monitor.gpu_info', self.mock_gpu_info)
        self.patcher.start()

        # Create a test monitor
        self.memory_monitor = monitor.MemoryMonitor()

    def tearDown(self):
        """Tear down test fixtures"""
        self.patcher.stop()

    def test_get_memory_usage(self):
        """Test get_memory_usage method"""
        usage = self.memory_monitor.get_memory_usage()

        # Should return a dictionary with GPU IDs as keys
        self.assertIn(0, usage)
        self.assertIn(1, usage)

        # Check structure
        for gpu_id, info in usage.items():
            self.assertIn("total", info)
            self.assertIn("used", info)
            self.assertIn("free", info)
            self.assertIn("percent", info)

            # Check calculations
            self.assertEqual(info["free"], info["total"] - info["used"])
            self.assertEqual(info["percent"], round(info["used"] / info["total"] * 100, 1))

    def test_is_memory_critical(self):
        """Test is_memory_critical method"""
        # Mock high memory usage
        high_usage_mock = MagicMock()
        high_usage_mock.query.return_value = [
            {
                "id": 0,
                "name": "Test GPU 0",
                "mem_total": 16384,
                "mem_used": 15565,  # 95% usage
            }
        ]

        with patch('dualgpuopt.memory.monitor.gpu_info', high_usage_mock):
            # Create a new monitor with the high usage mock
            critical_monitor = monitor.MemoryMonitor()

            # Should report critical memory
            self.assertTrue(critical_monitor.is_memory_critical(0))

            # Lower threshold temporarily
            original_threshold = critical_monitor.CRITICAL_THRESHOLD
            critical_monitor.CRITICAL_THRESHOLD = 80
            self.assertTrue(critical_monitor.is_memory_critical(0))

            # Restore threshold
            critical_monitor.CRITICAL_THRESHOLD = original_threshold

    def test_is_memory_low(self):
        """Test is_memory_low method with normal and low memory"""
        # Default memory (50% usage)
        self.assertFalse(self.memory_monitor.is_memory_low(0))

        # Mock low memory
        low_memory_mock = MagicMock()
        low_memory_mock.query.return_value = [
            {
                "id": 0,
                "name": "Test GPU 0",
                "mem_total": 16384,
                "mem_used": 13107,  # 80% usage
            }
        ]

        with patch('dualgpuopt.memory.monitor.gpu_info', low_memory_mock):
            # Create a new monitor with the low memory mock
            low_monitor = monitor.MemoryMonitor()

            # Should report low memory
            self.assertTrue(low_monitor.is_memory_low(0))

class TestMemoryMetrics(unittest.TestCase):
    """Tests for the Memory Metrics module"""

    def test_calculate_usage_percent(self):
        """Test calculate_usage_percent function"""
        # Test normal case
        self.assertEqual(metrics.calculate_usage_percent(5000, 10000), 50.0)

        # Test zero total (should not crash)
        self.assertEqual(metrics.calculate_usage_percent(5000, 0), 100.0)

        # Test negative values (should handle gracefully)
        self.assertEqual(metrics.calculate_usage_percent(-100, 10000), 0.0)

        # Test very high usage
        self.assertEqual(metrics.calculate_usage_percent(9999, 10000), 100.0)

    def test_format_memory_size(self):
        """Test format_memory_size function"""
        # Test MB
        self.assertEqual(metrics.format_memory_size(100), "100 MB")

        # Test GB
        self.assertEqual(metrics.format_memory_size(1024), "1.0 GB")
        self.assertEqual(metrics.format_memory_size(10240), "10.0 GB")

        # Test precision
        self.assertEqual(metrics.format_memory_size(1536), "1.5 GB")
        self.assertEqual(metrics.format_memory_size(1536, precision=2), "1.50 GB")

class TestMemoryAlerts(unittest.TestCase):
    """Tests for the Memory Alerts module"""

    def test_alert_severity(self):
        """Test alert severity levels"""
        # Check that severity levels are ordered correctly
        self.assertLess(alerts.AlertSeverity.INFO, alerts.AlertSeverity.WARNING)
        self.assertLess(alerts.AlertSeverity.WARNING, alerts.AlertSeverity.ERROR)
        self.assertLess(alerts.AlertSeverity.ERROR, alerts.AlertSeverity.CRITICAL)

    def test_create_memory_alert(self):
        """Test create_memory_alert function"""
        # Test warning alert
        alert = alerts.create_memory_alert(0, 85.0, alerts.AlertSeverity.WARNING)
        self.assertEqual(alert.gpu_id, 0)
        self.assertEqual(alert.usage_percent, 85.0)
        self.assertEqual(alert.severity, alerts.AlertSeverity.WARNING)
        self.assertIn("85.0%", alert.message)
        self.assertIn("WARNING", alert.message)

        # Test critical alert
        alert = alerts.create_memory_alert(1, 95.0, alerts.AlertSeverity.CRITICAL)
        self.assertEqual(alert.gpu_id, 1)
        self.assertEqual(alert.usage_percent, 95.0)
        self.assertEqual(alert.severity, alerts.AlertSeverity.CRITICAL)
        self.assertIn("95.0%", alert.message)
        self.assertIn("CRITICAL", alert.message)

class TestMemoryRecovery(unittest.TestCase):
    """Tests for the Memory Recovery module"""

    @patch('dualgpuopt.memory.recovery.gc.collect')
    def test_attempt_memory_recovery(self, mock_gc_collect):
        """Test attempt_memory_recovery function"""
        # Mock monitoring functions
        mock_is_memory_low = MagicMock(return_value=True)

        # Test recovery attempts
        result = recovery.attempt_memory_recovery(0, is_memory_low_func=mock_is_memory_low)

        # Should call gc.collect
        mock_gc_collect.assert_called_once()

        # Function should return False since memory is still low after recovery
        self.assertFalse(result)

        # Test with successful recovery
        mock_is_memory_low.side_effect = [True, False]  # First call returns True, second call returns False
        result = recovery.attempt_memory_recovery(0, is_memory_low_func=mock_is_memory_low)

        # Function should return True since memory is no longer low
        self.assertTrue(result)

class TestMemoryPredictor(unittest.TestCase):
    """Tests for the Memory Predictor module"""

    def test_predict_memory_usage(self):
        """Test predict_memory_usage function"""
        # Test with simple linear prediction
        # Historical data: memory increases by 1000 MB each sample
        history = [
            {"timestamp": 0, "gpu_id": 0, "used": 5000},
            {"timestamp": 1, "gpu_id": 0, "used": 6000},
            {"timestamp": 2, "gpu_id": 0, "used": 7000},
            {"timestamp": 3, "gpu_id": 0, "used": 8000},
            {"timestamp": 4, "gpu_id": 0, "used": 9000},
        ]

        # Predict next value (should be around 10000)
        prediction = predictor.predict_memory_usage(history, 0, 5)

        # Allow some flexibility in prediction algorithm
        self.assertGreaterEqual(prediction, 9500)
        self.assertLessEqual(prediction, 10500)

    def test_will_run_out_of_memory(self):
        """Test will_run_out_of_memory function"""
        # Mock monitoring functions
        mock_get_memory_usage = MagicMock(return_value={
            0: {"total": 16384, "used": 8192, "free": 8192, "percent": 50.0}
        })

        # With linear growth of 1000 MB per sample, memory should run out in ~8 samples
        memory_samples = [
            {"timestamp": 0, "gpu_id": 0, "used": 8192},
            {"timestamp": 1, "gpu_id": 0, "used": 9192},
            {"timestamp": 2, "gpu_id": 0, "used": 10192},
            {"timestamp": 3, "gpu_id": 0, "used": 11192},
        ]

        # Test prediction
        result = predictor.will_run_out_of_memory(
            0,
            memory_samples,
            get_memory_usage_func=mock_get_memory_usage
        )

        # Should predict OOM within the threshold period
        self.assertTrue(result.will_oom)

        # Time to OOM should be positive
        self.assertGreater(result.time_to_oom_seconds, 0)

        # With stable memory usage, should not predict OOM
        stable_samples = [
            {"timestamp": 0, "gpu_id": 0, "used": 8192},
            {"timestamp": 1, "gpu_id": 0, "used": 8192},
            {"timestamp": 2, "gpu_id": 0, "used": 8192},
            {"timestamp": 3, "gpu_id": 0, "used": 8192},
        ]

        result = predictor.will_run_out_of_memory(
            0,
            stable_samples,
            get_memory_usage_func=mock_get_memory_usage
        )

        # Should not predict OOM
        self.assertFalse(result.will_oom)

if __name__ == "__main__":
    unittest.main()