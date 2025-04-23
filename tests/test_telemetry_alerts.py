"""
Unit tests for the telemetry alert system
"""

import time
from enum import Enum

import pytest

try:
    from dualgpuopt.telemetry import AlertLevel, GPUMetrics, TelemetryService

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

    class AlertLevel(Enum):
        NORMAL = 0
        WARNING = 1
        CRITICAL = 2
        EMERGENCY = 3

    class GPUMetrics:
        def __init__(
            self,
            gpu_id=0,
            name="",
            utilization=0,
            memory_used=0,
            memory_total=0,
            temperature=0,
            power_usage=0,
            power_limit=0,
            fan_speed=0,
            clock_sm=0,
            clock_memory=0,
            pcie_tx=0,
            pcie_rx=0,
            timestamp=0,
            error_state=False,
        ):
            self.gpu_id = gpu_id
            self.name = name
            self.utilization = utilization
            self.memory_used = memory_used
            self.memory_total = memory_total
            self.temperature = temperature
            self.power_usage = power_usage
            self.power_limit = power_limit
            self.fan_speed = fan_speed
            self.clock_sm = clock_sm
            self.clock_memory = clock_memory
            self.pcie_tx = pcie_tx
            self.pcie_rx = pcie_rx
            self.timestamp = timestamp
            self.error_state = error_state

        @property
        def memory_percent(self):
            if self.memory_total == 0:
                return 0.0
            return (self.memory_used / self.memory_total) * 100.0

        @property
        def power_percent(self):
            if self.power_limit == 0:
                return 0.0
            return (self.power_usage / self.power_limit) * 100.0

        def get_alert_level(self):
            # Match the actual implementation in dualgpuopt/telemetry.py
            # Start with NORMAL alert level
            level = AlertLevel.NORMAL

            # Memory usage thresholds
            if self.memory_percent >= 95:
                level = AlertLevel.EMERGENCY
            elif self.memory_percent >= 90:
                level = AlertLevel.CRITICAL if level.value < AlertLevel.CRITICAL.value else level
            elif self.memory_percent >= 75:
                level = AlertLevel.WARNING if level.value < AlertLevel.WARNING.value else level

            # Temperature thresholds
            if self.temperature >= 90:
                level = AlertLevel.EMERGENCY
            elif self.temperature >= 80:
                level = AlertLevel.CRITICAL if level.value < AlertLevel.CRITICAL.value else level
            elif self.temperature >= 70:
                level = AlertLevel.WARNING if level.value < AlertLevel.WARNING.value else level

            # Power usage thresholds (percentage of limit)
            if self.power_percent >= 98:
                level = AlertLevel.CRITICAL if level.value < AlertLevel.CRITICAL.value else level
            elif self.power_percent >= 90:
                level = AlertLevel.WARNING if level.value < AlertLevel.WARNING.value else level

            return level

    class TelemetryService:
        pass


# Skip all tests if the module is not available
pytestmark = pytest.mark.skipif(not TELEMETRY_AVAILABLE, reason="Telemetry module not available")


class TestAlertLevels:
    """Test the AlertLevel functionality"""

    def test_alert_level_enum(self):
        """Test that AlertLevel enum is properly defined"""
        assert AlertLevel.NORMAL.value == 0
        assert AlertLevel.WARNING.value == 1
        assert AlertLevel.CRITICAL.value == 2
        assert AlertLevel.EMERGENCY.value == 3

        # Verify order for comparison operators using values directly
        assert AlertLevel.NORMAL.value < AlertLevel.WARNING.value
        assert AlertLevel.WARNING.value < AlertLevel.CRITICAL.value
        assert AlertLevel.CRITICAL.value < AlertLevel.EMERGENCY.value

        # Test max() operation for alert levels
        # Max via explicit comparison
        alert1 = AlertLevel.NORMAL
        alert2 = AlertLevel.WARNING
        max_alert = AlertLevel.WARNING if alert1.value < alert2.value else alert1
        assert max_alert == AlertLevel.WARNING

        # Another max test
        alert1 = AlertLevel.CRITICAL
        alert2 = AlertLevel.WARNING
        max_alert = AlertLevel.CRITICAL if alert1.value > alert2.value else alert2
        assert max_alert == AlertLevel.CRITICAL

        # One more max test
        alert1 = AlertLevel.EMERGENCY
        alert2 = AlertLevel.CRITICAL
        max_alert = AlertLevel.EMERGENCY if alert1.value > alert2.value else alert2
        assert max_alert == AlertLevel.EMERGENCY

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
            timestamp=time.time(),
        )
        assert metrics.get_alert_level() == AlertLevel.NORMAL

        # Warning level memory usage (75%)
        metrics.memory_used = 6144  # 75% of 8192
        assert metrics.get_alert_level() == AlertLevel.WARNING

        # Critical level memory usage (90%)
        metrics.memory_used = 7373  # 90% of 8192
        assert metrics.get_alert_level() == AlertLevel.CRITICAL

        # Emergency level memory usage (95%)
        metrics.memory_used = 7800  # ~95.2% of 8192 - must be at least 95%
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
            timestamp=time.time(),
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
            timestamp=time.time(),
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
            temperature=72,  # WARNING
            power_usage=100,  # Normal
            power_limit=200,
            fan_speed=40,
            clock_sm=1500,
            clock_memory=7000,
            pcie_tx=5000,
            pcie_rx=3000,
            timestamp=time.time(),
        )
        assert metrics.get_alert_level() == AlertLevel.WARNING

        # Mix of warning and critical
        metrics.power_usage = 196  # 98% (CRITICAL)
        assert metrics.get_alert_level() == AlertLevel.CRITICAL

        # Mix of all alert levels
        metrics.memory_used = 7800  # 95.2% (EMERGENCY)
        metrics.temperature = 75  # WARNING
        metrics.power_usage = 196  # 98% (CRITICAL)
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY

        # All metrics at emergency level
        metrics.memory_used = 7800  # 95.2% (EMERGENCY)
        metrics.temperature = 92  # EMERGENCY
        metrics.power_usage = 196  # 98% (CRITICAL)
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY
