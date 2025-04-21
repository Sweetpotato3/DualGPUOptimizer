"""
Unit tests for the telemetry module
"""
import os
import time
import pytest
from unittest.mock import MagicMock, patch
import threading

# Import the module under test - use a try/except to handle possible import errors
try:
    from dualgpuopt.telemetry import (
        GPUMetrics,
        TelemetryService,
        get_telemetry_service,
        reset_telemetry_service,
        ENV_POLL_INTERVAL,
        ENV_MOCK_TELEMETRY,
        ENV_MAX_RECOVERY_ATTEMPTS,
        AlertLevel
    )
    TELEMETRY_AVAILABLE = True
except ImportError:
    # Create a minimal mock for testing without the real module
    TELEMETRY_AVAILABLE = False

    # Mock class definitions for testing
    class AlertLevel:
        NORMAL = 0
        WARNING = 1
        CRITICAL = 2
        EMERGENCY = 3
        
    class GPUMetrics:
        def __init__(self, gpu_id=0, name="", utilization=0, memory_used=0, memory_total=0,
                    temperature=0, power_usage=0, power_limit=0, fan_speed=0, clock_sm=0,
                    clock_memory=0, pcie_tx=0, pcie_rx=0, timestamp=0, error_state=False):
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

        @property
        def formatted_memory(self):
            return f"{self.memory_used}/{self.memory_total} MB ({self.memory_percent:.1f}%)"

        @property
        def formatted_pcie(self):
            return f"TX: {self.pcie_tx/1024:.1f} MB/s, RX: {self.pcie_rx/1024:.1f} MB/s"
            
        def get_alert_level(self):
            # Mock implementation
            if self.memory_percent >= 95 or self.temperature >= 90:
                return AlertLevel.EMERGENCY
            elif self.memory_percent >= 90 or self.temperature >= 80:
                return AlertLevel.CRITICAL
            elif self.memory_percent >= 75 or self.temperature >= 70:
                return AlertLevel.WARNING
            return AlertLevel.NORMAL

    class TelemetryService:
        def __init__(self, poll_interval=1.0, use_mock=True):
            self.poll_interval = poll_interval
            self.force_mock = use_mock
            self.use_mock = True
            self.running = False
            self.metrics = {}
            self.callbacks = []
            self._thread = None
            self._stop_event = threading.Event()
            self._nvml_initialized = False
            self._metrics_history = {}
            self._history_length = 60

        def start(self):
            self.running = True

        def stop(self):
            self.running = False

        def register_callback(self, callback):
            self.callbacks.append(callback)

        def unregister_callback(self, callback):
            if callback in self.callbacks:
                self.callbacks.remove(callback)
                return True
            return False

        def get_metrics(self):
            return self.metrics.copy()
            
        def get_history(self, gpu_id=None, seconds=None):
            if gpu_id is not None:
                return []
            return {}

        def _get_mock_metrics(self, gpu_id, timestamp, error_state=False):
            return GPUMetrics(
                gpu_id=gpu_id,
                name=f"Mock GPU {gpu_id}",
                utilization=50,
                memory_used=4096,
                memory_total=8192,
                temperature=65,
                power_usage=180,
                power_limit=300,
                fan_speed=60,
                clock_sm=1500,
                clock_memory=8000,
                pcie_tx=5000,
                pcie_rx=3000,
                timestamp=timestamp,
                error_state=error_state
            )

    def get_telemetry_service():
        return TelemetryService()

    def reset_telemetry_service():
        return True

    ENV_POLL_INTERVAL = 1.0
    ENV_MOCK_TELEMETRY = False
    ENV_MAX_RECOVERY_ATTEMPTS = 3

# Skip all tests if the module is not available
pytestmark = pytest.mark.skipif(
    not TELEMETRY_AVAILABLE,
    reason="Telemetry module not available"
)

class TestGPUMetrics:
    """Test the GPUMetrics class"""

    def test_creation(self):
        """Test creating a GPUMetrics instance"""
        metrics = GPUMetrics(
            gpu_id=0,
            name="Test GPU",
            utilization=50,
            memory_used=4096,
            memory_total=8192,
            temperature=70,
            power_usage=150,
            power_limit=250,
            fan_speed=60,
            clock_sm=1500,
            clock_memory=8000,
            pcie_tx=5000,
            pcie_rx=3000,
            timestamp=time.time()
        )

        assert metrics.gpu_id == 0
        assert metrics.name == "Test GPU"
        assert metrics.utilization == 50
        assert metrics.memory_used == 4096
        assert metrics.memory_total == 8192
        assert metrics.temperature == 70
        assert metrics.power_usage == 150
        assert metrics.power_limit == 250
        assert metrics.fan_speed == 60
        assert metrics.clock_sm == 1500
        assert metrics.clock_memory == 8000
        assert metrics.pcie_tx == 5000
        assert metrics.pcie_rx == 3000
        assert isinstance(metrics.timestamp, float)
        assert metrics.error_state is False

    def test_properties(self):
        """Test the GPUMetrics properties"""
        metrics = GPUMetrics(
            gpu_id=0,
            name="Test GPU",
            utilization=50,
            memory_used=4096,
            memory_total=8192,
            temperature=70,
            power_usage=150,
            power_limit=250,
            fan_speed=60,
            clock_sm=1500,
            clock_memory=8000,
            pcie_tx=5000,
            pcie_rx=3000,
            timestamp=time.time()
        )

        # Test memory percentage
        assert metrics.memory_percent == 50.0

        # Test power percentage
        assert metrics.power_percent == 60.0

        # Test memory formatting
        assert metrics.formatted_memory == "4096/8192 MB (50.0%)"

        # Test PCIe formatting
        assert metrics.formatted_pcie == "TX: 4.9 MB/s, RX: 2.9 MB/s"

    def test_edge_cases(self):
        """Test edge cases for the GPUMetrics class"""
        # Test with zero memory total
        metrics = GPUMetrics(
            memory_used=100,
            memory_total=0
        )
        assert metrics.memory_percent == 0.0

        # Test with zero power limit
        metrics = GPUMetrics(
            power_usage=100,
            power_limit=0
        )
        assert metrics.power_percent == 0.0
        
    def test_alert_levels(self):
        """Test alert level calculation based on metrics"""
        # Normal state
        metrics = GPUMetrics(
            memory_used=4096,
            memory_total=8192,  # 50% memory
            temperature=60,
            power_usage=150,
            power_limit=250  # 60% power
        )
        assert metrics.get_alert_level() == AlertLevel.NORMAL
        
        # Warning level due to temperature
        metrics = GPUMetrics(
            memory_used=4096,
            memory_total=8192,  # 50% memory
            temperature=72,  # High temperature
            power_usage=150,
            power_limit=250  # 60% power
        )
        assert metrics.get_alert_level() == AlertLevel.WARNING
        
        # Warning level due to memory
        metrics = GPUMetrics(
            memory_used=6144,
            memory_total=8192,  # 75% memory
            temperature=60,
            power_usage=150,
            power_limit=250  # 60% power
        )
        assert metrics.get_alert_level() == AlertLevel.WARNING
        
        # Critical level due to temperature
        metrics = GPUMetrics(
            memory_used=4096,
            memory_total=8192,  # 50% memory
            temperature=85,  # Critical temperature
            power_usage=150,
            power_limit=250  # 60% power
        )
        assert metrics.get_alert_level() == AlertLevel.CRITICAL
        
        # Critical level due to memory
        metrics = GPUMetrics(
            memory_used=7373,
            memory_total=8192,  # 90% memory
            temperature=60,
            power_usage=150,
            power_limit=250  # 60% power
        )
        assert metrics.get_alert_level() == AlertLevel.CRITICAL
        
        # Emergency level due to temperature
        metrics = GPUMetrics(
            memory_used=4096,
            memory_total=8192,  # 50% memory
            temperature=92,  # Emergency temperature
            power_usage=150,
            power_limit=250  # 60% power
        )
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY
        
        # Emergency level due to memory
        metrics = GPUMetrics(
            memory_used=7782,
            memory_total=8192,  # 95% memory
            temperature=60,
            power_usage=150,
            power_limit=250  # 60% power
        )
        assert metrics.get_alert_level() == AlertLevel.EMERGENCY

class TestTelemetryService:
    """Test the TelemetryService class"""

    @pytest.fixture
    def mock_nvml(self):
        """Mock the pynvml module"""
        mock = MagicMock()
        mock.nvmlInit = MagicMock()
        mock.nvmlDeviceGetCount = MagicMock(return_value=2)
        mock.nvmlDeviceGetHandleByIndex = MagicMock()
        mock.nvmlDeviceGetName = MagicMock(return_value="Mock GPU")
        mock.nvmlDeviceGetUtilizationRates = MagicMock()
        mock.nvmlDeviceGetUtilizationRates.return_value.gpu = 50
        mock.nvmlDeviceGetMemoryInfo = MagicMock()
        mock.nvmlDeviceGetMemoryInfo.return_value.used = 4 * 1024 * 1024 * 1024  # 4GB
        mock.nvmlDeviceGetMemoryInfo.return_value.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock.nvmlDeviceGetTemperature = MagicMock(return_value=70)
        mock.nvmlDeviceGetPowerUsage = MagicMock(return_value=150000)  # 150W
        mock.nvmlDeviceGetPowerManagementLimit = MagicMock(return_value=250000)  # 250W
        mock.nvmlDeviceGetFanSpeed = MagicMock(return_value=60)
        mock.nvmlDeviceGetClockInfo = MagicMock(return_value=1500)
        mock.nvmlDeviceGetPcieThroughput = MagicMock(return_value=5000)

        # Add constants needed
        mock.NVML_TEMPERATURE_GPU = 0
        mock.NVML_CLOCK_SM = 0
        mock.NVML_CLOCK_MEM = 1
        mock.NVML_PCIE_UTIL_TX_BYTES = 0
        mock.NVML_PCIE_UTIL_RX_BYTES = 1

        return mock

    @pytest.fixture
    def telemetry_service(self):
        """Create a telemetry service for testing"""
        # Create service with higher poll interval for testing
        service = TelemetryService(poll_interval=0.01)
        yield service
        # Make sure to stop the service after each test
        service.stop()

    def test_creation(self):
        """Test creating a TelemetryService instance"""
        service = TelemetryService()

        assert service.poll_interval == ENV_POLL_INTERVAL
        assert service.force_mock == ENV_MOCK_TELEMETRY
        assert service.running is False
        assert service.metrics == {}
        assert service.callbacks == []
        assert service._thread is None
        assert service._nvml_initialized is False
        assert service._metrics_history == {}
        assert service._history_length == 60

    def test_custom_parameters(self):
        """Test creating a TelemetryService with custom parameters"""
        service = TelemetryService(poll_interval=2.5, use_mock=True)

        assert service.poll_interval == 2.5
        assert service.force_mock is True
        assert service.use_mock is True

    @patch('dualgpuopt.telemetry.NVML_AVAILABLE', True)
    def test_init_nvml(self, mock_nvml):
        """Test initializing NVML"""
        with patch('dualgpuopt.telemetry.pynvml', mock_nvml):
            service = TelemetryService(use_mock=False)

            # Check if NVML was initialized
            mock_nvml.nvmlInit.assert_called_once()
            assert service._nvml_initialized is True
            assert service.use_mock is False
            assert service.gpu_count == 2

    @patch('dualgpuopt.telemetry.NVML_AVAILABLE', True)
    def test_init_nvml_failure(self, mock_nvml):
        """Test handling NVML initialization failure"""
        mock_nvml.nvmlInit.side_effect = Exception("NVML init failed")

        with patch('dualgpuopt.telemetry.pynvml', mock_nvml):
            service = TelemetryService(use_mock=False)

            # Check if it falls back to mock mode
            assert service.use_mock is True
            assert service._nvml_initialized is False
            assert service.gpu_count == 2

    def test_start_stop(self, telemetry_service):
        """Test starting and stopping the telemetry service"""
        # Start the service
        telemetry_service.start()
        assert telemetry_service.running is True
        assert telemetry_service._thread is not None

        # Stop the service
        telemetry_service.stop()
        assert telemetry_service.running is False
        assert telemetry_service._stop_event.is_set() is True

    def test_register_callback(self, telemetry_service):
        """Test registering and unregistering callbacks"""
        callback = MagicMock()

        # Register callback
        telemetry_service.register_callback(callback)
        assert callback in telemetry_service.callbacks

        # Unregister callback
        result = telemetry_service.unregister_callback(callback)
        assert result is True
        assert callback not in telemetry_service.callbacks

        # Try to unregister a callback that isn't registered
        result = telemetry_service.unregister_callback(callback)
        assert result is False

    def test_mock_metrics(self, telemetry_service):
        """Test the mock metrics generation"""
        # Get mock metrics
        timestamp = time.time()
        metrics = telemetry_service._get_mock_metrics(0, timestamp)

        # Check the metrics
        assert isinstance(metrics, GPUMetrics)
        assert metrics.gpu_id == 0
        assert "Mock" in metrics.name
        assert metrics.timestamp == timestamp
        assert metrics.error_state is False

        # Try with error state
        metrics = telemetry_service._get_mock_metrics(1, timestamp, error_state=True)
        assert metrics.error_state is True

    @patch('dualgpuopt.telemetry.NVML_AVAILABLE', True)
    def test_get_gpu_metrics(self, mock_nvml, telemetry_service):
        """Test getting GPU metrics"""
        # Mock the telemetry service's NVML initialized state
        telemetry_service._nvml_initialized = True
        telemetry_service.use_mock = False

        with patch('dualgpuopt.telemetry.pynvml', mock_nvml):
            # Get real metrics
            timestamp = time.time()
            metrics = telemetry_service._get_gpu_metrics(0, timestamp)

            # Check the metrics
            assert isinstance(metrics, GPUMetrics)
            assert metrics.gpu_id == 0
            assert metrics.name == "Mock GPU"
            assert metrics.utilization == 50
            assert metrics.memory_used == 4096  # 4GB in MB
            assert metrics.memory_total == 8192  # 8GB in MB
            assert metrics.temperature == 70
            assert metrics.power_usage == 150.0
            assert metrics.power_limit == 250.0
            assert metrics.fan_speed == 60
            assert metrics.timestamp == timestamp
            assert metrics.error_state is False

    @patch('dualgpuopt.telemetry.NVML_AVAILABLE', True)
    def test_get_gpu_metrics_error(self, mock_nvml, telemetry_service):
        """Test getting GPU metrics with errors"""
        # Mock the telemetry service's NVML initialized state
        telemetry_service._nvml_initialized = True
        telemetry_service.use_mock = False

        # Make nvmlDeviceGetHandleByIndex raise an exception
        mock_nvml.nvmlDeviceGetHandleByIndex.side_effect = Exception("Device error")

        with patch('dualgpuopt.telemetry.pynvml', mock_nvml):
            # Get metrics, should fall back to mock
            timestamp = time.time()
            metrics = telemetry_service._get_gpu_metrics(0, timestamp)

            # Should be mock metrics with error state
            assert isinstance(metrics, GPUMetrics)
            assert metrics.error_state is True

    def test_history_storage(self, telemetry_service):
        """Test metrics history storage and retrieval"""
        # Create some test metrics
        metrics0 = telemetry_service._get_mock_metrics(0, time.time() - 30)
        metrics1 = telemetry_service._get_mock_metrics(1, time.time() - 20)
        metrics2 = telemetry_service._get_mock_metrics(0, time.time() - 10)
        
        # Manually add to history
        telemetry_service._metrics_history = {
            0: [metrics0, metrics2],
            1: [metrics1]
        }
        
        # Test getting all history
        all_history = telemetry_service.get_history()
        assert len(all_history) == 2  # Two GPUs
        assert len(all_history[0]) == 2  # Two entries for GPU 0
        assert len(all_history[1]) == 1  # One entry for GPU 1
        
        # Test getting history for specific GPU
        gpu0_history = telemetry_service.get_history(gpu_id=0)
        assert len(gpu0_history) == 2
        assert gpu0_history[0] == metrics0
        assert gpu0_history[1] == metrics2
        
        # Test getting history with time window
        recent_history = telemetry_service.get_history(seconds=15)
        assert 0 in recent_history
        assert 1 in recent_history
        assert len(recent_history[0]) == 1  # Only metrics2 is recent enough
        assert len(recent_history[1]) == 0  # metrics1 is too old
        
        # Test getting history for specific GPU with time window
        gpu0_recent = telemetry_service.get_history(gpu_id=0, seconds=15)
        assert len(gpu0_recent) == 1
        assert gpu0_recent[0] == metrics2
        
        # Test getting history for non-existent GPU
        nonexistent_history = telemetry_service.get_history(gpu_id=99)
        assert nonexistent_history == []
    
    def test_metrics_history_update(self, telemetry_service):
        """Test that metrics history is properly updated and trimmed"""
        # Mock _process_metrics_update to not actually call callbacks
        telemetry_service._process_metrics_update = MagicMock()
        
        # Set a smaller history length for testing
        telemetry_service._history_length = 3
        
        # Simulate telemetry loop updates
        for i in range(5):  # More than _history_length
            batch_metrics = {
                0: telemetry_service._get_mock_metrics(0, time.time() + i),
                1: telemetry_service._get_mock_metrics(1, time.time() + i)
            }
            
            # Update metrics and history
            with telemetry_service._metrics_lock:
                telemetry_service.metrics = batch_metrics
                
                # Update history (copied from _telemetry_loop)
                for gpu_id, metrics in batch_metrics.items():
                    if gpu_id not in telemetry_service._metrics_history:
                        telemetry_service._metrics_history[gpu_id] = []
                    telemetry_service._metrics_history[gpu_id].append(metrics)
                    
                    # Trim history if needed
                    if len(telemetry_service._metrics_history[gpu_id]) > telemetry_service._history_length:
                        # Keep only the last _history_length entries
                        telemetry_service._metrics_history[gpu_id] = telemetry_service._metrics_history[gpu_id][-telemetry_service._history_length:]
            
            # Call process_metrics_update
            telemetry_service._process_metrics_update(batch_metrics)
        
        # Verify history length is maintained
        assert len(telemetry_service._metrics_history[0]) == 3
        assert len(telemetry_service._metrics_history[1]) == 3
        
        # Verify we kept the most recent entries (timestamps should be the highest)
        timestamps0 = [m.timestamp for m in telemetry_service._metrics_history[0]]
        timestamps1 = [m.timestamp for m in telemetry_service._metrics_history[1]]
        
        assert sorted(timestamps0) == timestamps0  # Should be in chronological order
        assert sorted(timestamps1) == timestamps1
        
        # The earliest timestamp should be time.time() + 2 (entries 0, 1 were discarded)
        assert abs(timestamps0[0] - (time.time() + 2)) < 1.0

class TestTelemetryModule:
    """Test the telemetry module functions"""

    def test_get_telemetry_service(self):
        """Test getting the global telemetry service"""
        # Get the service
        service1 = get_telemetry_service()
        assert isinstance(service1, TelemetryService)

        # Getting it again should return the same instance
        service2 = get_telemetry_service()
        assert service1 is service2

    def test_reset_telemetry_service(self):
        """Test resetting the telemetry service"""
        # Get the service
        service = get_telemetry_service()

        # Reset it
        with patch.object(service, 'reset', return_value=True):
            result = reset_telemetry_service()
            assert result is True