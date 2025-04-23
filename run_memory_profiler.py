#!/usr/bin/env python
"""
Run the memory profiler as a standalone application.

This script launches the memory profiler interface for GPU memory analysis.
"""

import argparse
import os
import sys


def main():
    """Main entry point for running the memory profiler"""
    parser = argparse.ArgumentParser(description="Memory Profiler for GPU memory usage")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without real GPUs")
    args = parser.parse_args()

    if args.mock:
        os.environ["DUALGPUOPT_MOCK_GPU"] = "1"
        os.environ["DUALGPUOPT_GPU_COUNT"] = "2"
        print("Running in mock mode with 2 simulated GPUs")

    # Run the memory profiler module
    try:
        import dualgpuopt.memory.__main__

        dualgpuopt.memory.__main__.main()
    except ImportError as e:
        print(f"Error importing memory profiler: {e}")
        print("Make sure dualgpuopt package is installed or in the Python path")
        return 1
    except Exception as e:
        print(f"Error running memory profiler: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
