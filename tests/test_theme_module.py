"""
Tests for the Theme module
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path so we can import directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock tkinter before importing the theme module
sys.modules['ttkthemes'] = MagicMock()
sys.modules['ttkbootstrap'] = MagicMock()

# Now import the module to be tested
from dualgpuopt.gui import theme

class TestThemeColors(unittest.TestCase):
    """Tests for theme color functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Cache the original themes
        self.original_themes = theme.colors.THEMES.copy()

        # Create a test theme for testing
        theme.colors.THEMES['test_theme'] = {
            'bg': '#111111',
            'fg': '#EEEEEE',
            'accent': '#3366CC',
            'success': '#33CC33',
            'warning': '#FFCC00',
            'error': '#CC3333',
            'button': '#444444',
            'button_hover': '#666666',
            'inactive': '#888888',
        }

    def tearDown(self):
        """Tear down test fixtures"""
        # Restore original themes
        theme.colors.THEMES = self.original_themes

    def test_get_theme_colors(self):
        """Test get_theme_colors function"""
        colors = theme.colors.get_theme_colors('test_theme')

        # Check that all expected colors are present
        self.assertEqual(colors['bg'], '#111111')
        self.assertEqual(colors['fg'], '#EEEEEE')
        self.assertEqual(colors['accent'], '#3366CC')
        self.assertEqual(colors['success'], '#33CC33')
        self.assertEqual(colors['warning'], '#FFCC00')
        self.assertEqual(colors['error'], '#CC3333')

        # Test with nonexistent theme
        with self.assertRaises(ValueError):
            theme.colors.get_theme_colors('nonexistent_theme')

    def test_is_valid_theme(self):
        """Test is_valid_theme function"""
        # Test with valid themes
        self.assertTrue(theme.colors.is_valid_theme('test_theme'))
        self.assertTrue(theme.colors.is_valid_theme('dark'))

        # Test with invalid theme
        self.assertFalse(theme.colors.is_valid_theme('nonexistent_theme'))

    def test_get_available_themes(self):
        """Test get_available_themes function"""
        themes = theme.colors.get_available_themes()

        # Check that our test theme is included
        self.assertIn('test_theme', themes)

        # Should always have at least dark and light themes
        self.assertIn('dark', themes)
        self.assertIn('light', themes)

class TestThemeDPI(unittest.TestCase):
    """Tests for theme DPI functionality"""

    def test_scale_size(self):
        """Test scale_size function"""
        # Test with different DPI scales
        with patch('dualgpuopt.gui.theme.dpi.get_dpi_scale', return_value=1.0):
            self.assertEqual(theme.dpi.scale_size(10), 10)
            self.assertEqual(theme.dpi.scale_size(20), 20)

        with patch('dualgpuopt.gui.theme.dpi.get_dpi_scale', return_value=1.5):
            self.assertEqual(theme.dpi.scale_size(10), 15)
            self.assertEqual(theme.dpi.scale_size(20), 30)

        with patch('dualgpuopt.gui.theme.dpi.get_dpi_scale', return_value=2.0):
            self.assertEqual(theme.dpi.scale_size(10), 20)
            self.assertEqual(theme.dpi.scale_size(20), 40)

    def test_get_font_size(self):
        """Test get_font_size function"""
        # Test with different DPI scales
        with patch('dualgpuopt.gui.theme.dpi.get_dpi_scale', return_value=1.0):
            self.assertEqual(theme.dpi.get_font_size('normal'), 10)
            self.assertEqual(theme.dpi.get_font_size('small'), 8)
            self.assertEqual(theme.dpi.get_font_size('large'), 12)

        with patch('dualgpuopt.gui.theme.dpi.get_dpi_scale', return_value=1.5):
            self.assertEqual(theme.dpi.get_font_size('normal'), 15)
            self.assertEqual(theme.dpi.get_font_size('small'), 12)
            self.assertEqual(theme.dpi.get_font_size('large'), 18)

class TestThemeStyling(unittest.TestCase):
    """Tests for theme styling functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock ttk.Style
        self.mock_style = MagicMock()
        self.style_patcher = patch('tkinter.ttk.Style', return_value=self.mock_style)
        self.style_patcher.start()

        # Mock Tk root
        self.mock_root = MagicMock()
        self.tk_patcher = patch('tkinter.Tk', return_value=self.mock_root)
        self.tk_patcher.start()

    def tearDown(self):
        """Tear down test fixtures"""
        self.style_patcher.stop()
        self.tk_patcher.stop()

    def test_configure_ttk_style(self):
        """Test configure_ttk_style function"""
        # Create a mock style
        mock_style = MagicMock()

        # Test with a theme
        theme.styling.configure_ttk_style(mock_style, 'dark')

        # Should call configure and map methods
        self.assertTrue(mock_style.configure.called)
        self.assertTrue(mock_style.map.called)

    def test_apply_widget_styles(self):
        """Test apply_widget_styles function"""
        # Create mock widgets
        mock_button = MagicMock()
        mock_label = MagicMock()
        mock_entry = MagicMock()

        # Test with widgets
        widgets = {'button': mock_button, 'label': mock_label, 'entry': mock_entry}
        theme.styling.apply_widget_styles(widgets, 'dark')

        # Should configure widgets
        self.assertTrue(mock_button.configure.called)
        self.assertTrue(mock_label.configure.called)
        self.assertTrue(mock_entry.configure.called)

class TestThemeCore(unittest.TestCase):
    """Tests for core theme functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock ttk.Style
        self.mock_style = MagicMock()
        self.style_patcher = patch('tkinter.ttk.Style', return_value=self.mock_style)
        self.style_patcher.start()

        # Mock configure_ttk_style function
        self.configure_patcher = patch('dualgpuopt.gui.theme.styling.configure_ttk_style')
        self.mock_configure = self.configure_patcher.start()

    def tearDown(self):
        """Tear down test fixtures"""
        self.style_patcher.stop()
        self.configure_patcher.stop()

    @patch('dualgpuopt.gui.theme.core.styling.configure_ttk_style')
    def test_apply_theme(self, mock_configure_style):
        """Test apply_theme function"""
        # Mock root and style
        mock_root = MagicMock()
        mock_style = MagicMock()

        # Test theme application
        theme.core.apply_theme(mock_root, 'dark', mock_style)

        # Should configure style and root
        mock_configure_style.assert_called_once()
        self.assertTrue(mock_root.configure.called)

    @patch('dualgpuopt.gui.theme.core.colors.get_theme_colors')
    def test_get_themed_widget_colors(self, mock_get_colors):
        """Test get_themed_widget_colors function"""
        # Mock theme colors
        mock_get_colors.return_value = {
            'bg': '#111111',
            'fg': '#EEEEEE',
            'accent': '#3366CC',
            'success': '#33CC33',
            'warning': '#FFCC00',
            'error': '#CC3333',
        }

        # Test getting widget colors
        colors = theme.core.get_themed_widget_colors('dark')

        # Should retrieve colors and convert to widget-specific format
        mock_get_colors.assert_called_once_with('dark')
        self.assertIn('button', colors)
        self.assertIn('label', colors)
        self.assertIn('entry', colors)

class TestThemeCompatibility(unittest.TestCase):
    """Tests for theme compatibility module"""

    @patch('dualgpuopt.gui.theme.compatibility.load_ttkbootstrap')
    @patch('dualgpuopt.gui.theme.compatibility.load_ttkthemes')
    def test_setup_theme_compatibility(self, mock_load_ttkthemes, mock_load_ttkbootstrap):
        """Test setup_theme_compatibility function"""
        # Mock style
        mock_style = MagicMock()

        # Test compatibility setup
        theme.compatibility.setup_theme_compatibility(mock_style)

        # Should attempt to load both compatibility modules
        mock_load_ttkthemes.assert_called_once_with(mock_style)
        mock_load_ttkbootstrap.assert_called_once_with(mock_style)

if __name__ == "__main__":
    unittest.main()