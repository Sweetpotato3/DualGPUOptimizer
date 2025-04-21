#!/usr/bin/env python3
"""
Test core components of DualGPUOptimizer without UI dependencies
"""

import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CoreTester")

def test_gpu_modules():
    """Test GPU-related modules"""
    logger.info("Testing GPU modules...")

    # Test GpuMetrics import from gpu.common
    try:
        from dualgpuopt.gpu.common import GpuMetrics
        logger.info("✓ GpuMetrics class imported from gpu.common")

        # Create a test instance
        metrics = GpuMetrics(
            gpu_id=0,
            name="Test GPU",
            utilization=50,
            memory_used=4000,
            memory_total=8000,
            temperature=65,
            power_usage=150,
            power_limit=250,
            fan_speed=70,
            clock_sm=1500,
            clock_memory=7000,
            pcie_tx=100,
            pcie_rx=200,
            timestamp=time.time()
        )

        # Test the memory_percent property
        memory_percent = metrics.memory_percent
        logger.info(f"✓ Memory percent: {memory_percent:.1f}%")

    except Exception as e:
        logger.error(f"✗ Error with GpuMetrics: {e}")

    # Test GpuMonitor from gpu.monitor
    try:
        from dualgpuopt.gpu.monitor import GpuMonitor
        logger.info("✓ GpuMonitor class imported from gpu.monitor")

        # Create a monitor instance with mock mode
        monitor = GpuMonitor(mock_mode=True)
        logger.info(f"✓ Created GpuMonitor instance with mock_mode={monitor.mock_mode}")

    except Exception as e:
        logger.error(f"✗ Error with GpuMonitor: {e}")

def test_optimizer():
    """Test optimizer module"""
    logger.info("Testing optimizer module...")

    try:
        from dualgpuopt.optimizer import calculate_split_ratio
        logger.info("✓ calculate_split_ratio imported from optimizer")

        # Test with some values
        gpu_memory = [24000, 12000]  # 24GB and 12GB GPUs
        result = calculate_split_ratio(gpu_memory)
        logger.info(f"✓ Split ratio calculated: {result}")

    except Exception as e:
        logger.error(f"✗ Error with optimizer: {e}")

def test_telemetry():
    """Test telemetry module"""
    logger.info("Testing telemetry module...")

    try:
        from dualgpuopt.telemetry import TelemetryService
        logger.info("✓ TelemetryService imported from telemetry")

        # Create a telemetry service instance
        telemetry = TelemetryService(mock=True)
        logger.info("✓ Created TelemetryService instance with mock=True")

        # Start it briefly
        telemetry.start()
        logger.info("✓ Started telemetry service")

        # Wait a moment to collect some data
        time.sleep(1)

        # Get metrics
        metrics = telemetry.get_metrics()
        logger.info(f"✓ Got metrics for {len(metrics)} GPUs")

        # Stop telemetry
        telemetry.stop()
        logger.info("✓ Stopped telemetry service")

    except Exception as e:
        logger.error(f"✗ Error with telemetry: {e}")

def main():
    """Main test function"""
    logger.info("Starting core component tests")

    # Run the tests
    test_gpu_modules()
    test_optimizer()
    test_telemetry()

    logger.info("Core component testing complete")

if __name__ == "__main__":
    main()