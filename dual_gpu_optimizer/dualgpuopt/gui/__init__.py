"""
GUI module for the DualGPUOptimizer.

This package contains all the GUI components and functionality.
"""
from __future__ import annotations

from dualgpuopt.gui.app import DualGpuApp, run_app
from dualgpuopt.gui.dashboard import GpuDashboard
from dualgpuopt.gui.event_dashboard import EventDrivenDashboard

__all__ = ["DualGpuApp", "run_app", "GpuDashboard", "EventDrivenDashboard"] 