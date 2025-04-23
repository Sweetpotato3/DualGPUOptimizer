#!/usr/bin/env python3
"""
Test script to verify the Engine integration with backend implementations.
"""
import sys
from typing import Iterator

try:
    from dualgpuopt.engine.backend import Engine, HFBackend, LlamaCppBackend, VLLMBackend
except ImportError:
    print("Error: Could not import engine modules. Make sure the path is correct.")
    sys.exit(1)


def test_engine_model_selection():
    """Test that the Engine properly selects backends based on model path"""
    print("\n=== Testing Engine Model Selection ===")

    engine = Engine()

    # Test llama.cpp backend selection
    models = [
        "/path/to/model.gguf",
        "/path/to/llama-7b-gguf/model",
        "/some/gguf/model.bin",
    ]

    for model_path in models:
        # Don't actually load model, just check backend selection
        engine.backend = None

        # Mock the load method for testing
        original_load = engine.load
        engine.load = lambda mp, **kwargs: setattr(engine, "backend", engine._select_backend(mp))

        engine.load(model_path)

        # Debug info
        print(f"Model path: {model_path}")
        print(f"Backend type: {type(engine.backend)}")

        if isinstance(engine.backend, LlamaCppBackend):
            print(f"✓ Correctly selected llama.cpp backend for {model_path}")
        else:
            print(f"✗ Failed to select llama.cpp backend for {model_path}")
            return False

        # Restore original method
        engine.load = original_load

    # Test vLLM backend selection
    models = [
        "/path/to/model-awq.safetensors",
        "/path/to/quantized-awq.bin",
        "/some/awq-model.bin",
    ]

    for model_path in models:
        # Don't actually load model, just check backend selection
        engine.backend = None

        # Mock the load method for testing
        original_load = engine.load
        engine.load = lambda mp, **kwargs: setattr(engine, "backend", engine._select_backend(mp))

        engine.load(model_path)

        # Debug info
        print(f"Model path: {model_path}")
        print(f"Backend type: {type(engine.backend)}")

        if isinstance(engine.backend, VLLMBackend):
            print(f"✓ Correctly selected vLLM backend for {model_path}")
        else:
            print(f"✗ Failed to select vLLM backend for {model_path}")
            return False

        # Restore original method
        engine.load = original_load

    # Test HF backend selection (default)
    models = [
        "/path/to/model/",
        "meta-llama/Llama-2-7b-hf",
        "/some/other/model.bin",
    ]

    for model_path in models:
        # Don't actually load model, just check backend selection
        engine.backend = None

        # Mock the load method for testing
        original_load = engine.load
        engine.load = lambda mp, **kwargs: setattr(engine, "backend", engine._select_backend(mp))

        engine.load(model_path)

        # Debug info
        print(f"Model path: {model_path}")
        print(f"Backend type: {type(engine.backend)}")

        if isinstance(engine.backend, HFBackend):
            print(f"✓ Correctly selected HF backend for {model_path}")
        else:
            print(f"✗ Failed to select HF backend for {model_path}")
            return False

        # Restore original method
        engine.load = original_load

    print("✓ Engine backend selection tests passed")
    return True


def test_mock_streaming():
    """Test the streaming interface with mock implementations"""
    print("\n=== Testing Engine Streaming Interface ===")

    # Create a mock backend class for testing
    class MockBackend:
        def load(self, model_path: str, **kwargs) -> None:
            pass

        def stream(self, prompt: str, **kwargs) -> Iterator[str]:
            yield "This "
            yield "is "
            yield "a "
            yield "test "
            yield "response."

        def unload(self) -> None:
            pass

    # Create engine with mock backend
    engine = Engine()
    engine.backend = MockBackend()

    # Test streaming
    prompt = "Hello, world!"
    response = ""

    print("Testing streaming response...")
    for token in engine.stream(prompt):
        response += token
        print(f"  Received token: '{token}'")

    if response == "This is a test response.":
        print(f"✓ Received correct streamed response: '{response}'")
    else:
        print(f"✗ Incorrect streamed response: '{response}'")
        return False

    print("✓ Engine streaming tests passed")
    return True


if __name__ == "__main__":
    print("Testing Engine Integration")
    print("=========================")

    try:
        success = test_engine_model_selection() and test_mock_streaming()

        if success:
            print("\n✓ All engine integration tests passed!")
            sys.exit(0)
        else:
            print("\n✗ Engine integration tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
