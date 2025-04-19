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


@mock.patch.object(configio.CFG_PATH, 'exists')
@mock.patch.object(configio.CFG_PATH, 'open')
def test_load_cfg_no_file(mock_open, mock_exists):
    """Test loading config when file doesn't exist."""
    mock_exists.return_value = False
    result = configio.load_cfg()
    assert result == configio._DEFAULT
    mock_open.assert_not_called()


@mock.patch.object(configio.tomllib, 'load')
@mock.patch.object(configio.CFG_PATH, 'exists')
@mock.patch.object(configio.CFG_PATH, 'open')
def test_load_cfg_with_file(mock_open, mock_exists, mock_toml_load):
    """Test loading config from file."""
    mock_exists.return_value = True
    mock_file = mock.MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_toml_load.return_value = {"theme": "light", "ctx": 32768}
    
    result = configio.load_cfg()
    
    mock_open.assert_called_once()
    mock_toml_load.assert_called_once_with(mock_file)
    assert result["theme"] == "light"
    assert result["ctx"] == 32768


@mock.patch.object(configio.tomli_w, 'dump')
@mock.patch.object(configio.CFG_PATH, 'open')
def test_save_cfg(mock_open, mock_toml_dump):
    """Test saving config to file."""
    # Prepare mock file
    mock_file = mock.MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Test data
    test_config = {"theme": "light", "ctx": 32768}
    
    # Call function
    configio.save_cfg(test_config)
    
    # Verify calls
    mock_open.assert_called_once()
    mock_toml_dump.assert_called_once()
    
    # Check validation was applied
    args, _ = mock_toml_dump.call_args
    saved_config = args[0]
    assert saved_config["theme"] == "light"
    assert saved_config["ctx"] == 32768 