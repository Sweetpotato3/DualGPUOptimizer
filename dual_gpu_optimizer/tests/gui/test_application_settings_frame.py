"""
Unit tests for the ApplicationSettingsFrame component.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the components to test
from dualgpuopt.gui.settings.application_settings import ApplicationSettingsFrame


class TestApplicationSettingsFrame(unittest.TestCase):
    """Test cases for the ApplicationSettingsFrame class."""

    def setUp(self):
        """Set up the test environment."""
        self.root = tk.Tk()
        self.parent = ttk.Frame(self.root)
        self.callback = MagicMock()

        # Mock config_service.get to return preset values
        self.config_values = {
            "start_minimized": True,
            "idle_alerts": False,
            "idle_threshold": 40,
            "idle_time": 10,
        }

        with patch(
            "dualgpuopt.services.config_service.config_service.get",
            side_effect=lambda key, default: self.config_values.get(key, default),
        ):
            # Create the application settings frame with the callback
            self.app_settings_frame = ApplicationSettingsFrame(
                self.parent, pad=10, on_settings_change=self.callback
            )

    def tearDown(self):
        """Clean up after tests."""
        if self.root:
            self.root.destroy()

    def test_init(self):
        """Test initialization of the ApplicationSettingsFrame."""
        # Verify the application settings frame was initialized properly
        self.assertIsInstance(self.app_settings_frame, ApplicationSettingsFrame)
        self.assertEqual(self.app_settings_frame.parent, self.parent)
        self.assertEqual(self.app_settings_frame.pad, 10)
        self.assertEqual(self.app_settings_frame.on_settings_change, self.callback)

    def test_get_settings(self):
        """Test getting all settings."""
        # Set the frame's variables to known values
        self.app_settings_frame.start_min_var.set(True)
        self.app_settings_frame.idle_alerts_var.set(False)
        self.app_settings_frame.idle_threshold_var.set(45)
        self.app_settings_frame.idle_time_var.set(15)

        settings = self.app_settings_frame.get_settings()

        # Verify that the returned settings match the expected values
        self.assertEqual(
            settings,
            {
                "start_minimized": True,
                "idle_alerts": False,
                "idle_threshold": 45,
                "idle_time": 15,
            },
        )

    def test_apply_settings_all(self):
        """Test applying all settings."""
        # Define test settings
        test_settings = {
            "start_minimized": False,
            "idle_alerts": True,
            "idle_threshold": 35,
            "idle_time": 7,
        }

        # Apply the settings
        self.app_settings_frame.apply_settings(test_settings)

        # Verify that the variables were updated correctly
        self.assertEqual(self.app_settings_frame.start_min_var.get(), False)
        self.assertEqual(self.app_settings_frame.idle_alerts_var.get(), True)
        self.assertEqual(self.app_settings_frame.idle_threshold_var.get(), 35)
        self.assertEqual(self.app_settings_frame.idle_time_var.get(), 7)

        # Verify that the callback was called with the expected message
        self.callback.assert_called_once_with("Application settings updated")

    def test_apply_settings_partial(self):
        """Test applying only some settings."""
        # Set initial variable values
        self.app_settings_frame.start_min_var.set(True)
        self.app_settings_frame.idle_alerts_var.set(False)
        self.app_settings_frame.idle_threshold_var.set(40)
        self.app_settings_frame.idle_time_var.set(10)

        # Define partial settings to apply
        partial_settings = {"idle_threshold": 25, "idle_time": 3}

        # Apply the settings
        self.app_settings_frame.apply_settings(partial_settings)

        # Verify that only the specified settings were updated
        self.assertEqual(self.app_settings_frame.start_min_var.get(), True)  # Unchanged
        self.assertEqual(
            self.app_settings_frame.idle_alerts_var.get(), False
        )  # Unchanged
        self.assertEqual(
            self.app_settings_frame.idle_threshold_var.get(), 25
        )  # Changed
        self.assertEqual(self.app_settings_frame.idle_time_var.get(), 3)  # Changed

        # Verify that the callback was called with the expected message
        self.callback.assert_called_once_with("Application settings updated")

    def test_apply_settings_no_callback(self):
        """Test applying settings without a callback."""
        # Create a new frame without a callback
        with patch(
            "dualgpuopt.services.config_service.config_service.get",
            side_effect=lambda key, default: self.config_values.get(key, default),
        ):
            app_settings_frame = ApplicationSettingsFrame(
                self.parent, pad=10, on_settings_change=None
            )

        # Define test settings
        test_settings = {"start_minimized": False, "idle_alerts": True}

        # Apply the settings - this should not raise an error
        app_settings_frame.apply_settings(test_settings)

        # Verify that the variables were updated correctly
        self.assertEqual(app_settings_frame.start_min_var.get(), False)
        self.assertEqual(app_settings_frame.idle_alerts_var.get(), True)


if __name__ == "__main__":
    unittest.main()
