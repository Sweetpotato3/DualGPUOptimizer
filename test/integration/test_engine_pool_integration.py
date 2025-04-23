"""
Integration tests for the EnginePool.

These tests verify that the EnginePool works correctly with real Engine instances.
To avoid requiring actual models, tests run with mock backends.
"""

import logging
import time
import unittest
from unittest.mock import patch

from dualgpuopt.engine.backend import Engine
from dualgpuopt.engine.pool import CHECK_INT, MAX_FAIL, EnginePool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestEnginePool")


class MockBackend:
    """Mock backend for testing."""

    def __init__(self):
        self.loaded = False
        self.model_path = None
        self.port = None

    def load(self, model_path, **kwargs):
        """Simulate loading a model."""
        self.loaded = True
        self.model_path = model_path
        self.port = kwargs.get("port", 8000)
        logger.info(f"Loaded model {model_path} with kwargs {kwargs}")

    def stream(self, prompt, **kwargs):
        """Return a mock stream."""
        if not self.loaded:
            yield "ERROR: Model not loaded"
            return

        # Simple mock response
        yield "Mock response to: "
        yield prompt

    def unload(self):
        """Unload the model."""
        self.loaded = False
        logger.info(f"Unloaded model {self.model_path}")


class TestEnginePoolIntegration(unittest.TestCase):
    """Integration tests for EnginePool using mock backends."""

    def setUp(self):
        """Set up for each test."""
        # Patch select_backend to return our mock backend
        self.patcher = patch.object(Engine, "_select_backend", return_value=MockBackend())
        self.mock_select_backend = self.patcher.start()

        # Clear the EnginePool cache
        EnginePool._cache._data.clear()

    def tearDown(self):
        """Clean up after each test."""
        self.patcher.stop()

    def test_engine_reuse(self):
        """Test that engines are reused from the cache."""
        # Get first engine
        engine1 = EnginePool.get("model1", ctx_size=1024)

        # Get second engine for a different model
        engine2 = EnginePool.get("model2", ctx_size=2048)

        # Get first model again - should be reused
        engine3 = EnginePool.get("model1", ctx_size=1024)

        # Check that we have 2 engines total
        self.assertEqual(len(EnginePool._cache._data), 2)

        # Check that engine1 and engine3 are the same instance
        self.assertIs(engine1, engine3)

        # Check that engine2 is a different instance
        self.assertIsNot(engine1, engine2)

    def test_lru_eviction(self):
        """Test that least recently used engines are evicted when cache is full."""
        # Set cache size to 2 for testing
        original_size = EnginePool._cache._max
        EnginePool._cache._max = 2

        try:
            # Load 3 models - should evict first one
            EnginePool.get("model1", ctx_size=1024)
            EnginePool.get("model2", ctx_size=2048)
            EnginePool.get("model3", ctx_size=4096)

            # Check cache size
            self.assertEqual(len(EnginePool._cache._data), 2)

            # Check that model1 was evicted
            self.assertNotIn("model1", EnginePool._cache._data)
            self.assertIn("model2", EnginePool._cache._data)
            self.assertIn("model3", EnginePool._cache._data)

            # Access model2 to make it MRU
            EnginePool.get("model2", ctx_size=2048)

            # Add model4 - should evict model3
            EnginePool.get("model4", ctx_size=8192)

            # Check that model3 was evicted
            self.assertNotIn("model3", EnginePool._cache._data)
            self.assertIn("model2", EnginePool._cache._data)
            self.assertIn("model4", EnginePool._cache._data)
        finally:
            # Restore cache size
            EnginePool._cache._max = original_size

    def test_stream_from_cached_engine(self):
        """Test that streaming works with cached engines."""
        # Get an engine
        engine = EnginePool.get("test_model", ctx_size=2048)

        # Stream from the engine
        response = list(engine.stream("Hello, world!"))

        # Check response
        self.assertEqual(response, ["Mock response to: ", "Hello, world!"])

        # Get the same engine from cache
        cached_engine = EnginePool.get("test_model", ctx_size=2048)

        # Stream from cached engine
        response = list(cached_engine.stream("Hello again!"))

        # Check response
        self.assertEqual(response, ["Mock response to: ", "Hello again!"])

    @patch("dualgpuopt.engine.pool._ping_backend")
    def test_health_check_and_restart(self, mock_ping):
        """Test that unhealthy engines are restarted."""
        # Mock ping to initially return True, then False for MAX_FAIL times, then True again
        ping_values = [True] + [False] * MAX_FAIL + [True]
        mock_ping.side_effect = ping_values

        # Get an engine and ensure it's started the watchdog thread
        EnginePool.get("test_model", ctx_size=2048)
        self.assertTrue(EnginePool._watch_started)

        # Wait for health check cycle
        time.sleep(CHECK_INT * 1.5)

        # Check that ping was called multiple times
        self.assertGreaterEqual(mock_ping.call_count, 1)

        # Engine should have been restarted after MAX_FAIL failures
        mock_select_backend = Engine._select_backend
        self.assertGreaterEqual(mock_select_backend.call_count, 2)


if __name__ == "__main__":
    unittest.main()
