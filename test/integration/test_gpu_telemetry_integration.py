import os
import sys
import time
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject

# Import required modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from dualgpuopt.services.telemetry import GPUMetrics, TelemetryWorker


# Mock QObject class for testing
class SignalRecorder(QObject):
    """Helper class to record signal emissions for testing."""

    def __init__(self):
        super().__init__()
        self.util_values = []
        self.vram_values = []
        self.temp_values = []
        self.power_values = []
        self.full_metrics = []

    def record_util(self, value):
        self.util_values.append(value)

    def record_vram(self, value):
        self.vram_values.append(value)

    def record_temp(self, value):
        self.temp_values.append(value)

    def record_power(self, value):
        self.power_values.append(value)

    def record_metrics(self, metrics):
        self.full_metrics.append(metrics)


class TestGPUTelemetryIntegration:
    """Integration tests for GPU telemetry and monitoring components."""

    @pytest.fixture()
    def signal_recorder(self):
        """Create a signal recorder for testing."""
        return SignalRecorder()

    @pytest.fixture()
    def mock_gpu_data(self):
        """Create mock GPU data for testing."""
        # Initial state
        return {
            0: {
                "util": 30,
                "memory_percent": 25.0,
                "memory_used": 2 * 1024,  # 2GB
                "memory_total": 8 * 1024,  # 8GB
                "temp": 65,
                "power_percent": 40.0,
                "power_w": 100,
                "power_limit": 250,
                "name": "NVIDIA Test GPU 1",
                "clock_sm": 1500,
                "clock_memory": 7000,
                "pcie_tx": 100 * 1024,  # 100 MB/s
                "pcie_rx": 50 * 1024,  # 50 MB/s
            },
            1: {
                "util": 40,
                "memory_percent": 16.7,
                "memory_used": 2 * 1024,  # 2GB
                "memory_total": 12 * 1024,  # 12GB
                "temp": 70,
                "power_percent": 50.0,
                "power_w": 150,
                "power_limit": 300,
                "name": "NVIDIA Test GPU 2",
                "clock_sm": 1600,
                "clock_memory": 7500,
                "pcie_tx": 150 * 1024,  # 150 MB/s
                "pcie_rx": 75 * 1024,  # 75 MB/s
            },
        }

    def test_telemetry_emits_signals(self, signal_recorder, mock_gpu_data):
        """Test that TelemetryWorker correctly emits signals with GPU metrics."""
        # Create telemetry worker with mocked GPU data
        telemetry_worker = TelemetryWorker(poll_interval=0.1)

        # Mock the _get_gpu_data method to return our test data
        telemetry_worker._get_gpu_data = MagicMock(return_value=mock_gpu_data)

        # Connect signals to the recorder
        telemetry_worker.util_updated.connect(signal_recorder.record_util)
        telemetry_worker.vram_updated.connect(signal_recorder.record_vram)
        telemetry_worker.temp_updated.connect(signal_recorder.record_temp)
        telemetry_worker.power_updated.connect(signal_recorder.record_power)
        telemetry_worker.metrics_updated.connect(signal_recorder.record_metrics)

        # Start telemetry worker
        telemetry_worker.start()

        # Wait for a few polling cycles
        time.sleep(0.3)

        # Stop telemetry worker
        telemetry_worker.stop()

        # Verify signals were emitted
        assert len(signal_recorder.util_values) >= 2
        assert len(signal_recorder.vram_values) >= 2
        assert len(signal_recorder.temp_values) >= 2
        assert len(signal_recorder.power_values) >= 2
        assert len(signal_recorder.full_metrics) >= 2

        # Verify signal values
        # Should be average of the two GPUs
        assert abs(signal_recorder.util_values[0] - 35.0) < 0.1  # (30 + 40) / 2
        assert abs(signal_recorder.vram_values[0] - 20.85) < 0.1  # (25.0 + 16.7) / 2
        assert abs(signal_recorder.temp_values[0] - 67.5) < 0.1  # (65 + 70) / 2
        assert abs(signal_recorder.power_values[0] - 45.0) < 0.1  # (40 + 50) / 2

        # Verify full metrics structure
        first_metrics = signal_recorder.full_metrics[0]
        assert isinstance(first_metrics, dict)
        assert len(first_metrics) == 2  # Two GPUs
        assert isinstance(first_metrics[0], GPUMetrics)
        assert isinstance(first_metrics[1], GPUMetrics)

        # Verify metrics values
        assert first_metrics[0].utilization == 30
        assert first_metrics[0].memory_percent == 25.0
        assert first_metrics[0].temperature == 65
        assert first_metrics[0].power_percent == 40.0

        assert first_metrics[1].utilization == 40
        assert first_metrics[1].memory_percent == 16.7
        assert first_metrics[1].temperature == 70
        assert first_metrics[1].power_percent == 50.0

    def test_telemetry_with_changing_gpu_state(self, signal_recorder):
        """Test system behavior when GPU state changes."""
        # Initial state
        initial_gpu_data = {
            0: {
                "util": 30,
                "memory_percent": 25.0,
                "temp": 65,
                "power_percent": 40.0,
            },
            1: {
                "util": 40,
                "memory_percent": 16.7,
                "temp": 70,
                "power_percent": 50.0,
            },
        }

        # Changed state
        changed_gpu_data = {
            0: {
                "util": 80,
                "memory_percent": 50.0,
                "temp": 75,
                "power_percent": 60.0,
            },
            1: {
                "util": 40,
                "memory_percent": 16.7,
                "temp": 70,
                "power_percent": 50.0,
            },
        }

        # Create telemetry worker
        telemetry_worker = TelemetryWorker(poll_interval=0.1)

        # Setup mock to return initial data first, then changed data
        side_effect_values = [
            initial_gpu_data,
            initial_gpu_data,
            changed_gpu_data,
            changed_gpu_data,
        ]
        telemetry_worker._get_gpu_data = MagicMock(side_effect=side_effect_values)

        # Connect signals to the recorder
        telemetry_worker.util_updated.connect(signal_recorder.record_util)
        telemetry_worker.vram_updated.connect(signal_recorder.record_vram)
        telemetry_worker.temp_updated.connect(signal_recorder.record_temp)
        telemetry_worker.power_updated.connect(signal_recorder.record_power)

        # Start telemetry worker
        telemetry_worker.start()

        # Wait for initial metrics
        time.sleep(0.25)

        # Wait for updated metrics
        time.sleep(0.25)

        # Stop telemetry worker
        telemetry_worker.stop()

        # Verify we have both initial and changed values
        assert len(signal_recorder.util_values) >= 2

        # Calculate expected values
        initial_util_avg = (initial_gpu_data[0]["util"] + initial_gpu_data[1]["util"]) / 2
        changed_util_avg = (changed_gpu_data[0]["util"] + changed_gpu_data[1]["util"]) / 2

        # Verify initial value
        assert abs(signal_recorder.util_values[0] - initial_util_avg) < 0.1

        # Verify changed value
        assert abs(signal_recorder.util_values[-1] - changed_util_avg) < 0.1

        # Verify the change was detected
        assert signal_recorder.util_values[0] < signal_recorder.util_values[-1]

    def test_engine_integration_with_telemetry(self):
        """Test integration between TelemetryWorker and Engine."""
        # When implementing the actual test:
        # 1. Import Engine
        # 2. Create instances of both TelemetryWorker and Engine
        # 3. Configure Engine with mock model data
        # 4. Start TelemetryWorker and verify it works with Engine

        # For now, use a simple placeholder test
        try:
            from dualgpuopt.engine.backend import Engine

            engine_imported = True
        except ImportError:
            engine_imported = False

        # Skip test if Engine isn't available yet
        if not engine_imported:
            pytest.skip("Engine not available for testing yet")
            return

        # Basic test with the engine
        mock_telemetry = TelemetryWorker(poll_interval=0.1, use_mock=True)
        engine = Engine()

        # Verify the engine can be initialized
        assert engine is not None

        # Verify telemetry worker can be started and stopped
        mock_telemetry.start()
        time.sleep(0.2)
        mock_telemetry.stop()
