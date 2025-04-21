import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

# Import required modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from dualgpuopt.services.event_bus import EventBus
from dualgpuopt.telemetry import TelemetryService


class TestGPUTelemetryIntegration:
    """Integration tests for GPU telemetry and monitoring components."""

    @pytest.fixture
    def event_bus(self):
        """Create a real event bus for testing."""
        return EventBus()

    @pytest.fixture
    def mock_gpu_provider(self):
        """Create a mock GPU provider that returns controlled test data."""
        provider = MagicMock()
        provider.get_gpu_count.return_value = 2

        gpu1 = MagicMock()
        gpu1.name = "NVIDIA Test GPU 1"
        gpu1.total_memory = 8 * 1024 * 1024 * 1024  # 8GB
        gpu1.available_memory = 6 * 1024 * 1024 * 1024  # 6GB
        gpu1.temperature = 65
        gpu1.utilization = 30
        gpu1.power_usage = 100
        gpu1.power_limit = 250
        gpu1.fan_speed = 40
        gpu1.clock_speed = 1500
        gpu1.memory_clock = 7000

        gpu2 = MagicMock()
        gpu2.name = "NVIDIA Test GPU 2"
        gpu2.total_memory = 12 * 1024 * 1024 * 1024  # 12GB
        gpu2.available_memory = 10 * 1024 * 1024 * 1024  # 10GB
        gpu2.temperature = 70
        gpu2.utilization = 40
        gpu2.power_usage = 150
        gpu2.power_limit = 300
        gpu2.fan_speed = 45
        gpu2.clock_speed = 1600
        gpu2.memory_clock = 7500

        provider.get_gpu_info.side_effect = lambda idx: [gpu1, gpu2][idx]
        provider.get_gpus.return_value = [gpu1, gpu2]
        return provider

    def test_telemetry_publishes_gpu_metrics_events(self, event_bus, mock_gpu_provider):
        """Test that telemetry service correctly publishes GPU metrics events."""
        # Create a monitor for received events
        received_events = []

        def event_collector(event):
            received_events.append(event)

        # Subscribe to GPU metrics events
        from dualgpuopt.services.events import GPUMetricsEvent

        event_bus.subscribe(GPUMetricsEvent, event_collector)

        # Create telemetry service with mocked GPU provider and use dependency injection for event bus
        telemetry = TelemetryService(gpu_provider=mock_gpu_provider, event_bus=event_bus)

        # Start telemetry with a short poll interval for testing
        telemetry.start(poll_interval=0.1)

        # Wait for a few polling cycles
        time.sleep(0.3)

        # Stop telemetry
        telemetry.stop()

        # Verify events were received
        assert len(received_events) >= 2  # Should have at least 2 events (3 polls * 0.1s each)

        # Verify event data structure
        first_event = received_events[0]
        assert isinstance(first_event, GPUMetricsEvent)
        assert "memory_used" in first_event.metrics
        assert "utilization" in first_event.metrics
        assert "temperature" in first_event.metrics

        # Verify metrics values match our mock values
        assert len(first_event.metrics["memory_used"]) == 2
        # Memory used = total - available
        expected_memory_used = [
            8 * 1024 * 1024 * 1024 - 6 * 1024 * 1024 * 1024,
            12 * 1024 * 1024 * 1024 - 10 * 1024 * 1024 * 1024,
        ]
        assert first_event.metrics["memory_used"] == expected_memory_used
        assert first_event.metrics["utilization"] == [30, 40]
        assert first_event.metrics["temperature"] == [65, 70]

    def test_gpu_monitor_responds_to_telemetry(self, event_bus, mock_gpu_provider):
        """Test that GPU monitor correctly responds to telemetry events."""
        # Create telemetry service with mocked GPU provider
        telemetry = TelemetryService(gpu_provider=mock_gpu_provider, event_bus=event_bus)

        # Create a test monitor class that uses the monitor module functions instead of GPUMonitor class
        class TestMonitor:
            def __init__(self, event_bus):
                self.event_bus = event_bus

            def check_temperature_alerts(self, metrics):
                # Test implementation
                temps = [m.temperature for m in metrics.values()]
                return any(t > 80 for t in temps)

            def check_memory_pressure(self, metrics):
                # Test implementation
                memory_usages = [m.memory_percent for m in metrics.values()]
                return any(m > 90 for m in memory_usages)

            def handle_metrics(self, metrics):
                # This will call both check methods
                self.check_temperature_alerts(metrics)
                self.check_memory_pressure(metrics)

        # Use the test monitor instead of GPUMonitor
        monitor = TestMonitor(event_bus=event_bus)

        # Register the monitor's handle_metrics method as a callback
        telemetry.register_callback(monitor.handle_metrics)

        # Track calls to the monitor's alert methods
        with patch.object(monitor, "check_temperature_alerts") as mock_temp_check:
            with patch.object(monitor, "check_memory_pressure") as mock_memory_check:
                # Start telemetry
                telemetry.start(poll_interval=0.1)

                # Wait for a few polling cycles
                time.sleep(0.3)

                # Stop telemetry
                telemetry.stop()

                # Verify monitor methods were called
                assert mock_temp_check.call_count >= 2
                assert mock_memory_check.call_count >= 2

    def test_integration_with_changing_gpu_state(self, event_bus, mock_gpu_provider):
        """Test system behavior when GPU state changes."""
        # Create telemetry service with mocked GPU provider
        telemetry = TelemetryService(gpu_provider=mock_gpu_provider, event_bus=event_bus)

        # Create a monitor for received events
        received_events = []

        def event_collector(event):
            received_events.append(event)

        # Subscribe to GPU metrics events
        from dualgpuopt.services.events import GPUMetricsEvent

        event_bus.subscribe(GPUMetricsEvent, event_collector)

        # Initial stable state
        gpus = mock_gpu_provider.get_gpus()

        # Start telemetry
        telemetry.start(poll_interval=0.1)

        # Wait for initial metrics
        time.sleep(0.2)

        # Change GPU state (simulate load increase)
        gpus[0].utilization = 80
        gpus[0].temperature = 75
        gpus[0].available_memory = 4 * 1024 * 1024 * 1024  # Reduced available memory

        # Wait for updated metrics
        time.sleep(0.2)

        # Stop telemetry
        telemetry.stop()

        # Verify we have at least 2 events (before and after change)
        assert len(received_events) >= 2

        # Find events before and after the change
        early_event = received_events[0]
        late_event = received_events[-1]

        # Verify initial state
        assert early_event.metrics["utilization"][0] == 30
        assert early_event.metrics["temperature"][0] == 65

        # Verify updated state was captured
        assert late_event.metrics["utilization"][0] == 80
        assert late_event.metrics["temperature"][0] == 75
        # Memory used should increase (available decreased)
        assert late_event.metrics["memory_used"][0] > early_event.metrics["memory_used"][0]
