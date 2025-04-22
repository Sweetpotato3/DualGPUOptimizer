#!/usr/bin/env python3
"""
Simple test script to verify the telemetry history implementation.
"""
import time
import sys

try:
    from dualgpuopt.telemetry_history import HistoryBuffer
    from dualgpuopt.telemetry.sample import TelemetrySample
except ImportError:
    print("Error: Could not import telemetry modules. Make sure the path is correct.")
    sys.exit(1)


def test_basic_functionality():
    """Test basic history buffer functionality"""
    print("\n=== Testing Basic Functionality ===")
    
    # Create a history buffer
    hist = HistoryBuffer()
    
    # Push some values
    hist.push("test_metric", 10.0)
    hist.push("test_metric", 20.0)
    hist.push("test_metric", 30.0)
    
    # Get snapshot
    data = hist.snapshot("test_metric")
    
    # Verify data
    print(f"Snapshot length: {len(data)}")
    print("Values:", [value for _, value in data])
    
    assert len(data) == 3, f"Expected 3 items, got {len(data)}"
    assert [value for _, value in data] == [10.0, 20.0, 30.0], "Values don't match"
    
    print("✓ Basic functionality test passed")


def test_multiple_metrics():
    """Test multiple metrics in the same buffer"""
    print("\n=== Testing Multiple Metrics ===")
    
    hist = HistoryBuffer()
    
    # Push values for different metrics
    hist.push("cpu", 50.0)
    hist.push("memory", 60.0)
    hist.push("gpu", 70.0)
    
    # Get snapshots
    cpu_data = hist.snapshot("cpu")
    memory_data = hist.snapshot("memory")
    gpu_data = hist.snapshot("gpu")
    
    # Verify data
    print(f"CPU value: {cpu_data[0][1]}")
    print(f"Memory value: {memory_data[0][1]}")
    print(f"GPU value: {gpu_data[0][1]}")
    
    assert cpu_data[0][1] == 50.0, f"Expected CPU value 50.0, got {cpu_data[0][1]}"
    assert memory_data[0][1] == 60.0, f"Expected Memory value 60.0, got {memory_data[0][1]}"
    assert gpu_data[0][1] == 70.0, f"Expected GPU value 70.0, got {gpu_data[0][1]}"
    
    print("✓ Multiple metrics test passed")


def test_trimming():
    """Test that old data gets trimmed after the time limit"""
    print("\n=== Testing Trimming (Short Duration) ===")
    
    # Use a very short duration for testing
    import dualgpuopt.telemetry_history
    original_seconds = dualgpuopt.telemetry_history.SECONDS
    dualgpuopt.telemetry_history.SECONDS = 0.5  # 500ms for faster testing
    
    try:
        hist = HistoryBuffer()
        
        # Push initial value
        print("Pushing initial value...")
        hist.push("trim_test", 1.0)
        
        # Verify it's there
        assert len(hist.snapshot("trim_test")) == 1, "Initial value not in buffer"
        print("Initial value verified")
        
        # Wait longer than our trim duration
        print("Waiting for trim duration...")
        time.sleep(0.6)  # Wait slightly longer than SECONDS
        
        # Push a new value
        print("Pushing new value...")
        hist.push("trim_test", 2.0)
        
        # Get snapshot - should have trimmed the old value
        data = hist.snapshot("trim_test")
        print(f"Snapshot length: {len(data)}")
        print("Values:", [value for _, value in data])
        
        assert len(data) == 1, f"Expected 1 item after trimming, got {len(data)}"
        assert data[0][1] == 2.0, f"Expected value 2.0 after trimming, got {data[0][1]}"
        
        print("✓ Trimming test passed")
    finally:
        # Restore original duration
        dualgpuopt.telemetry_history.SECONDS = original_seconds


def test_telemetry_sample():
    """Test the TelemetrySample dataclass"""
    print("\n=== Testing TelemetrySample ===")
    
    hist = HistoryBuffer()
    
    # Push some values
    for i in range(5):
        hist.push("sample_test", i * 10.0)
    
    # Create a sample
    sample = TelemetrySample(
        name="sample_test",
        value=50.0,
        series=hist.snapshot("sample_test")
    )
    
    # Verify sample
    print(f"Sample name: {sample.name}")
    print(f"Sample value: {sample.value}")
    print(f"Sample series length: {len(sample.series)}")
    
    assert sample.name == "sample_test", f"Expected name 'sample_test', got '{sample.name}'"
    assert sample.value == 50.0, f"Expected value 50.0, got {sample.value}"
    assert len(sample.series) == 5, f"Expected 5 items in series, got {len(sample.series)}"
    
    print("✓ TelemetrySample test passed")


def test_threaded_access():
    """Test thread safety using concurrent pushes"""
    print("\n=== Testing Thread Safety ===")
    
    import threading
    
    hist = HistoryBuffer()
    push_count = 1000
    thread_count = 10
    
    def push_values(thread_id):
        for i in range(push_count):
            hist.push(f"thread_{thread_id}", i)
    
    # Create and start threads
    threads = []
    for i in range(thread_count):
        t = threading.Thread(target=push_values, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for threads to complete
    for t in threads:
        t.join()
    
    # Verify data
    success = True
    for i in range(thread_count):
        data = hist.snapshot(f"thread_{i}")
        if len(data) != push_count:
            print(f"Thread {i}: Expected {push_count} items, got {len(data)}")
            success = False
    
    if success:
        print(f"✓ Successfully handled {thread_count} threads with {push_count} pushes each")
    else:
        print("✗ Thread safety test failed")


if __name__ == "__main__":
    print("Testing Telemetry History Implementation")
    print("=======================================")
    
    try:
        test_basic_functionality()
        test_multiple_metrics()
        test_trimming()
        test_telemetry_sample()
        test_threaded_access()
        
        print("\n✓ All tests passed successfully!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1) 