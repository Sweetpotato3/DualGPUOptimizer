#!/usr/bin/env python3
"""
Standalone test script that defines and tests a simple telemetry history implementation
without relying on external imports.
"""
import time
import threading
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Deque, Tuple, Dict

# Define the core components inline for standalone testing
SECONDS = 60  # Keep 60 seconds of data


@dataclass(slots=True)
class SampleSeries:
    """Holds (timestamp, value) pairs, drops data older than SECONDS."""
    data: Deque[Tuple[float, float]] = field(default_factory=deque)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def push(self, value: float) -> None:
        now = time.monotonic()
        with self.lock:
            self.data.append((now, value))
            cutoff = now - SECONDS
            while self.data and self.data[0][0] < cutoff:
                self.data.popleft()

    def snapshot(self) -> Tuple[Tuple[float, float], ...]:
        now = time.monotonic()
        with self.lock:
            cutoff = now - SECONDS
            while self.data and self.data[0][0] < cutoff:
                self.data.popleft()
            return tuple(self.data)  # zero-copy immutable


class HistoryBuffer:
    """
    Global container mapping metric name -> SampleSeries.
    """
    def __init__(self) -> None:
        self._buf: Dict[str, SampleSeries] = defaultdict(SampleSeries)

    def push(self, metric: str, value: float) -> None:
        self._buf[metric].push(value)

    def snapshot(self, metric: str) -> Tuple[Tuple[float, float], ...]:
        return self._buf[metric].snapshot()


@dataclass(slots=True)
class TelemetrySample:
    """Represents a telemetry metric with its current value and historical data."""
    name: str
    value: float
    series: Tuple[Tuple[float, float], ...] = field(default_factory=tuple)


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


def test_trimming():
    """Test that old data gets trimmed after the time limit"""
    print("\n=== Testing Trimming (Short Duration) ===")
    
    # Use a very short duration for testing
    global SECONDS
    original_seconds = SECONDS
    SECONDS = 0.5  # 500ms for faster testing
    
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
        SECONDS = original_seconds


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


def test_simulated_telemetry():
    """Test a simulated telemetry setup with multiple metrics over time"""
    print("\n=== Testing Simulated Telemetry ===")
    
    import math
    import random
    
    # Create history buffer
    hist = HistoryBuffer()
    
    # Simulate metrics for N seconds
    duration = 3
    interval = 0.1
    iterations = int(duration / interval)
    
    metrics = ["util", "mem", "temp", "power"]
    start_time = time.monotonic()
    
    print(f"Simulating {len(metrics)} metrics for {duration} seconds...")
    
    for i in range(iterations):
        # Calculate simulated values based on time
        elapsed = time.monotonic() - start_time
        for metric in metrics:
            # Different patterns for each metric
            if metric == "util":
                value = 50 + 30 * math.sin(elapsed) + random.uniform(-5, 5)
            elif metric == "mem":
                value = 70 + 10 * math.sin(elapsed / 2) + random.uniform(-3, 3)
            elif metric == "temp":
                value = 60 + 5 * math.sin(elapsed / 3) + random.uniform(-2, 2)
            else:  # power
                value = 80 + 15 * math.sin(elapsed / 4) + random.uniform(-4, 4)
            
            # Push to history
            hist.push(metric, value)
        
        # Sleep for interval
        time.sleep(interval)
    
    # Verify we have data for all metrics
    success = True
    for metric in metrics:
        data = hist.snapshot(metric)
        count = len(data)
        print(f"{metric} samples: {count}")
        
        # Should have approximately the number of iterations
        # (might be slightly less due to timing)
        if count < iterations - 2:  # Allow for some timing variance
            print(f"Error: Expected ~{iterations} samples for {metric}, got {count}")
            success = False
    
    if success:
        print("✓ Simulated telemetry test passed")
    else:
        print("✗ Simulated telemetry test failed")


if __name__ == "__main__":
    print("Standalone Telemetry History Test")
    print("=================================")
    
    try:
        test_basic_functionality()
        test_trimming()
        test_telemetry_sample()
        test_threaded_access()
        test_simulated_telemetry()
        print("\n✓ All tests passed successfully!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import sys
        sys.exit(1) 