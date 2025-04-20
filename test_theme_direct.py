"""
Direct test of theme module components without application initialization
"""
import sys
import logging
from pathlib import Path

# Configure logging with timestamp and level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ThemeDirectTest")

def test_colors_module():
    """Test the colors module"""
    try:
        logger.info("Testing theme colors module...")
        
        # Direct import from colors.py
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from dualgpuopt.gui.theme.colors import (
            current_theme, 
            AVAILABLE_THEMES, 
            THEME_DARK_PURPLE,
            get_theme_by_name,
            update_current_theme
        )
        
        # Verify the module is working
        logger.info(f"Current theme has {len(current_theme)} properties")
        logger.info(f"Available themes: {', '.join(AVAILABLE_THEMES.keys())}")
        
        # Test theme selection
        logger.info("Testing theme selection...")
        theme = get_theme_by_name("light")
        logger.info(f"Light theme background: {theme['bg']}")
        
        # Test theme updating
        logger.info("Testing theme updating...")
        update_current_theme("neon_dark")
        logger.info(f"Current theme background: {current_theme['bg']}")
        
        return True
    except Exception as e:
        logger.error(f"Colors module test failed: {e}")
        return False

def test_dpi_module():
    """Test the DPI module"""
    try:
        logger.info("Testing theme DPI module...")
        
        # Direct import from dpi.py
        from dualgpuopt.gui.theme.dpi import (
            FONT_SCALE,
            DEFAULT_FONT_SIZE,
            scale_font_size
        )
        
        # Verify the module is working
        logger.info(f"Font scale: {FONT_SCALE}")
        logger.info(f"Default font size: {DEFAULT_FONT_SIZE}")
        logger.info(f"Scaled font size (12): {scale_font_size(12)}")
        
        return True
    except Exception as e:
        logger.error(f"DPI module test failed: {e}")
        return False

def test_core_module():
    """Test the core module"""
    try:
        logger.info("Testing theme core module...")
        
        # Direct import from core.py
        from dualgpuopt.gui.theme.core import (
            get_theme_path
        )
        
        # Verify the module is working
        logger.info(f"Theme path: {get_theme_path()}")
        
        return True
    except Exception as e:
        logger.error(f"Core module test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting direct theme module tests...")
    
    # Run tests
    colors_result = test_colors_module()
    dpi_result = test_dpi_module()
    core_result = test_core_module()
    
    # Report results
    logger.info("\nTest Results:")
    logger.info(f"Colors Module: {'PASSED' if colors_result else 'FAILED'}")
    logger.info(f"DPI Module: {'PASSED' if dpi_result else 'FAILED'}")
    logger.info(f"Core Module: {'PASSED' if core_result else 'FAILED'}")
    
    # Overall result
    if colors_result and dpi_result and core_result:
        logger.info("\nAll tests PASSED!")
    else:
        logger.error("\nSome tests FAILED!")
        sys.exit(1) 