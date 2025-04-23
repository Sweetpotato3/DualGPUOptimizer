#!/usr/bin/env python3
"""
Test script for demonstrating benchmark recording and performance tracking.
Records model performance metrics and displays the fastest models.
"""

import logging
import random
import time
from unittest.mock import patch

from dualgpuopt.engine.backend import Engine
from dualgpuopt.engine.benchmark import benchmark_db, get_fastest_models
from dualgpuopt.engine.pool import EnginePool

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BenchmarkTest")


class TokenGeneratorBackend:
    """Mock backend that simulates token generation with configurable speed."""

    def __init__(
        self, tokens_per_second: float = 20.0, gpu_util: float = 60.0, memory_usage: float = 4000.0
    ):
        self.name = "TokenGenerator"
        self.loaded = False
        self.model_path = None
        self.tokens_per_second = tokens_per_second
        self.gpu_util = gpu_util
        self.memory_usage = memory_usage

    def load(self, model_path, **kwargs):
        """Simulate loading a model."""
        sleep_time = random.uniform(0.5, 2.0)  # Random load time between 0.5 and 2 seconds
        time.sleep(sleep_time)
        self.loaded = True
        self.model_path = model_path
        logger.info(f"Loaded model {model_path} (simulated load time: {sleep_time:.2f}s)")

    def stream(self, prompt, **kwargs):
        """Simulate token streaming at configured rate."""
        if not self.loaded:
            yield "ERROR: Model not loaded"
            return

        # Calculate total tokens to generate (based on prompt length)
        total_tokens = len(prompt.split()) * 2  # Simple simulation

        # Generate tokens with simulated timing
        for i in range(total_tokens):
            yield f"token_{i} "
            time.sleep(1.0 / self.tokens_per_second)  # Sleep to simulate token generation speed

    def unload(self):
        """Unload the model."""
        logger.info(f"Unloaded model {self.model_path}")
        self.loaded = False


def simulate_chat_session(model_path: str, backend: TokenGeneratorBackend, num_messages: int = 3):
    """
    Simulate a chat session with multiple messages and record benchmark data.

    Args:
    ----
        model_path: Path to the model (for EnginePool)
        backend: The mock backend to use
        num_messages: Number of messages to simulate

    """
    # Path the engine._select_backend to return our mock backend
    with patch.object(Engine, "_select_backend", return_value=backend):
        # Get the engine from the pool
        engine = EnginePool.get(model_path)

        for i in range(num_messages):
            # Generate a random prompt
            prompt_length = random.randint(5, 15)  # Words
            prompt = " ".join([f"word_{j}" for j in range(prompt_length)])

            logger.info(f'Message {i+1}: "{prompt}"')

            # Record start time
            start_time = time.time()

            # Collect tokens
            tokens = []
            token_count = 0

            # Stream tokens
            for token in engine.stream(prompt):
                tokens.append(token)
                token_count += 1

            # Calculate elapsed time and tokens per second
            elapsed = time.time() - start_time
            tokens_per_second = token_count / elapsed

            logger.info(
                f"Generated {token_count} tokens in {elapsed:.2f}s ({tokens_per_second:.2f} tokens/s)"
            )

            # Record benchmark using the EnginePool
            EnginePool.record_benchmark(
                model_path=model_path,
                tokens_per_second=tokens_per_second,
                memory_used=backend.memory_usage,
                gpu_utilization=backend.gpu_util,
                prompt_tokens=prompt_length,
                output_tokens=token_count,
                temperature=0.7,  # Simulated parameter
                context_size=4096,  # Simulated parameter
            )

            # Wait a bit between messages
            time.sleep(0.5)


def test_benchmark_system():
    """Run test of the benchmark system with multiple models."""
    # Create a few different mock backends with different performance characteristics
    fast_model = TokenGeneratorBackend(tokens_per_second=30.0, gpu_util=75.0, memory_usage=8000.0)
    medium_model = TokenGeneratorBackend(tokens_per_second=20.0, gpu_util=60.0, memory_usage=4000.0)
    slow_model = TokenGeneratorBackend(tokens_per_second=10.0, gpu_util=40.0, memory_usage=2000.0)

    # Model paths
    models = {
        "/models/fast-70b-v2": fast_model,
        "/models/medium-13b-v1": medium_model,
        "/models/slow-7b-v3": slow_model,
    }

    # Test each model
    for model_path, backend in models.items():
        logger.info(f"\n=== Testing model: {model_path} ===\n")
        simulate_chat_session(model_path, backend, num_messages=2)

    # Get and display the fastest models
    logger.info("\n=== Fastest Models ===\n")
    fastest_models = get_fastest_models(limit=5)

    for i, model in enumerate(fastest_models):
        logger.info(f"{i+1}. {model['model_path']}")
        logger.info(f"   Average Speed: {model['avg_tokens_per_second']:.2f} tokens/s")
        logger.info(f"   GPU Utilization: {model['avg_gpu_utilization']:.1f}%")
        logger.info(f"   Memory Usage: {model['avg_memory_used']:.0f} MB")
        logger.info(f"   Last Benchmarked: {model['last_benchmark_datetime']}")
        logger.info("")

    # Display database path
    logger.info(f"Benchmark database path: {benchmark_db.db_path}")
    logger.info(
        f"Total benchmarks: {len(benchmark_db.get_model_benchmarks('/models/fast-70b-v2'))}"
    )


if __name__ == "__main__":
    logger.info("Starting benchmark system test...")
    test_benchmark_system()
    logger.info("Test completed.")
