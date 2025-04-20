"""
Simple test script to verify the refactored theme module is working correctly
"""
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ThemeTest")

# Test direct imports from the theme package
try:
    logger.info("Testing imports from dualgpuopt.gui.theme...")

    from dualgpuopt.gui.theme.colors import (
        current_theme,
        AVAILABLE_THEMES,
        THEME_DARK_PURPLE
    )

    from dualgpuopt.gui.theme.dpi import (
        FONT_SCALE,
        DEFAULT_FONT_SIZE
    )

    from dualgpuopt.gui.theme.core import (
        get_theme_path
    )

    logger.info("Import test successful!")
    logger.info(f"Current theme has {len(current_theme)} properties")
    logger.info(f"Available themes: {', '.join(AVAILABLE_THEMES.keys())}")
    logger.info(f"Font scale: {FONT_SCALE}")
    logger.info(f"Default font size: {DEFAULT_FONT_SIZE}")
    logger.info(f"Theme path: {get_theme_path()}")

except ImportError as e:
    logger.error(f"Import test failed: {e}")

# Test backward compatibility imports
try:
    logger.info("\nTesting backward compatibility imports...")

    from dualgpuopt.gui.theme import (
        current_theme as original_current_theme,
        AVAILABLE_THEMES as original_AVAILABLE_THEMES
    )

    logger.info("Backward compatibility test successful!")
    logger.info(f"Original current theme has {len(original_current_theme)} properties")
    logger.info(f"Original available themes: {', '.join(original_AVAILABLE_THEMES.keys())}")

    # Verify the objects are the same
    logger.info(f"Current theme is the same object: {current_theme is original_current_theme}")
    logger.info(f"AVAILABLE_THEMES is the same object: {AVAILABLE_THEMES is original_AVAILABLE_THEMES}")

except ImportError as e:
    logger.error(f"Backward compatibility test failed: {e}")

logger.info("\nAll tests completed.")