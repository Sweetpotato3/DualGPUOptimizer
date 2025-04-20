"""
Compatibility module for backward compatibility with gpu_info.py
"""
from __future__ import annotations
import sys
from typing import Dict, Any, List, Optional

from dualgpuopt.gpu.info import query
from dualgpuopt.gpu.mock import set_mock_mode, get_mock_mode, generate_mock_gpus

# Create a module-like object that will be used in place of the original gpu_info.py
class GpuInfoCompat:
    """Compatibility class to emulate the original gpu_info.py module"""
    
    @staticmethod
    def query() -> List[Dict[str, Any]]:
        """Emulate original query function"""
        return query()
    
    @staticmethod
    def set_mock_mode(enabled: bool) -> None:
        """Emulate original set_mock_mode function"""
        set_mock_mode(enabled)
    
    @staticmethod
    def get_mock_mode() -> bool:
        """Emulate original get_mock_mode function"""
        return get_mock_mode()
    
    @staticmethod
    def _generate_mock_gpus() -> List[Dict[str, Any]]:
        """Emulate original _generate_mock_gpus function"""
        return generate_mock_gpus()
    
    @staticmethod
    def _query_nvidia() -> List[Dict[str, Any]]:
        """Emulate original _query_nvidia function"""
        from dualgpuopt.gpu.info import _query_nvidia
        return _query_nvidia()
    
    @staticmethod
    def _query_mac() -> List[Dict[str, Any]]:
        """Emulate original _query_mac function"""
        from dualgpuopt.gpu.info import _query_mac
        return _query_mac()

# Create a compatibility module
compat_module = GpuInfoCompat()

# Install the module in sys.modules to enable imports
sys.modules["dualgpuopt.gpu_info"] = compat_module 