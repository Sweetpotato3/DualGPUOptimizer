#!/usr/bin/env python3
"""
Test script to verify integration of the telemetry history with the telemetry service.
This uses mock GPU data to test the integration.
"""
import sys
import time
from typing import Dict

try:
    import importlib.util

    from dualgpuopt.telemetry import GPUMetrics, get_telemetry_service, hist

    # Check if TelemetrySample is available without importing it
    if importlib.util.find_spec("dualgpuopt.telemetry.sample"):
        pass  # Module exists but we don't need to import it
except ImportError:
    print("Error: Could not import telemetry modules. Make sure the path is correct.")
    sys.exit(1)

# Flag to indicate callback was called
callback_received = False
# Storage for received metrics
latest_metrics = {}


def test_telemetry_service_with_history():
    """Test integration of history buffer with telemetry service"""
    print("\n=== Testing Telemetry Service Integration ===")

    # Initialize telemetry service with mock data
    telemetry = get_telemetry_service()
    telemetry.use_mock = True

    # Define callback to receive metrics
    def metrics_callback(metrics: Dict[int, GPUMetrics]):
        global callback_received, latest_metrics
        callback_received = True
        latest_metrics = metrics
        print(f"Received metrics for {len(metrics)} GPUs")

        # Print basic info for each GPU
        for gpu_id, gpu_metrics in metrics.items():
            print(
                f"GPU {gpu_id}: Util={gpu_metrics.utilization}%, "
                f"Memory={gpu_metrics.memory_percent:.1f}%, "
                f"Temp={gpu_metrics.temperature}°C",
            )

    # Register callback
    telemetry.register_callback(metrics_callback)

    # Start telemetry service
    print("Starting telemetry service...")
    telemetry.start(poll_interval=0.5)  # Fast polling for testing

    # Wait for first metrics
    wait_time = 0
    while not callback_received and wait_time < 5:
        time.sleep(0.1)
        wait_time += 0.1

    if not callback_received:
        print("Error: Did not receive metrics callback")
        telemetry.stop()
        return False

    # Wait for multiple metrics to be collected
    print("Collecting metrics for 3 seconds...")
    time.sleep(3)

    # Check that histories are populated
    metrics_to_check = ["util", "vram", "temp"]

    success = True
    for metric in metrics_to_check:
        history = hist.snapshot(metric)
        print(f"{metric} history length: {len(history)}")
        if len(history) < 3:  # Should have at least 3 samples after 3 seconds
            print(f"Error: Expected at least 3 samples for {metric}, got {len(history)}")
            success = False

    # Also check per-GPU metrics
    for gpu_id in latest_metrics:
        for metric in ["util", "vram", "temp", "power"]:
            per_gpu_metric = f"{metric}_{gpu_id}"
            history = hist.snapshot(per_gpu_metric)
            print(f"{per_gpu_metric} history length: {len(history)}")
            if len(history) < 3:
                print(
                    f"Error: Expected at least 3 samples for {per_gpu_metric}, got {len(history)}",
                )
                success = False

    # Stop telemetry service
    telemetry.stop()
    print("Telemetry service stopped")

    if success:
        print("✓ Telemetry history integration test passed")
    else:
        print("✗ Telemetry history integration test failed")

    return success


if __name__ == "__main__":
    print("Testing Telemetry History Integration")
    print("====================================")

    try:
        if test_telemetry_service_with_history():
            print("\n✓ All integration tests passed!")
            sys.exit(0)
        else:
            print("\n✗ Integration tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
