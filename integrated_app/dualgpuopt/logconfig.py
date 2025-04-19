#!/usr/bin/env python3
"""
Centralized logging configuration for the DualGPUOptimizer.
"""
from __future__ import annotations

import logging
import logging.handlers
import pathlib
import sys
from typing import Dict, Optional


def setup_logging(verbose: bool = False, log_file: Optional[pathlib.Path] = None) -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        verbose: Whether to enable DEBUG level logging
        log_file: Optional path to write logs to
        
    Returns:
        Root logger for the application
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logger
    logger = logging.getLogger("dualgpuopt")
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    simple_fmt = logging.Formatter("%(levelname)s: %(message)s")
    detailed_fmt = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console handler
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(simple_fmt)
    logger.addHandler(console)
    
    # File handler (if requested)
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=1024*1024, backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)  # Always log details to file
        file_handler.setFormatter(detailed_fmt)
        logger.addHandler(file_handler)
    
    # Configure module-specific log levels
    configure_module_log_levels(verbose)
    
    return logger


def configure_module_log_levels(verbose: bool = False) -> None:
    """
    Configure specific log levels for different modules.
    
    Args:
        verbose: Whether debug mode is enabled globally
    """
    # Default level based on verbose flag
    default_level = logging.DEBUG if verbose else logging.INFO
    
    # Module-specific log levels
    module_levels: Dict[str, int] = {
        # Set GPU module to a higher level to reduce polling noise
        "dualgpuopt.gpu_info": logging.WARNING,
        "dualgpuopt.telemetry": logging.WARNING,
        
        # Keep critical modules at INFO level even in non-verbose mode
        "dualgpuopt.services.error": logging.INFO,
        "dualgpuopt.services.config": logging.INFO,
        "dualgpuopt.services.state": logging.INFO,
        
        # Set other modules at default level
        "dualgpuopt.optimizer": default_level,
        "dualgpuopt.layer_balance": default_level,
        "dualgpuopt.mpolicy": default_level
    }
    
    # Override with DEBUG if verbose mode is enabled
    if verbose:
        for key in list(module_levels.keys()):
            module_levels[key] = logging.DEBUG
    
    # Apply the log levels
    for module, level in module_levels.items():
        logging.getLogger(module).setLevel(level) 