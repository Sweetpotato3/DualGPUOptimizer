"""
Bundle smoke test for DualGPUOptimizer
Verifies DLLs are loaded correctly and constants.py is accessible
"""
import os
import sys
import unittest
from pathlib import Path


class BundleTest(unittest.TestCase):
    """Test PyInstaller bundle integrity"""
    
    def test_meipass_exists(self):
        """Verify _MEIPASS exists when run from bundle"""
        if getattr(sys, 'frozen', False):
            self.assertTrue(hasattr(sys, '_MEIPASS'))
            meipass = Path(sys._MEIPASS)
            self.assertTrue(meipass.exists())
    
    def test_cuda_dlls_present(self):
        """Verify CUDA DLLs are present when packaged"""
        if getattr(sys, 'frozen', False):
            meipass = Path(sys._MEIPASS)
            
            # Check for at least one CUDA DLL
            cuda_dlls = list(meipass.glob("cublas*.dll")) + list(meipass.glob("cudart*.dll"))
            self.assertTrue(len(cuda_dlls) > 0, "No CUDA DLLs found in bundle")
    
    def test_gui_constants_importable(self):
        """Verify gui.constants can be imported"""
        try:
            from dualgpuopt.gui import constants
            self.assertTrue(hasattr(constants, 'GUI_VERSION'))
        except ImportError as e:
            self.fail(f"Failed to import dualgpuopt.gui.constants: {e}")


if __name__ == "__main__":
    unittest.main() 