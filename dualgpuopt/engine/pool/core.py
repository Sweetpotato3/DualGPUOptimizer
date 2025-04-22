"""
EnginePool - Hot-swapping engine pool for LLM inference.
"""
import os
import time
import threading
import logging
import json
import atexit
from typing import Dict, Any, List, Optional, Generator, TypeVar, Callable
from collections import OrderedDict
import weakref

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics integration (optional)
try:
    import prometheus_client as prom
    HAVE_PROMETHEUS = True
    
    # Only start Prometheus server if explicitly enabled via environment variable
    if os.getenv('DUALGPUOPT_METRICS_PORT'):
        prom_port = int(os.getenv('DUALGPUOPT_METRICS_PORT'))
        prom.start_http_server(prom_port)
        logger.info(f"Prometheus metrics server started on port {prom_port}")
    
    # Define metrics
    ENGINE_CACHE_SIZE = prom.Gauge('engine_cache_size', 'Number of models in cache')
    ENGINE_CACHE_HITS = prom.Counter('engine_cache_hits_total', 'Total cache hits', ['model'])
    ENGINE_CACHE_MISSES = prom.Counter('engine_cache_misses_total', 'Total cache misses', ['model'])
    ENGINE_LOAD_TIME = prom.Histogram('engine_load_time_seconds', 'Time to load model', ['model'])
    ENGINE_HEALTH_CHECKS = prom.Counter('engine_health_checks_total', 'Total health checks', ['model'])
    ENGINE_HEALTH_FAILURES = prom.Counter('engine_health_failures_total', 'Failed health checks', ['model'])
    
except ImportError:
    HAVE_PROMETHEUS = False
    logger.warning("Prometheus client not installed, metrics will not be available")
    # Define dummy metric classes for when prometheus is not available
    class DummyMetric:
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
    
    ENGINE_CACHE_SIZE = DummyMetric()
    ENGINE_CACHE_HITS = DummyMetric()
    ENGINE_CACHE_MISSES = DummyMetric()
    ENGINE_LOAD_TIME = DummyMetric()
    ENGINE_HEALTH_CHECKS = DummyMetric()
    ENGINE_HEALTH_FAILURES = DummyMetric()

# Sanitize model path for use as metric label (safe for Prometheus)
def _sanitize_label(path: str) -> str:
    """Sanitize model path for use as a metric label."""
    # Convert to string if needed
    path_str = str(path)
    # Remove special characters
    sanitized = ''.join(c if c.isalnum() or c in '-_/' else '_' for c in path_str)
    # Truncate if too long to avoid label cardinality issues
    if len(sanitized) > 100:
        sanitized = sanitized[:97] + "..."
    return sanitized

# Type for the Engine class
EngineType = TypeVar('EngineType')

class Engine:
    """Base Engine class - will be implemented by specific engine backends."""
    
    def __init__(self, model_path: str, **kwargs):
        """Initialize engine with model path and options."""
        self.model_path = model_path
        self.options = kwargs
        self.last_used = time.time()
        self.last_health_check = 0
        self.health_failures = 0
        self.max_failures = int(os.getenv('DUALGPUOPT_MAX_ENGINE_FAILURES', '3'))
        
        # Backend-specific initialization will happen in subclasses
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion for the given prompt."""
        raise NotImplementedError("Subclasses must implement generate()")
    
    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Stream text completion tokens for the given prompt."""
        raise NotImplementedError("Subclasses must implement stream()")
    
    def embedding(self, text: str) -> List[float]:
        """Generate embeddings for the given text."""
        raise NotImplementedError("Subclasses must implement embedding()")
    
    def is_healthy(self) -> bool:
        """Check if the engine is healthy and ready to use."""
        # Default implementation: just return True
        # Subclasses should override this with actual health checks
        return True
    
    def shutdown(self) -> None:
        """Clean up resources used by the engine."""
        # Default implementation: do nothing
        # Subclasses should override this with actual cleanup logic
        pass

class MockEngine(Engine):
    """Mock engine for testing and development."""
    
    def __init__(self, model_path: str, **kwargs):
        """Initialize mock engine."""
        super().__init__(model_path, **kwargs)
        logger.info(f"Initialized MockEngine with model {model_path}")
        
    def generate(self, prompt: str, max_tokens: int = 100, **kwargs) -> str:
        """Generate mock completion."""
        self.last_used = time.time()
        # Simple mock generation
        if "legal" in self.model_path.lower():
            return f"Réponse juridique au sujet de: {prompt[:20]}..."
        else:
            return f"Response to: {prompt[:20]}..."
    
    def stream(self, prompt: str, max_tokens: int = 100, **kwargs) -> Generator[str, None, None]:
        """Stream mock completion tokens."""
        self.last_used = time.time()
        
        # Simple mock streaming
        response = self.generate(prompt, max_tokens, **kwargs)
        words = response.split()
        
        for word in words:
            yield word + " "
            time.sleep(0.1)  # Simulate delay between tokens
    
    def embedding(self, text: str) -> List[float]:
        """Generate mock embeddings."""
        self.last_used = time.time()
        # Return a fixed-size vector of random-ish values derived from the text
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        # Generate 384-dimensional vector (common embedding size)
        return [(float(b) / 255.0) * 2 - 1 for b in hash_bytes * 24]
    
    def is_healthy(self) -> bool:
        """Check if mock engine is healthy."""
        self.last_health_check = time.time()
        # Mock engine is always healthy
        return True

class EnginePool:
    """
    Thread-safe model engine pool with LRU caching.
    
    This class manages model loading and caching for efficient model switching.
    It automatically unloads least recently used models when the cache is full.
    """
    
    # Class-level attributes
    _instance = None
    _lock = threading.RLock()  # Allows re-entry from the same thread
    _engines = OrderedDict()  # LRU cache: model_path -> engine
    _max_cache_size = int(os.getenv('DUALGPUOPT_ENGINE_CACHE_SIZE', '2'))
    _health_thread = None
    _thread_stop = threading.Event()
    _thread_local = threading.local()  # Thread-local storage
    
    @classmethod
    def get(cls, model_path: str, **kwargs) -> Engine:
        """
        Get an engine for the specified model, using cache if available.
        
        Args:
            model_path: Path to the model
            **kwargs: Additional options for the engine
            
        Returns:
            Engine instance for the specified model
        """
        # Create the singleton instance if it doesn't exist
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    # Register shutdown handler
                    atexit.register(cls._shutdown)
                    # Start health check thread
                    cls._start_health_thread()
        
        # Sanitize model path for metrics
        model_label = _sanitize_label(model_path)
        
        # Check if engine is already in cache
        with cls._lock:
            cache_key = (model_path, json.dumps(kwargs, sort_keys=True))
            
            if cache_key in cls._engines:
                # Update LRU ordering
                engine = cls._engines.pop(cache_key)
                cls._engines[cache_key] = engine
                engine.last_used = time.time()
                
                # Update metrics
                ENGINE_CACHE_HITS.labels(model=model_label).inc()
                
                logger.debug(f"Cache hit for model {model_path}")
                return engine
        
        # Not in cache, load the engine
        ENGINE_CACHE_MISSES.labels(model=model_label).inc()
        
        # Start timing model loading
        start_time = time.time()
        
        # Create new engine instance
        try:
            engine = cls._create_engine(model_path, **kwargs)
            load_time = time.time() - start_time
            ENGINE_LOAD_TIME.labels(model=model_label).observe(load_time)
            logger.info(f"Loaded model {model_path} in {load_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error loading model {model_path}: {e}")
            # Fall back to mock engine in case of loading error
            engine = MockEngine(model_path, **kwargs)
        
        # Add to cache with thread-safe locking
        with cls._lock:
            # Check if cache is full and evict least recently used
            if len(cls._engines) >= cls._max_cache_size:
                cls._evict_lru()
            
            # Add to cache
            cache_key = (model_path, json.dumps(kwargs, sort_keys=True))
            cls._engines[cache_key] = engine
            
            # Update metrics
            ENGINE_CACHE_SIZE.set(len(cls._engines))
        
        return engine
    
    @classmethod
    def _create_engine(cls, model_path: str, **kwargs) -> Engine:
        """
        Create an engine for the specified model.
        
        Args:
            model_path: Path to the model
            **kwargs: Additional options for the engine
            
        Returns:
            Engine instance for the specified model
        """
        # Here we would implement autodetection of model type and create
        # the appropriate engine based on file extension or HF model type
        
        # Check if model path is a file or HuggingFace model ID
        if os.path.exists(model_path):
            # Model is a local file, check extension
            if model_path.endswith('.gguf'):
                # Use LlamaCppEngine for GGUF models
                try:
                    from dualgpuopt.engine.llamacpp import LlamaCppEngine
                    return LlamaCppEngine(model_path, **kwargs)
                except ImportError:
                    logger.warning("LlamaCppEngine not available, using MockEngine")
                    return MockEngine(model_path, **kwargs)
            
            # Add more file type checks here for other model types
            
        else:
            # Assume HuggingFace model ID
            try:
                from dualgpuopt.engine.hf import HuggingFaceEngine
                return HuggingFaceEngine(model_path, **kwargs)
            except ImportError:
                logger.warning("HuggingFaceEngine not available, using MockEngine")
                return MockEngine(model_path, **kwargs)
        
        # Default to mock engine if no specific engine was created
        logger.info(f"No specific engine for {model_path}, using MockEngine")
        return MockEngine(model_path, **kwargs)
    
    @classmethod
    def _evict_lru(cls) -> None:
        """Evict the least recently used engine from the cache."""
        # This must be called with _lock held
        if not cls._engines:
            return
        
        # Get the oldest item
        oldest_key, oldest_engine = next(iter(cls._engines.items()))
        
        # Shutdown the engine
        try:
            logger.info(f"Evicting model {oldest_engine.model_path} from cache")
            oldest_engine.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down engine {oldest_engine.model_path}: {e}")
        
        # Remove from cache
        del cls._engines[oldest_key]
        
        # Update metrics
        ENGINE_CACHE_SIZE.set(len(cls._engines))
    
    @classmethod
    def _start_health_thread(cls) -> None:
        """Start a thread to check engine health periodically."""
        if cls._health_thread is not None and cls._health_thread.is_alive():
            return
        
        # Reset stop event
        cls._thread_stop.clear()
        
        def health_check_loop():
            """Periodically check all engines for health."""
            logger.info("Started engine health check thread")
            
            while not cls._thread_stop.is_set():
                try:
                    # Sleep first to give time for initial setup
                    cls._thread_stop.wait(60)  # Check every minute
                    if cls._thread_stop.is_set():
                        break
                    
                    # Get a snapshot of engines to check, with lock
                    engines_to_check = []
                    with cls._lock:
                        for cache_key, engine in cls._engines.items():
                            engines_to_check.append((cache_key, engine))
                    
                    # Check each engine without holding the lock
                    for cache_key, engine in engines_to_check:
                        model_label = _sanitize_label(engine.model_path)
                        
                        try:
                            # Skip if checked recently
                            if time.time() - engine.last_health_check < 300:  # 5 minutes
                                continue
                            
                            # Update health check counter
                            ENGINE_HEALTH_CHECKS.labels(model=model_label).inc()
                            
                            # Check health
                            is_healthy = engine.is_healthy()
                            
                            if not is_healthy:
                                # Increment failure counter and metrics
                                engine.health_failures += 1
                                ENGINE_HEALTH_FAILURES.labels(model=model_label).inc()
                                
                                logger.warning(f"Engine {engine.model_path} health check failed "
                                              f"({engine.health_failures}/{engine.max_failures})")
                                
                                # If too many failures, remove from cache and reload
                                if engine.health_failures >= engine.max_failures:
                                    with cls._lock:
                                        if cache_key in cls._engines:
                                            logger.error(f"Engine {engine.model_path} failed too many health checks, "
                                                       f"removing from cache")
                                            try:
                                                engine.shutdown()
                                            except Exception as e:
                                                logger.error(f"Error shutting down engine {engine.model_path}: {e}")
                                            
                                            # Remove from cache
                                            del cls._engines[cache_key]
                                            ENGINE_CACHE_SIZE.set(len(cls._engines))
                        
                        except Exception as e:
                            logger.error(f"Error during health check for {engine.model_path}: {e}")
                
                except Exception as e:
                    logger.error(f"Error in health check thread: {e}")
        
        # Start the thread
        cls._health_thread = threading.Thread(
            target=health_check_loop,
            name="EngineHealthChecker",
            daemon=True
        )
        cls._health_thread.start()
    
    @classmethod
    def _shutdown(cls) -> None:
        """Clean up resources and shut down engines."""
        logger.info("Shutting down EnginePool")
        
        # Stop health check thread
        cls._thread_stop.set()
        if cls._health_thread and cls._health_thread.is_alive():
            cls._health_thread.join(timeout=5)
        
        # Shut down all engines
        with cls._lock:
            for cache_key, engine in list(cls._engines.items()):
                try:
                    logger.info(f"Shutting down engine for {engine.model_path}")
                    engine.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down engine {engine.model_path}: {e}")
            
            # Clear cache
            cls._engines.clear()
            ENGINE_CACHE_SIZE.set(0)
    
    @classmethod
    def get_cache_info(cls) -> Dict[str, Any]:
        """
        Get information about the current engine cache.
        
        Returns:
            Dictionary with cache statistics and model information
        """
        with cls._lock:
            models = []
            for (model_path, _), engine in cls._engines.items():
                models.append({
                    'path': model_path,
                    'last_used': engine.last_used,
                    'last_health_check': engine.last_health_check,
                    'health_failures': engine.health_failures,
                    'health_status': 'healthy' if engine.health_failures == 0 else
                                   'warning' if engine.health_failures < engine.max_failures else 'unhealthy'
                })
            
            return {
                'max_size': cls._max_cache_size,
                'current_size': len(cls._engines),
                'models': models
            }

# Global exception handler for model errors
def handle_engine_exception(func: Callable) -> Callable:
    """Decorator to handle exceptions from engine operations."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Engine error in {func.__name__}: {e}")
            # In a real implementation, could display a dialog or send to an error reporting service
            # For now, just log and re-raise
            raise
    return wrapper
