"""
Recovery mechanisms for error handling in DualGPUOptimizer.

This module provides utilities for recovering from various error conditions,
including GPU failures, memory issues, and configuration problems.
"""

import os
import sys
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Callable

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Recovery")

# Import error handling if available
try:
    from dualgpuopt.error_handler.base import ErrorCategory, ErrorSeverity
    error_handler_available = True
except ImportError:
    error_handler_available = False
    logger.warning("Error handler base module not available, using minimal recovery capabilities")


class RecoveryAction:
    """Enumeration of possible recovery actions"""
    RETRY = "retry"                  # Simply retry the operation
    REINIT_GPU = "reinit_gpu"        # Reinitialize GPU subsystem
    CLEAR_CACHE = "clear_cache"      # Clear memory/caches
    REDUCE_BATCH = "reduce_batch"    # Reduce batch size or workload
    USE_FALLBACK = "use_fallback"    # Use fallback implementation
    RESTART_SERVICE = "restart"      # Restart the affected service
    SHOW_ERROR = "show_error"        # Show error to user
    ABORT = "abort"                  # Abort operation


class RecoveryStrategy:
    """Defines a recovery strategy for a specific error condition"""
    
    def __init__(self, 
                category: Optional[str] = None,
                component: Optional[str] = None,
                error_type: Optional[str] = None,
                max_attempts: int = 3,
                backoff_factor: float = 2.0,
                actions: List[str] = None):
        """
        Initialize recovery strategy
        
        Args:
            category: Error category to match (or None for any)
            component: Component name to match (or None for any)
            error_type: Error type to match (or None for any)
            max_attempts: Maximum retry attempts
            backoff_factor: Exponential backoff factor between retries
            actions: List of RecoveryAction values to try in order
        """
        self.category = category
        self.component = component
        self.error_type = error_type
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.actions = actions or [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK]
    
    def matches(self, category: str, component: str, error_type: str) -> bool:
        """Check if this strategy matches the given error"""
        if self.category and self.category != category:
            return False
        if self.component and self.component != component:
            return False
        if self.error_type and self.error_type != error_type:
            return False
        return True


# Default recovery strategies
DEFAULT_STRATEGIES = [
    # GPU memory errors
    RecoveryStrategy(
        category="GPU_ERROR", 
        error_type="OutOfMemoryError",
        actions=[RecoveryAction.CLEAR_CACHE, RecoveryAction.REDUCE_BATCH, RecoveryAction.USE_FALLBACK]
    ),
    
    # NVML initialization errors
    RecoveryStrategy(
        category="GPU_ERROR",
        error_type="NVMLError",
        actions=[RecoveryAction.REINIT_GPU, RecoveryAction.USE_FALLBACK]
    ),
    
    # File access errors
    RecoveryStrategy(
        category="FILE_ERROR",
        actions=[RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK, RecoveryAction.SHOW_ERROR]
    ),
    
    # Configuration errors
    RecoveryStrategy(
        category="CONFIG_ERROR",
        actions=[RecoveryAction.USE_FALLBACK, RecoveryAction.SHOW_ERROR]
    )
]


class RecoveryManager:
    """Manager for error recovery operations"""
    
    def __init__(self):
        """Initialize recovery manager"""
        self.strategies = DEFAULT_STRATEGIES.copy()
        self.attempt_counts: Dict[str, int] = {}
        self.last_attempt_time: Dict[str, float] = {}
        self.recovery_handlers: Dict[str, Callable] = {
            RecoveryAction.REINIT_GPU: self._handle_gpu_reinit,
            RecoveryAction.CLEAR_CACHE: self._handle_clear_cache,
            RecoveryAction.REDUCE_BATCH: self._handle_reduce_batch,
            RecoveryAction.USE_FALLBACK: self._handle_use_fallback,
            RecoveryAction.RESTART_SERVICE: self._handle_restart_service,
        }
    
    def add_strategy(self, strategy: RecoveryStrategy) -> None:
        """Add a new recovery strategy"""
        self.strategies.append(strategy)
    
    def find_strategy(self, category: str, component: str, error_type: str) -> Optional[RecoveryStrategy]:
        """Find a matching recovery strategy for the error"""
        for strategy in self.strategies:
            if strategy.matches(category, component, error_type):
                return strategy
        return None
    
    def get_next_action(self, error_id: str, strategy: RecoveryStrategy) -> Optional[str]:
        """Get the next recovery action to try
        
        Args:
            error_id: Unique identifier for this error
            strategy: The recovery strategy to use
            
        Returns:
            Next action to try, or None if no more actions available
        """
        # Initialize if this is a new error
        if error_id not in self.attempt_counts:
            self.attempt_counts[error_id] = 0
            self.last_attempt_time[error_id] = 0
        
        # Check if we've exceeded max attempts
        if self.attempt_counts[error_id] >= strategy.max_attempts:
            logger.warning(f"Max recovery attempts ({strategy.max_attempts}) reached for {error_id}")
            return None
        
        # Apply backoff if needed
        current_time = time.time()
        if current_time - self.last_attempt_time[error_id] < (strategy.backoff_factor ** self.attempt_counts[error_id]):
            logger.debug(f"Backoff in effect for {error_id}, waiting...")
            return None
        
        # Get next action from strategy
        action_index = min(self.attempt_counts[error_id], len(strategy.actions) - 1)
        action = strategy.actions[action_index]
        
        # Update attempt count and time
        self.attempt_counts[error_id] += 1
        self.last_attempt_time[error_id] = current_time
        
        return action
    
    def attempt_recovery(self, 
                        error_id: str, 
                        category: str, 
                        component: str, 
                        error_type: str,
                        context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Attempt to recover from an error
        
        Args:
            error_id: Unique identifier for this error
            category: Error category
            component: Component where error occurred
            error_type: Type of error
            context: Additional context for recovery
            
        Returns:
            Tuple of (success, action_taken)
        """
        # Find appropriate strategy
        strategy = self.find_strategy(category, component, error_type)
        if not strategy:
            logger.debug(f"No recovery strategy found for {error_id} ({category}/{component}/{error_type})")
            return False, RecoveryAction.ABORT
        
        # Get next action to try
        action = self.get_next_action(error_id, strategy)
        if not action:
            logger.warning(f"No more recovery actions available for {error_id}")
            return False, RecoveryAction.ABORT
        
        # Attempt recovery
        logger.info(f"Attempting recovery for {error_id} with action: {action}")
        
        # Execute the recovery action
        handler = self.recovery_handlers.get(action)
        if handler:
            success = handler(context or {})
        else:
            # Default simple actions
            success = action != RecoveryAction.ABORT
        
        if success:
            logger.info(f"Recovery action {action} succeeded for {error_id}")
        else:
            logger.warning(f"Recovery action {action} failed for {error_id}")
            
        return success, action
    
    def reset_attempts(self, error_id: str) -> None:
        """Reset attempt counter for a specific error"""
        if error_id in self.attempt_counts:
            self.attempt_counts[error_id] = 0
            self.last_attempt_time[error_id] = 0
    
    def _handle_gpu_reinit(self, context: Dict[str, Any]) -> bool:
        """Handle GPU reinitialization"""
        try:
            # Import telemetry module
            from dualgpuopt.telemetry import reset_telemetry_service
            
            # Reset telemetry service (which reinitializes NVML)
            success = reset_telemetry_service()
            return success
        except ImportError:
            logger.error("Failed to import telemetry module for GPU reinitialization")
            return False
        except Exception as e:
            logger.error(f"Error reinitializing GPU: {e}")
            return False
    
    def _handle_clear_cache(self, context: Dict[str, Any]) -> bool:
        """Handle cache clearing"""
        try:
            # Try to run garbage collection
            import gc
            gc.collect()
            
            # If torch is available, clear CUDA cache
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("CUDA cache cleared")
            except ImportError:
                logger.debug("PyTorch not available, skipping CUDA cache clearing")
            
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def _handle_reduce_batch(self, context: Dict[str, Any]) -> bool:
        """Handle batch size reduction"""
        try:
            # Get current batch size from context
            current_batch = context.get("batch_size", 0)
            if not current_batch:
                logger.warning("No batch size specified in context")
                return False
            
            # Calculate reduced batch size (25% reduction, minimum 1)
            reduced_batch = max(1, int(current_batch * 0.75))
            if reduced_batch >= current_batch:
                reduced_batch = max(1, current_batch - 1)
            
            # Update context with new batch size
            context["batch_size"] = reduced_batch
            context["reduced_from"] = current_batch
            
            logger.info(f"Reduced batch size from {current_batch} to {reduced_batch}")
            return True
        except Exception as e:
            logger.error(f"Error reducing batch size: {e}")
            return False
    
    def _handle_use_fallback(self, context: Dict[str, Any]) -> bool:
        """Handle fallback to alternative implementation"""
        try:
            # Mark that we should use fallback implementation
            context["use_fallback"] = True
            return True
        except Exception as e:
            logger.error(f"Error setting fallback mode: {e}")
            return False
    
    def _handle_restart_service(self, context: Dict[str, Any]) -> bool:
        """Handle service restart"""
        try:
            # Get service name from context
            service_name = context.get("service_name")
            if not service_name:
                logger.warning("No service name specified in context")
                return False
            
            # Check if we have a restart function
            restart_func = context.get("restart_func")
            if restart_func and callable(restart_func):
                # Call the restart function
                return restart_func()
            
            # No restart function, try to restart based on service name
            if service_name == "telemetry":
                from dualgpuopt.telemetry import get_telemetry_service
                service = get_telemetry_service()
                # Stop and start the service
                service.stop()
                time.sleep(1.0)  # Brief pause
                service.start()
                return True
            
            logger.warning(f"No restart method for service: {service_name}")
            return False
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return False


# Singleton instance
_recovery_manager: Optional[RecoveryManager] = None


def get_recovery_manager() -> RecoveryManager:
    """Get the global recovery manager instance"""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager


def attempt_recovery(error_id: str, 
                   category: str, 
                   component: str, 
                   error_type: str,
                   context: Dict[str, Any] = None) -> Tuple[bool, str]:
    """Attempt to recover from an error (convenience function)"""
    manager = get_recovery_manager()
    return manager.attempt_recovery(error_id, category, component, error_type, context)


def verify_config(config: Dict[str, Any], 
                required_keys: List[str], 
                defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Verify configuration and apply defaults for missing values
    
    Args:
        config: Configuration dictionary to verify
        required_keys: List of required keys
        defaults: Default values for missing keys
        
    Returns:
        Verified configuration with defaults applied
    """
    if not isinstance(config, dict):
        logger.warning(f"Invalid configuration type: {type(config)}, using defaults")
        config = {}
    
    # Check required keys
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        logger.warning(f"Missing required configuration keys: {missing_keys}")
    
    # Apply defaults for missing keys
    for key, default_value in defaults.items():
        if key not in config or config[key] is None:
            config[key] = default_value
    
    return config


def ensure_directory(directory_path: str) -> bool:
    """Ensure a directory exists, creating it if necessary
    
    Args:
        directory_path: Path to directory
        
    Returns:
        True if directory exists or was created, False on error
    """
    if not directory_path:
        return False
        
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return os.path.isdir(directory_path)
    except Exception as e:
        logger.error(f"Error ensuring directory {directory_path}: {e}")
        return False


def safe_import(module_name: str) -> Tuple[bool, Any]:
    """Safely import a module with error handling
    
    Args:
        module_name: Name of module to import
        
    Returns:
        Tuple of (success, module) where module is None on failure
    """
    try:
        __import__(module_name)
        module = sys.modules[module_name]
        return True, module
    except ImportError as e:
        logger.warning(f"Failed to import {module_name}: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Error importing {module_name}: {e}")
        return False, None 