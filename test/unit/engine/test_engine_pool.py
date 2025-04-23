"""
Unit tests for the EnginePool implementation.
Tests LRU caching, health checking, and model reloading.
"""

import unittest
from unittest.mock import MagicMock, call, patch

from dualgpuopt.engine.pool import EnginePool, _LRUPool, _ping_backend, _port_open


class TestLRUPool(unittest.TestCase):
    """Test the internal LRU cache implementation."""

    def test_lru_eviction(self):
        """Test that the LRU pool evicts the least recently used item when full."""
        # Mock unload to avoid actual engine operations
        with patch("dualgpuopt.engine.pool._executor") as mock_executor:
            # Create a pool with size 2
            pool = _LRUPool(2)

            # Create mock entries
            entry1 = MagicMock()
            entry2 = MagicMock()
            entry3 = MagicMock()

            # Add entries
            pool.put("model1", entry1)
            pool.put("model2", entry2)

            # Access model1 to make it most recently used
            pool.get("model1")

            # Add model3, should evict model2
            pool.put("model3", entry3)

            # Check that model2 was evicted
            self.assertIn("model1", pool._data)
            self.assertIn("model3", pool._data)
            self.assertNotIn("model2", pool._data)

            # Check that unload was called on the evicted engine
            mock_executor.submit.assert_called_once_with(entry2.engine.unload)


class TestEnginePool(unittest.TestCase):
    """Test the EnginePool class."""

    @patch("dualgpuopt.engine.pool._ping_backend")
    @patch("dualgpuopt.engine.pool._executor")
    @patch("dualgpuopt.engine.pool.Engine")
    def test_get_from_cache(self, mock_engine_class, mock_executor, mock_ping):
        """Test retrieving an engine from cache."""
        # Set up mocks
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_ping.return_value = True  # Engine is healthy

        # First call should create and load a new engine
        engine1 = EnginePool.get("model1", param1="value1")

        # Second call to the same model should return the cached engine
        engine2 = EnginePool.get("model1", param1="value1")

        # Check that we got the same engine instance
        self.assertEqual(engine1, engine2)

        # Check that engine was only created once
        mock_engine_class.assert_called_once()

        # Check that load was only called once
        self.assertEqual(
            mock_executor.submit.call_args_list[0],
            call(mock_engine.load, "model1", param1="value1"),
        )

    @patch("dualgpuopt.engine.pool.event_bus")
    @patch("dualgpuopt.engine.pool._ping_backend")
    @patch("dualgpuopt.engine.pool._executor")
    @patch("dualgpuopt.engine.pool.Engine")
    def test_unhealthy_engine_reload(
        self, mock_engine_class, mock_executor, mock_ping, mock_event_bus
    ):
        """Test that an unhealthy engine is reloaded."""
        # Set up mocks
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_ping.return_value = False  # Engine is unhealthy

        # First call should create and load a new engine
        EnginePool.get("model1", param1="value1")

        # Reset mock to check second call
        mock_executor.reset_mock()
        mock_engine_class.reset_mock()

        # Create a new mock engine for the second call
        mock_engine2 = MagicMock()
        mock_engine_class.return_value = mock_engine2

        # Second call should detect unhealthy engine and create a new one
        engine2 = EnginePool.get("model1", param1="value1")

        # Check that we got a new engine
        self.assertEqual(engine2, mock_engine2)

        # Check that engine.unload was called on the first engine
        mock_executor.submit.assert_any_call(mock_engine.unload)

        # Check that a new engine was created
        mock_engine_class.assert_called_once()

        # Check that load was called on the new engine
        mock_executor.submit.assert_any_call(mock_engine2.load, "model1", param1="value1")


class TestPortOpen(unittest.TestCase):
    """Test the _port_open helper function."""

    @patch("dualgpuopt.engine.pool.socket.socket")
    def test_port_open(self, mock_socket):
        """Test checking if a port is open."""
        # Set up mock socket
        mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 0

        # Test port open
        self.assertTrue(_port_open(8000))

        # Test port closed
        mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 1
        self.assertFalse(_port_open(8000))


class TestPingBackend(unittest.TestCase):
    """Test the _ping_backend helper function."""

    @patch("dualgpuopt.engine.pool._port_open")
    def test_ping_vllm_backend(self, mock_port_open):
        """Test pinging a vLLM backend."""
        # Set up mock engine
        mock_engine = MagicMock()
        mock_backend = MagicMock()
        mock_backend.__class__.__name__ = "VLLMBackend"
        mock_engine.backend = mock_backend

        # Test port open
        mock_port_open.return_value = True
        self.assertTrue(_ping_backend(mock_engine))
        mock_port_open.assert_called_with(8000)

        # Test port closed
        mock_port_open.return_value = False
        self.assertFalse(_ping_backend(mock_engine))

    @patch("dualgpuopt.engine.pool._port_open")
    def test_ping_llama_cpp_backend(self, mock_port_open):
        """Test pinging a LlamaCpp backend."""
        # Set up mock engine
        mock_engine = MagicMock()
        mock_backend = MagicMock()
        mock_backend.__class__.__name__ = "LlamaCppBackend"
        mock_engine.backend = mock_backend

        # Test port open
        mock_port_open.return_value = True
        self.assertTrue(_ping_backend(mock_engine))
        mock_port_open.assert_called_with(8080)

        # Test port closed
        mock_port_open.return_value = False
        self.assertFalse(_ping_backend(mock_engine))

    def test_ping_hf_backend(self):
        """Test pinging an HF backend which is always considered healthy if it exists."""
        # Set up mock engine
        mock_engine = MagicMock()
        mock_backend = MagicMock()
        mock_backend.__class__.__name__ = "HFBackend"
        mock_engine.backend = mock_backend

        # HF backend should always be considered healthy if it exists
        self.assertTrue(_ping_backend(mock_engine))

    def test_ping_no_backend(self):
        """Test pinging an engine with no backend."""
        # Set up mock engine
        mock_engine = MagicMock()
        mock_engine.backend = None

        # Should return False if no backend
        self.assertFalse(_ping_backend(mock_engine))


if __name__ == "__main__":
    unittest.main()
