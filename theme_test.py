"""
Direct test of theme module by importing directly from files
"""
import sys
import os
import importlib.util
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ThemeDirectTest")

def import_from_path(module_name, file_path):
    """Import a module directly from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Base directory
base_dir = Path(__file__).resolve().parent
theme_dir = base_dir / "dualgpuopt" / "gui" / "theme"

# Import modules directly
try:
    logger.info(f"Importing modules from {theme_dir}...")

    # Import colors module
    colors_path = theme_dir / "colors.py"
    colors = import_from_path("theme_colors", str(colors_path))

    # Import dpi module
    dpi_path = theme_dir / "dpi.py"
    dpi = import_from_path("theme_dpi", str(dpi_path))

    # Import core module
    core_path = theme_dir / "core.py"
    core = import_from_path("theme_core", str(core_path))

    logger.info("All modules imported successfully")

    # Test functionality
    logger.info("\nTesting module functionality:")

    # Colors module
    logger.info("\nColors Module:")
    logger.info(f"Available themes: {', '.join(colors.AVAILABLE_THEMES.keys())}")
    logger.info(f"Dark purple background: {colors.THEME_DARK_PURPLE['bg']}")
    logger.info(f"Light theme background: {colors.THEME_LIGHT['bg']}")
    logger.info(f"Current theme background: {colors.current_theme['bg']}")

    # DPI module
    logger.info("\nDPI Module:")
    logger.info(f"Font scale: {dpi.FONT_SCALE}")
    logger.info(f"Default font size: {dpi.DEFAULT_FONT_SIZE}")
    logger.info(f"Scaled font size (12): {dpi.scale_font_size(12)}")

    # Core module
    logger.info("\nCore Module:")
    logger.info(f"Theme path: {core.get_theme_path()}")

    logger.info("\nAll tests PASSED!")

except Exception as e:
    logger.error(f"Test failed: {e}")
    raise