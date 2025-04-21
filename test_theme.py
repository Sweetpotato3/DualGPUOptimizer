"""
Test script for theme functionality in DualGPUOptimizer
"""
import sys
import logging
import pathlib
import tkinter as tk
from tkinter import ttk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ThemeTester")

# Make sure the directory structure exists
current_dir = pathlib.Path(__file__).parent.absolute()
print(f"Current directory: {current_dir}")

# Add the current directory to the path
sys.path.insert(0, str(current_dir))

# Create a services directory and config_service.py if they don't exist
def create_service_structure():
    """Create the service directory structure and basic config service"""
    services_dir = current_dir / "dualgpuopt" / "services"
    services_dir.mkdir(exist_ok=True, parents=True)

    # Create __init__.py
    init_file = services_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, "w") as f:
            f.write('"""Services package for DualGPUOptimizer."""\n\n__all__ = ["config_service", "event_service"]')

    # Create basic config_service.py if it doesn't exist
    config_file = services_dir / "config_service.py"
    if not config_file.exists():
        with open(config_file, "w") as f:
            config_content = '''"""
Configuration service for DualGPUOptimizer
"""
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("DualGPUOpt.ConfigService")

class ConfigService:
    """Service for managing application configuration"""

    def __init__(self):
        """Initialize config service with default values"""
        self.config = {
            "theme": "dark_purple",
            "gpu_layers": -1,
            "context_size": 4096,
            "thread_count": 8,
            "last_model_path": "",
            "gpu_split": "0.60,0.40"
        }

        # Config file path in user directory
        self.config_dir = Path.home() / ".dualgpuopt"
        self.config_file = self.config_dir / "config.json"

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)

        # Load configuration from file
        self.load()

    def load(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values
                    self.config.update(loaded_config)
                    logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
                logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def get(self, key, default=None):
        """Get a configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value and save

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        self.save()

# Singleton instance
config_service = ConfigService()
'''
            f.write(config_content)

# Create a simple theme test window
def run_theme_test():
    """Create a simple window to test themes"""

    # Create necessary files first
    create_service_structure()

    try:
        # Import our theme module
        from dualgpuopt.gui.theme import set_theme, apply_theme, toggle_theme, AVAILABLE_THEMES

        root = tk.Tk()
        root.title("Theme Tester")
        root.geometry("800x600")

        # Apply initial theme
        apply_theme(root)

        # Create a frame with some widgets
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add a heading
        heading = ttk.Label(main_frame, text="Theme Test Application", style="Heading.TLabel")
        heading.pack(pady=20)

        # Add some regular labels
        label1 = ttk.Label(main_frame, text="This is a regular label")
        label1.pack(pady=10)

        # Create a frame for buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        # Add buttons for each theme
        for theme_name in AVAILABLE_THEMES:
            def theme_changer(name=theme_name):
                set_theme(root, name)

            btn = ttk.Button(button_frame, text=f"Apply {theme_name} theme", command=theme_changer)
            btn.pack(side=tk.LEFT, padx=10)

        # Add a toggle button
        toggle_btn = ttk.Button(main_frame, text="Toggle Theme",
                               command=lambda: toggle_theme(root))
        toggle_btn.pack(pady=10)

        # Add an entry field
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(pady=20, fill=tk.X)

        entry_label = ttk.Label(entry_frame, text="Test Input:")
        entry_label.pack(side=tk.LEFT, padx=5)

        entry = ttk.Entry(entry_frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        entry.insert(0, "Sample text")

        # Add a notebook with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(pady=20, fill=tk.BOTH, expand=True)

        # Add tabs
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="Tab 1")

        tab1_content = ttk.Label(tab1, text="Content in Tab 1")
        tab1_content.pack(pady=20)

        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="Tab 2")

        tab2_content = ttk.Label(tab2, text="Content in Tab 2")
        tab2_content.pack(pady=20)

        # Debug info
        debug_frame = ttk.LabelFrame(main_frame, text="Debug Info")
        debug_frame.pack(pady=10, fill=tk.X)

        debug_text = tk.Text(debug_frame, height=5, width=60)
        debug_text.pack(pady=5, padx=5, fill=tk.BOTH)

        # Add some debug info
        debug_text.insert(tk.END, f"Current Python version: {sys.version}\n")
        debug_text.insert(tk.END, f"Tkinter version: {tk.TkVersion}\n")
        debug_text.insert(tk.END, f"Available themes: {list(AVAILABLE_THEMES.keys())}\n")

        # Start the main loop
        root.mainloop()

    except Exception as e:
        logger.error(f"Error in theme test: {e}", exc_info=True)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_theme_test()