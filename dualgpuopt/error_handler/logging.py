"""
Error logging configuration for the DualGPUOptimizer.

This module provides utilities for setting up and configuring logging
for error handling throughout the application.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


def configure_logging(log_dir: str, 
                     console_level: int = logging.INFO,
                     file_level: int = logging.DEBUG,
                     max_size: int = 10 * 1024 * 1024,  # 10 MB
                     backup_count: int = 5) -> None:
    """
    Configure logging for the application
    
    Args:
        log_dir: Directory to store log files
        console_level: Logging level for console output
        file_level: Logging level for file output
        max_size: Maximum size of log file before rotation (bytes)
        backup_count: Number of backup log files to keep
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(console_level)
    console_format = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    console.setFormatter(console_format)
    root_logger.addHandler(console)
    
    # Create error log file handler
    error_log = os.path.join(log_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_log, maxBytes=max_size, backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_format)
    root_logger.addHandler(error_handler)
    
    # Create debug log file handler
    debug_log = os.path.join(log_dir, 'debug.log')
    debug_handler = RotatingFileHandler(
        debug_log, maxBytes=max_size, backupCount=backup_count
    )
    debug_handler.setLevel(file_level)
    debug_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    debug_handler.setFormatter(debug_format)
    root_logger.addHandler(debug_handler)
    
    # Log initialization
    logging.info(f"Logging initialized: console={console_level}, file={file_level}")
    logging.info(f"Log files: {error_log} and {debug_log}")


def get_error_logger(component: str) -> logging.Logger:
    """
    Get a logger configured for error handling for a specific component
    
    Args:
        component: Component name for the logger
        
    Returns:
        Configured logger
    """
    logger_name = f"DualGPUOpt.{component}"
    return logging.getLogger(logger_name)


def log_system_info() -> None:
    """Log system information for diagnostics"""
    import platform
    import sys
    
    logger = logging.getLogger("DualGPUOpt.System")
    
    logger.info("System Information:")
    logger.info(f"  Platform: {platform.platform()}")
    logger.info(f"  Python: {sys.version}")
    logger.info(f"  Processor: {platform.processor()}")
    
    # Log environment variables that might be relevant
    env_vars = ['CUDA_VISIBLE_DEVICES', 'PYTORCH_CUDA_ALLOC_CONF', 'PATH']
    logger.info("Environment Variables:")
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        logger.info(f"  {var}: {value}")


def log_exception(e: Exception, component: str, additional_info: Optional[str] = None) -> None:
    """
    Log an exception with additional information
    
    Args:
        e: The exception to log
        component: Component name where the exception occurred
        additional_info: Additional information to include in the log
    """
    logger = get_error_logger(component)
    
    import traceback
    tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    
    message = f"Exception in {component}: {e}"
    if additional_info:
        message += f"\nAdditional info: {additional_info}"
        
    logger.error(message)
    logger.debug(f"Exception traceback:\n{tb_str}") 