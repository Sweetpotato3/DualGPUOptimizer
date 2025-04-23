"""
Unit tests for the AppearanceFrame component.
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
from dualgpuopt.gui.settings.appearance import AppearanceFrame


class TestAppearanceFrame(unittest.TestCase):
    """Test cases for the AppearanceFrame class."""

    def setUp(self):
        """Set up the test environment."""
        self.root = tk.Tk()
        self.parent = ttk.Frame(self.root)
        self.callback = MagicMock()

        # Create the appearance frame with the callback
        self.appearance_frame = AppearanceFrame(
            self.parent, pad=10, on_theme_change=self.callback
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.root:
            self.root.destroy()

    def test_init(self):
        """Test initialization of the AppearanceFrame."""
        # Verify the appearance frame was initialized properly
        self.assertIsInstance(self.appearance_frame, AppearanceFrame)
        self.assertEqual(self.appearance_frame.parent, self.parent)
        self.assertEqual(self.appearance_frame.pad, 10)
        self.assertEqual(self.appearance_frame.on_theme_change, self.callback)

    @patch("dualgpuopt.gui.theme_selector.ThemeSelector")
    def test_theme_selector_created(self, mock_theme_selector):
        """Test that the theme selector is created."""
        # Create a new appearance frame to trigger the component creation
        appearance_frame = AppearanceFrame(
            self.parent, pad=10, on_theme_change=self.callback
        )

        # Verify that the theme selector was created
        mock_theme_selector.assert_called_once()

    def test_on_theme_applied(self):
        """Test the theme applied callback."""
        test_theme = "dark_purple"
        self.appearance_frame._on_theme_applied(test_theme)

        # Verify that the callback was called with the expected message
        self.callback.assert_called_once_with(f"Theme changed to {test_theme}")

    @patch("dualgpuopt.gui.theme.set_theme")
    def test_apply_theme_from_preview(self, mock_set_theme):
        """Test applying a theme from a preview."""
        # Create a mock for the theme_selector
        self.appearance_frame.theme_selector = MagicMock()

        test_theme = "neon_dark"
        self.appearance_frame._apply_theme_from_preview(test_theme)

        # Verify that set_theme was called with the theme name
        self.appearance_frame.theme_selector.set_theme.assert_called_once_with(
            test_theme
        )

        # Verify that set_theme was called
        mock_set_theme.assert_called_once()

        # Verify that the callback was called with the expected message
        self.callback.assert_called_once_with(f"Theme changed to {test_theme}")

    @patch("dualgpuopt.services.config_service.config_service.set")
    @patch("dualgpuopt.services.event_service.event_bus.publish")
    @patch("tkinter.messagebox.showinfo")
    def test_apply_ttk_theme(self, mock_showinfo, mock_publish, mock_set):
        """Test applying a TTK theme."""
        # Create a mock for ttk_theme_var
        self.appearance_frame.ttk_theme_var = MagicMock()
        self.appearance_frame.ttk_theme_var.get.return_value = "clam"

        self.appearance_frame._apply_ttk_theme()

        # Verify that config_service.set was called with the TTK theme
        mock_set.assert_called_once_with("ttk_theme", "clam")

        # Verify that event_bus.publish was called with the TTK theme
        mock_publish.assert_called_once_with("config_changed:ttk_theme", "clam")

        # Verify that messagebox.showinfo was called
        mock_showinfo.assert_called_once()

        # Verify that the callback was called with the expected message
        self.callback.assert_called_once_with("TTK theme will apply on restart")

    def test_get_theme(self):
        """Test getting the current theme."""
        # Create a mock for the theme_selector
        self.appearance_frame.theme_selector = MagicMock()
        self.appearance_frame.theme_selector.get_theme.return_value = "light"

        theme = self.appearance_frame.get_theme()

        # Verify that the theme is as expected
        self.assertEqual(theme, "light")

        # Verify that get_theme was called on the theme selector
        self.appearance_frame.theme_selector.get_theme.assert_called_once()

    def test_get_ttk_theme_with_var(self):
        """Test getting the TTK theme when ttk_theme_var exists."""
        # Create a mock for ttk_theme_var
        self.appearance_frame.ttk_theme_var = MagicMock()
        self.appearance_frame.ttk_theme_var.get.return_value = "clam"

        ttk_theme = self.appearance_frame.get_ttk_theme()

        # Verify that the TTK theme is as expected
        self.assertEqual(ttk_theme, "clam")

        # Verify that get was called on ttk_theme_var
        self.appearance_frame.ttk_theme_var.get.assert_called_once()

    def test_get_ttk_theme_without_var(self):
        """Test getting the TTK theme when ttk_theme_var doesn't exist."""
        # Remove ttk_theme_var attribute if it exists
        if hasattr(self.appearance_frame, "ttk_theme_var"):
            delattr(self.appearance_frame, "ttk_theme_var")

        ttk_theme = self.appearance_frame.get_ttk_theme()

        # Verify that an empty string is returned
        self.assertEqual(ttk_theme, "")


if __name__ == "__main__":
    unittest.main()
