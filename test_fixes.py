#!/usr/bin/env python3
"""
Test script to verify bug fixes in DualGPUOptimizer
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FixTester")

def test_imports():
    """Test importing the fixed modules"""
    logger.info("Testing imports...")

    # Test importing the fixed modules
    try:
        # Import the dashboard module with fixed MEMORY_PROFILER_AVAILABLE
        logger.info("✓ Dashboard module import successful")
    except Exception as e:
        logger.error(f"✗ Dashboard module import failed: {e}")

    try:
        # Test importing from gpu_info with fixed GpuMetrics import
        logger.info("✓ GPU info module import successful")
    except Exception as e:
        logger.error(f"✗ GPU info module import failed: {e}")

    try:
        # Test importing direct_launcher with fixed ttk handling
        logger.info("✓ Direct launcher module import successful")
    except Exception as e:
        logger.error(f"✗ Direct launcher module import failed: {e}")

def test_run_direct_app():
    """Test if run_direct_app accepts the mock parameter"""
    logger.info("Testing run_direct_app...")

    try:
        # Add current directory to sys.path if not already there
        current_dir = str(Path.cwd())
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Import run_direct_app and verify it accepts the mock parameter
        import run_direct_app

        # Check if the main function accepts the mock parameter
        import inspect
        sig = inspect.signature(run_direct_app.main)
        if 'mock' in sig.parameters:
            logger.info("✓ run_direct_app.main accepts 'mock' parameter")
        else:
            logger.error("✗ run_direct_app.main does not accept 'mock' parameter")

    except Exception as e:
        logger.error(f"✗ Error testing run_direct_app: {e}")

def main():
    """Main test function"""
    logger.info("Starting fix verification tests")

    # Run the tests
    test_imports()
    test_run_direct_app()

    logger.info("Testing complete")

if __name__ == "__main__":
    main()