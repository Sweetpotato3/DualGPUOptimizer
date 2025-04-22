#!/usr/bin/env python3
"""
Test script for demonstrating EnginePool integration with chat functionality.
This script shows how the EnginePool enables instant switching between models.
"""

import logging
import time
from unittest.mock import patch

from dualgpuopt.engine.backend import Engine
from dualgpuopt.engine.pool import EnginePool


# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ChatIntegrationTest")


class SimpleChatBot:
    """Simple chat bot implementation to demonstrate EnginePool usage."""
    
    def __init__(self):
        self.current_model = None
        
    def load_model(self, model_path, **kwargs):
        """Load a model using EnginePool."""
        logger.info(f"Loading model: {model_path}")
        start = time.time()
        
        # Get engine from pool - will be cached if already loaded
        engine = EnginePool.get(model_path, **kwargs)
        
        elapsed = time.time() - start
        logger.info(f"Model loaded in {elapsed:.2f} seconds")
        
        self.current_model = model_path
        return engine
        
    def chat(self, engine, message):
        """Chat with the loaded model."""
        logger.info(f"User: {message}")
        
        # Stream response
        logger.info("Model is responding...")
        full_response = []
        for token in engine.stream(message):
            full_response.append(token)
            # In a real UI, we would render each token as it arrives
        
        response = ''.join(full_response)
        logger.info(f"Assistant: {response}")
        return response


class MockModel:
    """Mock model implementation for testing."""
    
    def __init__(self, name, response_prefix):
        self.name = name
        self.response_prefix = response_prefix
        self.load_time = 2.0  # Simulated load time in seconds
        
    def load(self, model_path, **kwargs):
        """Simulate loading a model."""
        logger.info(f"Loading {self.name}...")
        time.sleep(self.load_time)  # Simulate long loading time
        logger.info(f"{self.name} loaded successfully")
        
    def stream(self, prompt, **kwargs):
        """Stream a response with simulated token generation."""
        # Simulate token-by-token streaming
        response = f"{self.response_prefix} {prompt}"
        
        for word in response.split():
            yield word + " "
            time.sleep(0.1)  # Simulate token generation time
            
    def unload(self):
        """Unload the model."""
        logger.info(f"Unloading {self.name}")


def test_chat_integration():
    """Test the integration of EnginePool with chat functionality."""
    
    # Create mock models
    assistant_model = MockModel("Assistant Model", "I'm your helpful assistant, responding to:")
    code_model = MockModel("Code Model", "```python\n# Code response to:")
    
    # Dictionary mapping model paths to mock models
    mock_models = {
        "assistant": assistant_model,
        "code": code_model,
    }
    
    # Patch Engine._select_backend to return the appropriate mock model
    def mock_select_backend(model_path):
        return mock_models[model_path]
    
    with patch.object(Engine, '_select_backend', side_effect=mock_select_backend):
        # Create a simple chat bot
        chatbot = SimpleChatBot()
        
        # Initial loading of the assistant model (should be slow)
        logger.info("\n=== First load of assistant model ===")
        assistant_engine = chatbot.load_model("assistant", temperature=0.7)
        
        # Chat with the assistant model
        chatbot.chat(assistant_engine, "Hello, how are you?")
        
        # Switch to the code model (should be slow for first load)
        logger.info("\n=== First load of code model ===")
        code_engine = chatbot.load_model("code", temperature=0.2)
        
        # Chat with the code model
        chatbot.chat(code_engine, "Write a function to calculate fibonacci numbers")
        
        # Switch back to the assistant model (should be instant)
        logger.info("\n=== Second load of assistant model (should be instant) ===")
        assistant_engine2 = chatbot.load_model("assistant", temperature=0.7)
        
        # Verify it's the same instance
        logger.info(f"Same assistant engine instance: {assistant_engine is assistant_engine2}")
        
        # Chat with the assistant model again
        chatbot.chat(assistant_engine2, "Tell me about machine learning")
        
        # Switch back to the code model (should be instant)
        logger.info("\n=== Second load of code model (should be instant) ===")
        code_engine2 = chatbot.load_model("code", temperature=0.2)
        
        # Verify it's the same instance
        logger.info(f"Same code engine instance: {code_engine is code_engine2}")
        
        # Chat with the code model again
        chatbot.chat(code_engine2, "Write a bubble sort implementation")
        
        # Check the EnginePool cache
        logger.info(f"\nNumber of models in cache: {len(EnginePool._cache._data)}")
        logger.info(f"Cached models: {list(EnginePool._cache._data.keys())}")
        
        # Clean up
        logger.info("\nTest complete. Clearing EnginePool cache...")
        EnginePool._cache._data.clear()


if __name__ == "__main__":
    logger.info("Starting EnginePool chat integration test...")
    test_chat_integration()
    logger.info("Test completed.") 