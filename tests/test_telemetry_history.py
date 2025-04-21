"""
Tests for the telemetry history functionality
"""
import time
import unittest
from dualgpuopt.telemetry_history import HistoryBuffer, SECONDS


class TestHistoryBuffer(unittest.TestCase):
    """Test the HistoryBuffer functionality"""

    def test_push_and_snapshot(self):
        """Test basic push and snapshot operations"""
        hist = HistoryBuffer()
        hist.push("test_metric", 42.0)
        
        # Verify snapshot returns the pushed value
        snapshot = hist.snapshot("test_metric")
        self.assertEqual(len(snapshot), 1)
        self.assertAlmostEqual(snapshot[0][1], 42.0)
        
    def test_missing_metric(self):
        """Test snapshot of non-existent metric"""
        hist = HistoryBuffer()
        snapshot = hist.snapshot("nonexistent")
        self.assertEqual(len(snapshot), 0)

    def test_multiple_metrics(self):
        """Test pushing multiple metrics"""
        hist = HistoryBuffer()
        metrics = ["cpu", "memory", "disk"]
        values = [75.0, 80.0, 90.0]
        
        for m, v in zip(metrics, values):
            hist.push(m, v)
            
        for m, v in zip(metrics, values):
            snapshot = hist.snapshot(m)
            self.assertEqual(len(snapshot), 1)
            self.assertAlmostEqual(snapshot[0][1], v)
    
    def test_trim_functionality(self):
        """Test that old data gets trimmed"""
        hist = HistoryBuffer()
        # Override SECONDS for testing
        test_duration = 0.1  # 100ms
        original_seconds = SECONDS
        
        try:
            # Monkeypatch SECONDS for this test
            import dualgpuopt.telemetry_history
            dualgpuopt.telemetry_history.SECONDS = test_duration
            
            # Push a value now
            hist.push("trim_test", 1.0)
            
            # Wait for slightly longer than our test duration
            time.sleep(test_duration * 1.1)
            
            # Push another value
            hist.push("trim_test", 2.0)
            
            # Get snapshot - should only have the newest value
            snapshot = hist.snapshot("trim_test")
            self.assertEqual(len(snapshot), 1)
            self.assertAlmostEqual(snapshot[0][1], 2.0)
            
        finally:
            # Restore original value
            dualgpuopt.telemetry_history.SECONDS = original_seconds
            
    def test_multiple_values_over_time(self):
        """Test pushing multiple values for the same metric"""
        hist = HistoryBuffer()
        
        # Push several values with small delays
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for v in values:
            hist.push("multi_test", v)
            time.sleep(0.01)  # Small delay between pushes
            
        # Verify all values are in the snapshot
        snapshot = hist.snapshot("multi_test")
        self.assertEqual(len(snapshot), len(values))
        
        # Values should be in chronological order
        actual_values = [v for _, v in snapshot]
        self.assertEqual(actual_values, values)


if __name__ == "__main__":
    unittest.main() 