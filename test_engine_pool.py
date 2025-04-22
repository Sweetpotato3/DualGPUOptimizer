#!/usr/bin/env python3
"""
Simple test script for the EnginePool functionality.
This script demonstrates how to use the EnginePool and verifies its caching behavior.
"""

import logging
import time
from unittest.mock import patch

from dualgpuopt.engine.backend import Engine
from dualgpuopt.engine.pool import EnginePool


# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("EnginePoolTest")


class MockBackend:
    """Mock backend for testing."""
    
    def __init__(self):
        self.loaded = False
        self.model_path = None
        
    def load(self, model_path, **kwargs):
        """Simulate loading a model."""
        time.sleep(1)  # Simulate loading time
        self.loaded = True
        self.model_path = model_path
        logger.info(f"Loaded model {model_path}")
        
    def stream(self, prompt, **kwargs):
        """Return a mock stream."""
        if not self.loaded:
            yield "ERROR: Model not loaded"
            return
            
        # Simple mock response
        yield f"Processing: '{prompt}'"
        yield f"Response from {self.model_path}"
        
    def unload(self):
        """Unload the model."""
        logger.info(f"Unloaded model {self.model_path}")
        self.loaded = False


def test_engine_pool():
    """Test the EnginePool functionality."""
    
    # Patch Engine._select_backend to return our mock backend
    with patch.object(Engine, '_select_backend', return_value=MockBackend()):
        # First load - should take time
        logger.info("Loading first model...")
        start = time.time()
        engine1 = EnginePool.get("model1", ctx_size=2048)
        elapsed1 = time.time() - start
        logger.info(f"First load took {elapsed1:.2f} seconds")
        
        # Stream from first engine
        logger.info("Streaming from first model...")
        response = list(engine1.stream("Hello world"))
        logger.info(f"Response: {response}")
        
        # Second load of same model - should be instant
        logger.info("Loading first model again (should be cached)...")
        start = time.time()
        engine2 = EnginePool.get("model1", ctx_size=2048)
        elapsed2 = time.time() - start
        logger.info(f"Second load took {elapsed2:.2f} seconds")
        
        # Should be the same instance
        logger.info(f"Same engine instance: {engine1 is engine2}")
        
        # Load a different model
        logger.info("Loading second model...")
        start = time.time()
        engine3 = EnginePool.get("model2", ctx_size=4096)
        elapsed3 = time.time() - start
        logger.info(f"Different model load took {elapsed3:.2f} seconds")
        
        # Stream from second engine
        logger.info("Streaming from second model...")
        response = list(engine3.stream("Different prompt"))
        logger.info(f"Response: {response}")
        
        # Should have 2 models in cache
        logger.info(f"Number of cached models: {len(EnginePool._cache._data)}")
        logger.info(f"Cached models: {list(EnginePool._cache._data.keys())}")
        
        # Load a third model (should evict first model if cache size is 2)
        logger.info("Loading third model (should evict first model)...")
        EnginePool.get("model3", ctx_size=8192)
        
        # Check what's in cache
        logger.info(f"Cached models after eviction: {list(EnginePool._cache._data.keys())}")
        
        # Try loading first model again - should be slow because it was evicted
        logger.info("Loading first model again (should have been evicted)...")
        start = time.time()
        EnginePool.get("model1", ctx_size=2048)
        elapsed5 = time.time() - start
        logger.info(f"Reloading evicted model took {elapsed5:.2f} seconds")


if __name__ == "__main__":
    logger.info("Starting EnginePool test...")
    test_engine_pool()
    logger.info("Test completed.") 