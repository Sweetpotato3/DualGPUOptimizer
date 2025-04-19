"""
GUI module for the DualGPUOptimizer.

This is a legacy module that redirects to the new refactored structure.
"""
from __future__ import annotations

from dualgpuopt.gui.app import DualGpuApp, run_app
# Re-export for backward compatibility
__all__ = ["DualGpuApp", "run_app"]