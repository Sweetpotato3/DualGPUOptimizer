"""
Centralized logging configuration for the DualGPUOptimizer.
"""
from __future__ import annotations

import logging
import logging.handlers
import pathlib
import sys
from typing import Optional


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
    
    return logger 