#!/usr/bin/env python3
"""
DualGPUOptimizer - A utility for optimizing dual GPU setups for ML model inference.
"""

__version__ = "0.1.0"

import os
import logging

# Early setup of environment variables
if os.environ.get("DGPUOPT_MOCK_GPUS") == "1":
    MOCK_MODE = True
else:
    MOCK_MODE = False

# Initialize logger
logger = logging.getLogger("dualgpuopt")