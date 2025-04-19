"""
Test imports to verify package structure.
"""
import sys
from .context import dualgpuopt

def test_version():
    """Test that VERSION is accessible."""
    assert dualgpuopt.VERSION
    assert isinstance(dualgpuopt.VERSION, str)

def test_mock_mode():
    """Test mock mode functions."""
    assert not dualgpuopt.is_mock_mode_enabled()
    dualgpuopt.enable_mock_mode()
    assert dualgpuopt.is_mock_mode_enabled()

def test_module_imports():
    """Test that various modules can be imported without circular import errors."""
    # Test importing GPU info
    from dualgpuopt import gpu_info
    
    # Test importing GUI
    from dualgpuopt.gui import run_app
    
    # Test importing services
    from dualgpuopt.services import event_bus
    
    # Test importing commands
    from dualgpuopt.commands import command_base
    
    # These imports should work without errors
    assert True 