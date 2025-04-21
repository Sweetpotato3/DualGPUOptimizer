"""
Unit tests for the telemetry alert system
"""
import pytest
from unittest.mock import MagicMock, patch
import time

try:
    from dualgpuopt.telemetry import AlertLevel, GPUMetrics, TelemetryService
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    class AlertLevel:
        NORMAL = 0
        WARNING = 1
        CRITICAL = 2
        EMERGENCY = 3
    
    class GPUMetrics:
        pass

    class TelemetryService:
        pass

# Skip all tests if the module is not available
pytestmark = pytest.mark.skipif(
    not TELEMETRY_AVAILABLE,
    reason="Telemetry module not available"
)

class TestAlertLevels:
    """Test the AlertLevel functionality"""

    def test_alert_level_enum(self):
        """Test that AlertLevel enum is properly defined"""
        assert AlertLevel.NORMAL.value == 0
        assert AlertLevel.WARNING.value == 1
        assert AlertLevel.CRITICAL.value == 2
        assert AlertLevel.EMERGENCY.value == 3
        
        # Verify order for comparison operators
        assert AlertLevel.NORMAL < AlertLevel.WARNING
        assert AlertLevel.WARNING < AlertLevel.CRITICAL
        assert AlertLevel.CRITICAL < AlertLevel.EMERGENCY
        
        # Test max() operation for alert levels
        assert max(AlertLevel.NORMAL, AlertLevel.WARNING) == AlertLevel.WARNING
        assert max(AlertLevel.CRITICAL, AlertLevel.WARNING) == AlertLevel.CRITICAL
        assert max(AlertLevel.EMERGENCY, AlertLevel.CRITICAL) == AlertLevel.EMERGENCY

    def test_alert_detection_memory(self):
        """Test that alerts are correctly triggered based on memory usage"""
        # Normal memory usage (50%)
        metrics = GPUMetrics(
            gpu_id=0,
            name="Test GPU",
            utilization=30,
            memory_used=4096,
            memory_total=8192,
            temperature=60,
            power_usage=100,
            power_limit=200,
            fan_speed=40,
            clock_sm=1500,
            clock_memory=7000,
            pcie_tx=5000,
            pcie_rx=3000,
            timestamp=time.time()
        )
        assert metrics.get_alert_level() == AlertLevel.NORMAL
        
        # Warning level memory usage (75%)
        metrics.memory_used = 6144  # 75% of 8192
        assert metrics.get_alert_level() == AlertLevel.WARNING
        
        # Critical level memory usage (90%)
        metrics.memory_used = 7373  # 90% of 8192
        assert metrics.get_alert_level() == AlertLevel.CRITICAL
        
        # Emergency level memory usage (95%)
        metrics.memory_used = 7782  # 95% of 8192
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY
        
        # 100% memory usage
        metrics.memory_used = 8192
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY

    def test_alert_detection_temperature(self):
        """Test that alerts are correctly triggered based on temperature"""
        # Normal temperature
        metrics = GPUMetrics(
            gpu_id=0,
            name="Test GPU",
            utilization=30,
            memory_used=4096,
            memory_total=8192,
            temperature=60,
            power_usage=100,
            power_limit=200,
            fan_speed=40,
            clock_sm=1500,
            clock_memory=7000,
            pcie_tx=5000,
            pcie_rx=3000,
            timestamp=time.time()
        )
        assert metrics.get_alert_level() == AlertLevel.NORMAL
        
        # Warning level temperature
        metrics.temperature = 70
        assert metrics.get_alert_level() == AlertLevel.WARNING
        
        # Critical level temperature
        metrics.temperature = 80
        assert metrics.get_alert_level() == AlertLevel.CRITICAL
        
        # Emergency level temperature
        metrics.temperature = 90
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY
        
        # Very high temperature
        metrics.temperature = 95
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY

    def test_alert_detection_power(self):
        """Test that alerts are correctly triggered based on power usage"""
        # Normal power usage (50%)
        metrics = GPUMetrics(
            gpu_id=0,
            name="Test GPU",
            utilization=30,
            memory_used=4096,
            memory_total=8192,
            temperature=60,
            power_usage=100,
            power_limit=200,
            fan_speed=40,
            clock_sm=1500,
            clock_memory=7000,
            pcie_tx=5000,
            pcie_rx=3000,
            timestamp=time.time()
        )
        assert metrics.get_alert_level() == AlertLevel.NORMAL
        
        # Warning level power usage (90%)
        metrics.power_usage = 180  # 90% of 200
        assert metrics.get_alert_level() == AlertLevel.WARNING
        
        # Critical level power usage (98%)
        metrics.power_usage = 196  # 98% of 200
        assert metrics.get_alert_level() == AlertLevel.CRITICAL
        
        # At power limit (100%)
        metrics.power_usage = 200
        assert metrics.get_alert_level() == AlertLevel.CRITICAL

    def test_combined_alerts(self):
        """Test alert levels with multiple metrics triggering alerts"""
        # Multiple warnings (memory and temperature)
        metrics = GPUMetrics(
            gpu_id=0,
            name="Test GPU",
            utilization=50,
            memory_used=6144,  # 75% (WARNING)
            memory_total=8192,
            temperature=72,    # WARNING
            power_usage=100,   # Normal
            power_limit=200,
            fan_speed=40,
            clock_sm=1500,
            clock_memory=7000,
            pcie_tx=5000,
            pcie_rx=3000,
            timestamp=time.time()
        )
        assert metrics.get_alert_level() == AlertLevel.WARNING
        
        # Mix of warning and critical
        metrics.power_usage = 196  # 98% (CRITICAL)
        assert metrics.get_alert_level() == AlertLevel.CRITICAL
        
        # Mix of all alert levels
        metrics.memory_used = 7782  # 95% (EMERGENCY)
        metrics.temperature = 75    # WARNING
        metrics.power_usage = 196   # 98% (CRITICAL) 
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY
        
        # All metrics at emergency level
        metrics.memory_used = 7782  # 95% (EMERGENCY)
        metrics.temperature = 92    # EMERGENCY
        metrics.power_usage = 196   # 98% (CRITICAL)
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY 