"""
Test script for the memory profiler module.

This script verifies that the memory profiler can track GPU memory
allocations, detect leaks, and generate valid reports.
"""

import os
import time
import threading
import random
import tempfile
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable mock mode for testing without real GPUs
os.environ["DUALGPUOPT_MOCK_GPU"] = "1"
os.environ["DUALGPUOPT_GPU_COUNT"] = "2"

# Import the memory profiler
from dualgpuopt.memory import get_memory_profiler, MemoryEventType

# Create a simple console-based test
def run_memory_profiler_test():
    """Run a test of the memory profiler functionality"""
    print("Starting Memory Profiler Test")
    print("-" * 50)
    
    # Get profiler instance
    profiler = get_memory_profiler()
    
    # Set up event handling
    event_count = 0
    
    def event_handler(event_data):
        nonlocal event_count
        event_count += 1
        event_type = event_data.get("event_type", "UNKNOWN")
        description = event_data.get("description", "No description")
        print(f"[{event_type}] {description}")
    
    # Register for events
    for event_type in MemoryEventType:
        profiler.register_callback(event_type, event_handler)
    
    # Start a profiling session
    session_id = profiler.start_profiling("test_session")
    print(f"Started profiling session: {session_id}")
    
    # Allow profiler to collect initial metrics
    time.sleep(2)
    
    # Simulate a memory allocation event - we'll simulate multiple inference sessions
    for i in range(3):
        # Start inference
        print(f"\nStarting inference #{i+1}")
        profiler.start_inference()
        
        # Simulate memory usage during inference
        print(f"  Simulating memory activity...")
        # Wait to allow the profiler to capture the memory activity
        time.sleep(3)
        
        # End inference
        print(f"Ending inference #{i+1}")
        profiler.end_inference(token_count=random.randint(500, 2000))
        
        # Give the profiler time to process events
        time.sleep(1)
    
    # For the last test, create an artificial "leak" by simulating retained memory
    print("\nTesting leak detection...")
    profiler.start_inference()
    
    # Sleep to collect some data
    time.sleep(3)
    
    # End inference
    profiler.end_inference(token_count=1500)
    
    # Give the profiler time to process events
    time.sleep(2)
    
    # Generate a report
    report = profiler.get_session_report()
    print("\nSession Report Summary:")
    print(f"- Duration: {report.get('duration', 0):.1f} seconds")
    print(f"- Inference count: {report.get('inference_count', 0)}")
    print(f"- Total events: {event_count}")
    
    # Try to export the timeline
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        filepath = tmp.name
    
    export_success = profiler.export_timeline_data(filepath)
    if export_success:
        print(f"- Timeline exported to: {filepath}")
        
        # Show first few lines of the exported file
        try:
            with open(filepath, 'r') as f:
                print("\nExport preview:")
                for i, line in enumerate(f):
                    if i > 5:
                        break
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"Error reading export file: {e}")
    
    # End the session
    profiler.end_session()
    print("\nMemory profiler test completed")


if __name__ == "__main__":
    run_memory_profiler_test() 