#!/usr/bin/env python3
"""
Test script for the health monitoring and auto-restart feature of the EnginePool.
This script demonstrates how the EnginePool automatically restarts unhealthy backends.
"""

import logging
import time
from unittest.mock import patch

from dualgpuopt.engine.backend import Engine
from dualgpuopt.engine.pool import CHECK_INT, MAX_FAIL, EnginePool

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("HealthMonitorTest")


class FailingBackend:
    """A backend that fails after a certain number of pings."""

    def __init__(self):
        self.loaded = False
        self.model_path = None
        self.fail_after = 4  # Fail after 4 successful pings
        self.ping_count = 0
        self.healthy = True

    def load(self, model_path, **kwargs):
        """Simulate loading a model."""
        time.sleep(0.5)  # Simulate loading time
        self.loaded = True
        self.model_path = model_path
        self.healthy = True
        self.ping_count = 0
        logger.info(f"Loaded model {model_path}")

    def stream(self, prompt, **kwargs):
        """Return a mock stream."""
        if not self.loaded or not self.healthy:
            yield "ERROR: Model not loaded or unhealthy"
            return

        # Simple mock response
        yield f"Processing: '{prompt}'"
        yield f"Response from {self.model_path}"

    def unload(self):
        """Unload the model."""
        logger.info(f"Unloaded model {self.model_path}")
        self.loaded = False

    def is_healthy(self):
        """Simulate health check ping."""
        self.ping_count += 1
        logger.info(f"Health check #{self.ping_count} for {self.model_path}")

        if self.ping_count >= self.fail_after:
            self.healthy = False
            logger.warning(f"Backend for {self.model_path} is now unhealthy!")

        return self.healthy


def test_health_monitoring():
    """Test the health monitoring and auto-restart functionality."""
    # Create our failing backend
    failing_backend = FailingBackend()

    # Patch Engine._select_backend to return our failing backend
    with patch.object(Engine, "_select_backend", return_value=failing_backend):
        # Patch the _ping_backend function to use our backend's is_healthy method
        with patch(
            "dualgpuopt.engine.pool._ping_backend",
            side_effect=lambda e: failing_backend.is_healthy(),
        ):
            # Load the model
            logger.info("Loading model...")
            engine = EnginePool.get("test_model", ctx_size=2048)

            # Check initial health
            logger.info("Initial health check: %s", failing_backend.is_healthy())

            # Stream some data
            logger.info("Streaming initial data...")
            response = list(engine.stream("Initial prompt"))
            logger.info(f"Initial response: {response}")

            # Monitor engine health
            logger.info(
                f"Monitoring engine health for {MAX_FAIL+3} health checks (check interval: {CHECK_INT}s)..."
            )
            logger.info(f"Backend will fail after {failing_backend.fail_after} health checks")
            logger.info(f"EnginePool will restart after {MAX_FAIL} consecutive failures")

            # Wait for more health checks than fail_after
            total_wait = CHECK_INT * (MAX_FAIL + 3)
            logger.info(f"Waiting {total_wait:.1f} seconds for health checks and restart...")

            # Wait for the backend to fail and then be restarted
            time.sleep(total_wait)

            # Check if engine was restarted (ping count should be reset)
            logger.info(f"Current ping count: {failing_backend.ping_count}")

            # Try streaming again after potential restart
            logger.info("Streaming after monitoring period...")
            response = list(engine.stream("After monitoring prompt"))
            logger.info(f"Final response: {response}")

            # Clean up
            logger.info("Test complete. Clearing EnginePool cache...")
            EnginePool._cache._data.clear()


if __name__ == "__main__":
    logger.info("Starting EnginePool health monitoring test...")
    test_health_monitoring()
    logger.info("Test completed.")
