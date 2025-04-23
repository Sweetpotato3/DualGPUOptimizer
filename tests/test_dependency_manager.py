import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to make dualgpuopt importable
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDependencyManager(unittest.TestCase):
    """Test cases for dependency management system"""

    def setUp(self):
        """Set up test environment, reset cached modules"""
        # Clear any modules loaded by previous tests
        modules_to_clear = [
            "dualgpuopt.dependency_manager",
            "dualgpuopt.ui.compat",
            "dualgpuopt.ui.chat_compat",
        ]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

    @patch("importlib.util.find_spec")
    def test_check_dependency(self, mock_find_spec):
        """Test dependency checking with mocked find_spec"""
        # Import the module under test
        from dualgpuopt.dependency_manager import check_dependency

        # Configure mock to return True for 'numpy', False for 'missing_package'
        def side_effect(name):
            return MagicMock() if name == "numpy" else None

        mock_find_spec.side_effect = side_effect

        # Test with tkinter separately since it has special handling
        with patch("dualgpuopt.dependency_manager.importlib.util.find_spec") as mock_spec:
            with patch("importlib.__import__") as mock_import:
                mock_import.return_value = MagicMock()
                mock_spec.return_value = MagicMock()

                # Should return True when tkinter can be imported
                self.assertTrue(check_dependency("tkinter"))

                # Should return False when tkinter import raises ImportError
                mock_import.side_effect = ImportError
                self.assertFalse(check_dependency("tkinter"))

        # Test normal dependency checking
        self.assertTrue(check_dependency("numpy"))
        self.assertFalse(check_dependency("missing_package"))

    @patch("dualgpuopt.dependency_manager.check_dependency")
    def test_get_missing_dependencies(self, mock_check_dependency):
        """Test getting missing dependencies with mocked check_dependency"""
        # Import the module under test
        from dualgpuopt.dependency_manager import get_missing_dependencies

        # Configure mock to return True for some dependencies, False for others
        def side_effect(name):
            # Only tkinter, pynvml, and numpy are available
            return name in ["tkinter", "pynvml", "numpy"]

        mock_check_dependency.side_effect = side_effect

        # Get missing dependencies
        missing = get_missing_dependencies()

        # Verify results
        self.assertNotIn("required", missing, "Required dependencies should be present")
        self.assertIn("ui", missing, "UI dependencies should be missing")
        self.assertIn("chat", missing, "Chat dependencies should be missing")
        self.assertIn("ml", missing, "ML dependencies should be missing")

        # Check that specific packages are listed as missing
        self.assertIn("ttkbootstrap", missing["ui"])
        self.assertIn("requests", missing["chat"])
        self.assertIn("torch", missing["ml"])

    @patch("dualgpuopt.dependency_manager.check_dependency")
    def test_get_installation_commands(self, mock_check_dependency):
        """Test generating installation commands with mocked dependencies"""
        # Import the module under test
        from dualgpuopt.dependency_manager import (
            get_installation_commands,
            get_missing_dependencies,
        )

        # Configure mock to return False for all dependencies
        mock_check_dependency.return_value = False

        # Get missing dependencies
        missing = get_missing_dependencies()

        # Test generating commands for all categories
        commands = get_installation_commands(missing, {"required", "core", "ui", "chat", "ml"})

        # Verify that commands are generated for each category
        command_text = " ".join(commands)
        self.assertIn("pynvml", command_text)
        self.assertIn("ttkbootstrap", command_text)
        self.assertIn("requests", command_text)
        self.assertIn("torch", command_text)

        # Test generating commands for only core dependencies
        commands = get_installation_commands(missing, {"required", "core"})

        # Verify that only core commands are generated
        command_text = " ".join(commands)
        self.assertIn("pynvml", command_text)
        self.assertNotIn("ttkbootstrap", command_text)
        self.assertNotIn("requests", command_text)
        self.assertNotIn("torch", command_text)

    @patch("subprocess.run")
    @patch("dualgpuopt.dependency_manager.get_missing_dependencies")
    def test_install_dependencies(self, mock_get_missing, mock_subprocess_run):
        """Test installing dependencies with mocked subprocess and missing deps"""
        # Import the module under test
        import argparse

        from dualgpuopt.dependency_manager import install_dependencies

        # Configure mocks
        mock_get_missing.return_value = {
            "core": ["pynvml", "numpy"],
            "ui": ["ttkbootstrap"],
        }

        mock_subprocess_run.return_value = MagicMock(returncode=0)

        # Create args namespace
        args = argparse.Namespace(
            core_only=True,
            ui_only=False,
            chat_only=False,
            ml_only=False,
            yes=True,
            verbose=False,
        )

        # Call the function
        result = install_dependencies(args)

        # Verify subprocess was called with correct pip command
        command_called = mock_subprocess_run.call_args[0][0]
        self.assertIn("pip install", command_called)
        self.assertIn("pynvml", command_called)
        self.assertIn("numpy", command_called)
        self.assertEqual(result, 0, "Should return success status code")

        # Test failure case
        mock_subprocess_run.return_value = MagicMock(returncode=1)
        result = install_dependencies(args)
        self.assertEqual(result, 1, "Should return failure status code")

    @patch("importlib.util.find_spec")
    def test_dynamic_importer(self, mock_find_spec):
        """Test dynamic importer with mocked imports"""

        # Configure mock to selectively return specs
        def side_effect(name):
            if name in ["tkinter", "pynvml", "numpy"]:
                return MagicMock()
            return None

        mock_find_spec.side_effect = side_effect

        # Import with dependency statuses mocked
        with patch("dualgpuopt.dependency_manager.dependency_status") as mock_status:
            # Test with ttkbootstrap available
            mock_status.get.return_value = True

            from dualgpuopt.dependency_manager import DynamicImporter

            # Test UI import with ttkbootstrap available
            with patch("importlib.import_module") as mock_import:
                mock_import.return_value = MagicMock()
                ui_module = DynamicImporter.import_ui()
                self.assertIsNotNone(ui_module)
                mock_import.assert_called_with("ttkbootstrap")

            # Test UI import without ttkbootstrap
            mock_status.get.return_value = False
            with patch("importlib.import_module") as mock_import:
                mock_import.return_value = MagicMock()
                ui_module = DynamicImporter.import_ui()
                self.assertIsNotNone(ui_module)
                mock_import.assert_called_with("tkinter.ttk")


if __name__ == "__main__":
    unittest.main()
