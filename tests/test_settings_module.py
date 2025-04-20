"""
Tests for the Settings module
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import json
import tempfile

# Add parent directory to path so we can import directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock tkinter before importing GUI modules
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['ttkbootstrap'] = MagicMock()

# Now import the modules to be tested
from dualgpuopt.gui.settings import appearance, overclocking, application_settings

class TestAppearanceSettings(unittest.TestCase):
    """Tests for the Appearance Settings module"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temp file for settings
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # Mock the settings file path
        self.patcher = patch('dualgpuopt.gui.settings.appearance.SETTINGS_FILE', self.temp_file.name)
        self.patcher.start()
        
        # Sample settings
        self.sample_settings = {
            'theme': 'dark',
            'ui_scale': 1.0,
            'font_size': 10
        }
        
        # Write sample settings to the file
        with open(self.temp_file.name, 'w') as f:
            json.dump(self.sample_settings, f)
        
        # Create settings instance
        self.appearance_settings = appearance.AppearanceSettings()
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.patcher.stop()
        os.unlink(self.temp_file.name)
    
    def test_load_settings(self):
        """Test load_settings method"""
        # Load settings
        settings = self.appearance_settings.load_settings()
        
        # Should match the sample settings
        self.assertEqual(settings['theme'], self.sample_settings['theme'])
        self.assertEqual(settings['ui_scale'], self.sample_settings['ui_scale'])
        self.assertEqual(settings['font_size'], self.sample_settings['font_size'])
    
    def test_save_settings(self):
        """Test save_settings method"""
        # Modify settings
        new_settings = {
            'theme': 'light',
            'ui_scale': 1.2,
            'font_size': 12
        }
        
        # Save settings
        self.appearance_settings.save_settings(new_settings)
        
        # Load settings to verify
        loaded_settings = self.appearance_settings.load_settings()
        
        # Should match the new settings
        self.assertEqual(loaded_settings['theme'], new_settings['theme'])
        self.assertEqual(loaded_settings['ui_scale'], new_settings['ui_scale'])
        self.assertEqual(loaded_settings['font_size'], new_settings['font_size'])
    
    def test_get_available_themes(self):
        """Test get_available_themes method"""
        # Get available themes
        themes = self.appearance_settings.get_available_themes()
        
        # Should include at least dark and light themes
        self.assertIn('dark', themes)
        self.assertIn('light', themes)
    
    def test_apply_theme(self):
        """Test apply_theme method"""
        # Mock necessary components
        mock_root = MagicMock()
        mock_style = MagicMock()
        
        # Test applying theme
        with patch('dualgpuopt.gui.settings.appearance.apply_theme') as mock_apply_theme:
            self.appearance_settings.apply_theme('dark', mock_root, mock_style)
            
            # Should call apply_theme once
            mock_apply_theme.assert_called_once_with(mock_root, 'dark', mock_style)

class TestOverclockingSettings(unittest.TestCase):
    """Tests for the Overclocking Settings module"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temp file for settings
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # Mock the settings file path
        self.patcher = patch('dualgpuopt.gui.settings.overclocking.SETTINGS_FILE', self.temp_file.name)
        self.patcher.start()
        
        # Mock GPU info
        self.gpu_info_patcher = patch('dualgpuopt.gui.settings.overclocking.gpu_info')
        self.mock_gpu_info = self.gpu_info_patcher.start()
        self.mock_gpu_info.query.return_value = [
            {'id': 0, 'name': 'Test GPU 0', 'clock_sm': 1000, 'clock_memory': 800},
            {'id': 1, 'name': 'Test GPU 1', 'clock_sm': 1200, 'clock_memory': 900}
        ]
        
        # Sample settings
        self.sample_settings = {
            'gpu_0': {
                'core_clock_offset': 100,
                'memory_clock_offset': 200,
                'power_limit': 250,
                'fan_speed': 70
            },
            'gpu_1': {
                'core_clock_offset': 50,
                'memory_clock_offset': 100,
                'power_limit': 200,
                'fan_speed': 60
            },
            'auto_apply': True
        }
        
        # Write sample settings to the file
        with open(self.temp_file.name, 'w') as f:
            json.dump(self.sample_settings, f)
        
        # Create settings instance
        self.overclocking_settings = overclocking.OverclockingSettings()
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.patcher.stop()
        self.gpu_info_patcher.stop()
        os.unlink(self.temp_file.name)
    
    def test_load_settings(self):
        """Test load_settings method"""
        # Load settings
        settings = self.overclocking_settings.load_settings()
        
        # Should match the sample settings
        self.assertEqual(settings['gpu_0']['core_clock_offset'], self.sample_settings['gpu_0']['core_clock_offset'])
        self.assertEqual(settings['gpu_1']['memory_clock_offset'], self.sample_settings['gpu_1']['memory_clock_offset'])
        self.assertEqual(settings['auto_apply'], self.sample_settings['auto_apply'])
    
    def test_save_settings(self):
        """Test save_settings method"""
        # Modify settings
        new_settings = {
            'gpu_0': {
                'core_clock_offset': 150,
                'memory_clock_offset': 250,
                'power_limit': 300,
                'fan_speed': 75
            },
            'gpu_1': {
                'core_clock_offset': 100,
                'memory_clock_offset': 150,
                'power_limit': 220,
                'fan_speed': 65
            },
            'auto_apply': False
        }
        
        # Save settings
        self.overclocking_settings.save_settings(new_settings)
        
        # Load settings to verify
        loaded_settings = self.overclocking_settings.load_settings()
        
        # Should match the new settings
        self.assertEqual(loaded_settings['gpu_0']['core_clock_offset'], new_settings['gpu_0']['core_clock_offset'])
        self.assertEqual(loaded_settings['gpu_1']['memory_clock_offset'], new_settings['gpu_1']['memory_clock_offset'])
        self.assertEqual(loaded_settings['auto_apply'], new_settings['auto_apply'])
    
    @patch('dualgpuopt.gui.settings.overclocking.subprocess.run')
    def test_apply_overclocking(self, mock_run):
        """Test apply_overclocking method"""
        # Mock subprocess run to return a successful result
        mock_run.return_value = MagicMock(returncode=0)
        
        # Apply overclocking
        result = self.overclocking_settings.apply_overclocking({
            'gpu_id': 0,
            'core_clock_offset': 100,
            'memory_clock_offset': 200,
            'power_limit': 250,
            'fan_speed': 70
        })
        
        # Should call subprocess.run for each setting
        self.assertEqual(mock_run.call_count, 4)  # 4 settings to apply
        
        # Should return True for successful application
        self.assertTrue(result)
        
        # Test error handling
        mock_run.return_value = MagicMock(returncode=1)  # Command failed
        
        # Apply overclocking with failing command
        result = self.overclocking_settings.apply_overclocking({
            'gpu_id': 0,
            'core_clock_offset': 100,
            'memory_clock_offset': 200,
            'power_limit': 250,
            'fan_speed': 70
        })
        
        # Should return False for failed application
        self.assertFalse(result)

class TestApplicationSettings(unittest.TestCase):
    """Tests for the Application Settings module"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temp file for settings
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # Mock the settings file path
        self.patcher = patch('dualgpuopt.gui.settings.application_settings.SETTINGS_FILE', self.temp_file.name)
        self.patcher.start()
        
        # Sample settings
        self.sample_settings = {
            'auto_start': True,
            'minimize_to_tray': True,
            'log_level': 'INFO',
            'max_recent_models': 10,
            'thread_count': 4
        }
        
        # Write sample settings to the file
        with open(self.temp_file.name, 'w') as f:
            json.dump(self.sample_settings, f)
        
        # Create settings instance
        self.app_settings = application_settings.ApplicationSettings()
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.patcher.stop()
        os.unlink(self.temp_file.name)
    
    def test_load_settings(self):
        """Test load_settings method"""
        # Load settings
        settings = self.app_settings.load_settings()
        
        # Should match the sample settings
        self.assertEqual(settings['auto_start'], self.sample_settings['auto_start'])
        self.assertEqual(settings['minimize_to_tray'], self.sample_settings['minimize_to_tray'])
        self.assertEqual(settings['log_level'], self.sample_settings['log_level'])
        self.assertEqual(settings['max_recent_models'], self.sample_settings['max_recent_models'])
        self.assertEqual(settings['thread_count'], self.sample_settings['thread_count'])
    
    def test_save_settings(self):
        """Test save_settings method"""
        # Modify settings
        new_settings = {
            'auto_start': False,
            'minimize_to_tray': False,
            'log_level': 'DEBUG',
            'max_recent_models': 5,
            'thread_count': 8
        }
        
        # Save settings
        self.app_settings.save_settings(new_settings)
        
        # Load settings to verify
        loaded_settings = self.app_settings.load_settings()
        
        # Should match the new settings
        self.assertEqual(loaded_settings['auto_start'], new_settings['auto_start'])
        self.assertEqual(loaded_settings['minimize_to_tray'], new_settings['minimize_to_tray'])
        self.assertEqual(loaded_settings['log_level'], new_settings['log_level'])
        self.assertEqual(loaded_settings['max_recent_models'], new_settings['max_recent_models'])
        self.assertEqual(loaded_settings['thread_count'], new_settings['thread_count'])
    
    def test_get_available_log_levels(self):
        """Test get_available_log_levels method"""
        # Get available log levels
        log_levels = self.app_settings.get_available_log_levels()
        
        # Should include standard Python log levels
        self.assertIn('DEBUG', log_levels)
        self.assertIn('INFO', log_levels)
        self.assertIn('WARNING', log_levels)
        self.assertIn('ERROR', log_levels)
        self.assertIn('CRITICAL', log_levels)
    
    @patch('dualgpuopt.gui.settings.application_settings.os.cpu_count')
    def test_get_recommended_thread_count(self, mock_cpu_count):
        """Test get_recommended_thread_count method"""
        # Mock CPU count
        mock_cpu_count.return_value = 8
        
        # Get recommended thread count
        thread_count = self.app_settings.get_recommended_thread_count()
        
        # Should return 75% of available cores, rounded down
        self.assertEqual(thread_count, 6)
        
        # Test with None (which can happen if os.cpu_count fails)
        mock_cpu_count.return_value = None
        
        # Should return default value
        thread_count = self.app_settings.get_recommended_thread_count()
        self.assertEqual(thread_count, 4)

if __name__ == "__main__":
    unittest.main() 