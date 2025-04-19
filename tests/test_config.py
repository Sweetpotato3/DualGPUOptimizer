"""
Test suite for configuration management.
"""
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from dualgpuopt import configio


def test_validate_config_defaults():
    """Test config validation with empty input."""
    # Empty input should return defaults
    result = configio.validate_config({})
    assert result == configio._DEFAULT


def test_validate_config_theme():
    """Test theme validation."""
    # Valid themes
    for theme in ["dark", "light", "system"]:
        result = configio.validate_config({"theme": theme})
        assert result["theme"] == theme

    # Invalid theme should get default
    result = configio.validate_config({"theme": "invalid"})
    assert result["theme"] == configio._DEFAULT["theme"]


def test_validate_config_integers():
    """Test integer validation."""
    # Valid values
    result = configio.validate_config({
        "ctx": 32768,
        "alert_threshold": 50,
        "alert_duration": 120
    })
    assert result["ctx"] == 32768
    assert result["alert_threshold"] == 50
    assert result["alert_duration"] == 120

    # Invalid values (negative)
    result = configio.validate_config({
        "ctx": -1000,
        "alert_threshold": -10,
        "alert_duration": -50
    })
    assert result["ctx"] == configio._DEFAULT["ctx"]
    assert result["alert_threshold"] == configio._DEFAULT["alert_threshold"]
    assert result["alert_duration"] == configio._DEFAULT["alert_duration"]


def test_validate_config_monitor_interval():
    """Test monitor interval validation."""
    # Valid interval
    result = configio.validate_config({"monitor_interval": 2.5})
    assert result["monitor_interval"] == 2.5

    # Too small
    result = configio.validate_config({"monitor_interval": 0.01})
    assert result["monitor_interval"] == configio._DEFAULT["monitor_interval"]

    # Too large
    result = configio.validate_config({"monitor_interval": 100.0})
    assert result["monitor_interval"] == configio._DEFAULT["monitor_interval"]

    # Invalid type
    result = configio.validate_config({"monitor_interval": "fast"})
    assert result["monitor_interval"] == configio._DEFAULT["monitor_interval"]


def test_validate_config_env_overrides():
    """Test environment overrides validation."""
    overrides = {
        "CUDA_VISIBLE_DEVICES": "0,1",
        "OMP_NUM_THREADS": 8
    }
    result = configio.validate_config({"env_overrides": overrides})
    assert result["env_overrides"] == {"CUDA_VISIBLE_DEVICES": "0,1", "OMP_NUM_THREADS": "8"}

    # Invalid type
    result = configio.validate_config({"env_overrides": "invalid"})
    assert result["env_overrides"] == configio._DEFAULT["env_overrides"]


def test_validate_config_fav_paths():
    """Test favorite paths validation."""
    paths = ["/models/llama", "C:/models/mistral"]
    result = configio.validate_config({"fav_paths": paths})
    assert result["fav_paths"] == paths

    # Invalid type
    result = configio.validate_config({"fav_paths": "not_a_list"})
    assert result["fav_paths"] == configio._DEFAULT["fav_paths"]


def test_load_cfg_no_file():
    """Test loading config when file doesn't exist."""
    # Create a backup of the original function
    original_exists = Path.exists
    
    try:
        # Replace Path.exists with a mock that always returns False
        Path.exists = lambda self: False
        
        # Call the function under test
        result = configio.load_cfg()
        
        # Verify results
        assert result == configio._DEFAULT
    
    finally:
        # Restore the original function
        Path.exists = original_exists


def test_load_cfg_with_file(monkeypatch):
    """Test loading config from file using monkeypatch."""
    # Test data
    test_config = {"theme": "light", "ctx": 32768}
    
    # Mock the exists function to return True
    monkeypatch.setattr(Path, "exists", lambda self: True)
    
    # Mock the open function to avoid file system access
    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Mock tomllib.load to return our test data
    monkeypatch.setattr("tomllib.load", lambda file: test_config)
    
    # Call the function under test
    result = configio.load_cfg()
    
    # Verify the result
    assert result["theme"] == "light"
    assert result["ctx"] == 32768


def test_save_cfg(monkeypatch):
    """Test saving config to file using monkeypatch."""
    # Test data
    test_config = {"theme": "light", "ctx": 32768}
    
    # Mock dependencies
    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)
    
    mock_dump = mock.Mock()
    monkeypatch.setattr("tomli_w.dump", mock_dump)
    
    # Call the function under test
    configio.save_cfg(test_config)
    
    # Verify mock was called
    mock_open.assert_called_once()
    mock_dump.assert_called_once() 