"""
Unit tests for the SettingsTab component.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the components to test
from dualgpuopt.gui.settings.settings_tab import SettingsTab
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.state_service import state_service
from dualgpuopt.gpu_info import GPU


class TestSettingsTab(unittest.TestCase):
    """Test cases for the SettingsTab class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.root = tk.Tk()
        self.parent = ttk.Frame(self.root)
        
        # Create mock GPUs
        self.mock_gpu1 = MagicMock(spec=GPU)
        self.mock_gpu1.short_name = "GeForce RTX 3080"
        self.mock_gpu2 = MagicMock(spec=GPU)
        self.mock_gpu2.short_name = "GeForce RTX 3070"
        self.gpus = [self.mock_gpu1, self.mock_gpu2]
        
        # Mock config_service
        self.mock_config = MagicMock()
        self.mock_config.get.return_value = {}
        self.mock_config.set.return_value = None
        self.mock_config.update.return_value = None
        
        # Mock state_service
        self.mock_state = MagicMock()
        
        # Create the settings tab with mocks
        self.settings_tab = SettingsTab(
            self.parent,
            gpus=self.gpus,
            config_service_instance=self.mock_config,
            state_service_instance=self.mock_state
        )
    
    def tearDown(self):
        """Clean up after tests."""
        if self.root:
            self.root.destroy()
    
    def test_init(self):
        """Test initialization of the SettingsTab."""
        # Verify the settings tab was initialized properly
        self.assertIsInstance(self.settings_tab, SettingsTab)
        self.assertEqual(self.settings_tab.parent, self.parent)
        self.assertEqual(self.settings_tab.gpus, self.gpus)
        self.assertEqual(self.settings_tab.config_service, self.mock_config)
        self.assertEqual(self.settings_tab.state_service, self.mock_state)
    
    @patch('dualgpuopt.gui.settings.appearance.AppearanceFrame')
    @patch('dualgpuopt.gui.settings.overclocking.OverclockingFrame')
    @patch('dualgpuopt.gui.settings.application_settings.ApplicationSettingsFrame')
    def test_components_created(self, mock_app_settings, mock_overclocking, mock_appearance):
        """Test that all required components are created."""
        # Create a new settings tab to trigger the component creation
        settings_tab = SettingsTab(
            self.parent,
            gpus=self.gpus,
            config_service_instance=self.mock_config,
            state_service_instance=self.mock_state
        )
        
        # Verify that all components were created
        mock_appearance.assert_called_once()
        mock_overclocking.assert_called_once()
        mock_app_settings.assert_called_once()
    
    def test_update_status(self):
        """Test updating the status message."""
        test_message = "Test status message"
        self.settings_tab._update_status(test_message)
        self.assertEqual(self.settings_tab.status_var.get(), test_message)
    
    @patch('tkinter.messagebox.askyesno', return_value=True)
    @patch('dualgpuopt.gui.theme.set_theme')
    def test_reset_all_settings(self, mock_set_theme, mock_askyesno):
        """Test resetting all settings to defaults."""
        # Create a mock for the application_settings_frame
        self.settings_tab.application_settings_frame = MagicMock()
        
        # Call the reset method
        self.settings_tab._reset_all_settings()
        
        # Verify that apply_settings was called with the default values
        self.settings_tab.application_settings_frame.apply_settings.assert_called_once()
        
        # Verify that the theme was reset
        mock_set_theme.assert_called_once()
        
        # Verify that messagebox.askyesno was called
        mock_askyesno.assert_called_once()
    
    def test_save_all_settings(self):
        """Test saving all settings."""
        # Create mocks for the components
        self.settings_tab.application_settings_frame = MagicMock()
        self.settings_tab.application_settings_frame.get_settings.return_value = {
            "start_minimized": False,
            "idle_alerts": True,
            "idle_threshold": 30,
            "idle_time": 5
        }
        
        self.settings_tab.appearance_frame = MagicMock()
        self.settings_tab.appearance_frame.get_theme.return_value = "dark_purple"
        self.settings_tab.appearance_frame.get_ttk_theme.return_value = "clam"
        
        # Mock the event_bus.publish method
        with patch('dualgpuopt.services.event_service.event_bus.publish') as mock_publish:
            # Mock the messagebox.showinfo method
            with patch('tkinter.messagebox.showinfo') as mock_showinfo:
                # Call the save method
                self.settings_tab._save_all_settings()
                
                # Verify that update was called with the correct config
                self.mock_config.update.assert_called_once()
                
                # Verify that the event was published
                mock_publish.assert_called_once_with("settings_saved")
                
                # Verify that messagebox.showinfo was called
                mock_showinfo.assert_called_once()


if __name__ == '__main__':
    unittest.main() 