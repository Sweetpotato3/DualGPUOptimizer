"""
Unit tests for the OverclockingFrame component.
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
from dualgpuopt.gui.settings.overclocking import OverclockingFrame
from dualgpuopt.gpu_info import GPU


class TestOverclockingFrame(unittest.TestCase):
    """Test cases for the OverclockingFrame class."""

    def setUp(self):
        """Set up the test environment."""
        self.root = tk.Tk()
        self.parent = ttk.Frame(self.root)
        self.callback = MagicMock()

        # Create mock GPUs
        self.mock_gpu1 = MagicMock(spec=GPU)
        self.mock_gpu1.short_name = "GeForce RTX 3080"
        self.mock_gpu2 = MagicMock(spec=GPU)
        self.mock_gpu2.short_name = "GeForce RTX 3070"
        self.gpus = [self.mock_gpu1, self.mock_gpu2]

        # Create the overclocking frame with the callback
        with patch("dualgpuopt.services.event_service.event_bus.subscribe"):
            self.oc_frame = OverclockingFrame(
                self.parent, self.gpus, pad=10, on_status_change=self.callback
            )

    def tearDown(self):
        """Clean up after tests."""
        if self.root:
            self.root.destroy()

    def test_init(self):
        """Test initialization of the OverclockingFrame."""
        # Verify the overclocking frame was initialized properly
        self.assertIsInstance(self.oc_frame, OverclockingFrame)
        self.assertEqual(self.oc_frame.parent, self.parent)
        self.assertEqual(self.oc_frame.gpus, self.gpus)
        self.assertEqual(self.oc_frame.pad, 10)
        self.assertEqual(self.oc_frame.on_status_change, self.callback)

    def test_toggle_fan_control_auto(self):
        """Test toggling fan control to auto."""
        # Set auto_fan to True
        self.oc_frame.auto_fan_var.set(True)
        self.oc_frame._toggle_fan_control()

        # Verify that fan speed scale is disabled
        self.assertEqual(self.oc_frame.fan_speed_scale.cget("state"), "disabled")

        # Verify that fan speed label shows "Auto"
        self.assertEqual(self.oc_frame.fan_speed_label.cget("text"), "Auto")

    def test_toggle_fan_control_manual(self):
        """Test toggling fan control to manual."""
        # Set auto_fan to False and fan speed to 75
        self.oc_frame.auto_fan_var.set(False)
        self.oc_frame.fan_speed_var.set(75)
        self.oc_frame._toggle_fan_control()

        # Verify that fan speed scale is enabled
        self.assertEqual(self.oc_frame.fan_speed_scale.cget("state"), "normal")

        # Verify that fan speed label shows the percentage
        self.assertEqual(self.oc_frame.fan_speed_label.cget("text"), "75%")

    def test_update_label(self):
        """Test updating a label."""
        test_label = ttk.Label(self.parent)
        test_text = "Test Text"

        self.oc_frame._update_label(test_label, test_text)

        # Verify that the label text was updated
        self.assertEqual(test_label.cget("text"), test_text)

    @patch("dualgpuopt.services.config_service.config_service.get")
    def test_update_oc_controls(self, mock_get):
        """Test updating overclocking controls."""
        # Mock the config service get method to return GPU overclocking settings
        mock_get.return_value = {
            "0": {
                "core": 100,
                "memory": 500,
                "power": 110,
                "fan": 75,
                "auto_fan": False,
            }
        }

        # Set the selected GPU
        self.oc_frame.oc_gpu_var.set("GPU 0: GeForce RTX 3080")

        # Call the update method
        self.oc_frame._update_oc_controls()

        # Verify that the sliders were updated correctly
        self.assertEqual(self.oc_frame.core_clock_var.get(), 100)
        self.assertEqual(self.oc_frame.memory_clock_var.get(), 500)
        self.assertEqual(self.oc_frame.power_limit_var.get(), 110)
        self.assertEqual(self.oc_frame.fan_speed_var.get(), 75)
        self.assertEqual(self.oc_frame.auto_fan_var.get(), False)

        # Verify that the callback was called
        self.callback.assert_called_once_with("Loaded settings for GPU 0")

    @patch("dualgpuopt.services.config_service.config_service.get")
    @patch("dualgpuopt.commands.command_base.command_manager.execute")
    def test_apply_overclock(self, mock_execute, mock_get):
        """Test applying overclock settings."""
        # Mock the config service get method to return empty overclock settings
        mock_get.return_value = {}

        # Set the selected GPU and overclocking values
        self.oc_frame.oc_gpu_var.set("GPU 0: GeForce RTX 3080")
        self.oc_frame.core_clock_var.set(150)
        self.oc_frame.memory_clock_var.set(1000)
        self.oc_frame.power_limit_var.set(105)
        self.oc_frame.fan_speed_var.set(80)
        self.oc_frame.auto_fan_var.set(False)

        # Call the apply method
        self.oc_frame._apply_overclock()

        # Verify that command_manager.execute was called with appropriate command
        mock_execute.assert_called_once()

        # Verify that the callback was called
        self.callback.assert_called_once_with("Applying overclock to GPU 0...")

    @patch("dualgpuopt.services.config_service.config_service.config")
    @patch("dualgpuopt.services.config_service.config_service.save")
    @patch("dualgpuopt.services.event_service.event_bus.publish")
    def test_reset_overclock(self, mock_publish, mock_save, mock_config):
        """Test resetting overclock settings."""
        # Set up mock config with GPU overclock settings
        mock_config.__contains__.return_value = True
        mock_config.__getitem__.return_value = {"0": {}}

        # Set the selected GPU
        self.oc_frame.oc_gpu_var.set("GPU 0: GeForce RTX 3080")

        # Call the reset method
        self.oc_frame._reset_overclock()

        # Verify that the sliders were reset
        self.assertEqual(self.oc_frame.core_clock_var.get(), 0)
        self.assertEqual(self.oc_frame.memory_clock_var.get(), 0)
        self.assertEqual(self.oc_frame.power_limit_var.get(), 100)
        self.assertEqual(self.oc_frame.fan_speed_var.get(), 0)
        self.assertEqual(self.oc_frame.auto_fan_var.get(), True)

        # Verify that the config was saved
        mock_save.assert_called_once()

        # Verify that the event was published
        mock_publish.assert_called_once()

        # Verify that the callback was called
        self.callback.assert_called_once_with("Reset overclock for GPU 0")

    @patch("dualgpuopt.commands.command_base.command_manager.undo")
    def test_undo_last_command_success(self, mock_undo):
        """Test undoing the last command successfully."""
        # Set up mock to return True, indicating success
        mock_undo.return_value = True

        # Call the undo method
        self.oc_frame._undo_last_command()

        # Verify that command_manager.undo was called
        mock_undo.assert_called_once()

        # Verify that the callback was called
        self.callback.assert_called_once_with("Last operation undone")

    @patch("dualgpuopt.commands.command_base.command_manager.undo")
    @patch("tkinter.messagebox.showerror")
    def test_undo_last_command_failure(self, mock_showerror, mock_undo):
        """Test undoing the last command with failure."""
        # Set up mock to return False, indicating failure
        mock_undo.return_value = False

        # Call the undo method
        self.oc_frame._undo_last_command()

        # Verify that command_manager.undo was called
        mock_undo.assert_called_once()

        # Verify that messagebox.showerror was called
        mock_showerror.assert_called_once()

        # Verify that the callback was not called
        self.callback.assert_not_called()

    def test_get_current_settings(self):
        """Test getting current overclocking settings."""
        # Set the selected GPU and overclocking values
        self.oc_frame.oc_gpu_var.set("GPU 1: GeForce RTX 3070")
        self.oc_frame.core_clock_var.set(50)
        self.oc_frame.memory_clock_var.set(250)
        self.oc_frame.power_limit_var.set(95)
        self.oc_frame.fan_speed_var.set(60)
        self.oc_frame.auto_fan_var.set(True)

        # Get the current settings
        settings = self.oc_frame.get_current_settings()

        # Verify that the returned settings match the expected values
        self.assertEqual(
            settings,
            {
                "gpu_index": 1,
                "core_offset": 50,
                "memory_offset": 250,
                "power_limit": 95,
                "fan_speed": 60,
                "auto_fan": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
