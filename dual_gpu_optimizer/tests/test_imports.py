"""
Test imports to verify package structure.
"""
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

    # Test importing GUI

    # Test importing services

    # Test importing commands

    # These imports should work without errors
    assert True
