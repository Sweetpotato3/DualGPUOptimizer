#!/usr/bin/env python
"""
Test runner for the settings module tests.
This will run all tests for the settings module components.
"""
import unittest
import sys
import os

# Add the parent directory to the path so we can import the tests package
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the test modules
from gui.test_settings_tab import TestSettingsTab
from gui.test_appearance_frame import TestAppearanceFrame
from gui.test_application_settings_frame import TestApplicationSettingsFrame
from gui.test_overclocking_frame import TestOverclockingFrame


def create_test_suite():
    """Create a test suite containing all settings tests."""
    test_suite = unittest.TestSuite()

    # Add test cases for settings module
    test_suite.addTest(unittest.makeSuite(TestSettingsTab))
    test_suite.addTest(unittest.makeSuite(TestAppearanceFrame))
    test_suite.addTest(unittest.makeSuite(TestApplicationSettingsFrame))
    test_suite.addTest(unittest.makeSuite(TestOverclockingFrame))

    return test_suite


if __name__ == "__main__":
    # Create and run the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    test_suite = create_test_suite()
    result = runner.run(test_suite)

    # Exit with a non-zero code if tests failed
    sys.exit(not result.wasSuccessful())