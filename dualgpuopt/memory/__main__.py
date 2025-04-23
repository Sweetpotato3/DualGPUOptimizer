"""
Run the memory profiler as a standalone application for testing and debugging.
"""

import argparse
import logging
import os
import sys
import tkinter as tk
from tkinter import ttk

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Add parent directory to path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def main():
    """Main entry point for the memory profiler application"""
    parser = argparse.ArgumentParser(description="Memory Profiler for GPU memory usage")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without real GPU")
    args = parser.parse_args()

    # Enable mock mode if requested
    if args.mock:
        os.environ["DUALGPUOPT_MOCK_GPU"] = "1"
        os.environ["DUALGPUOPT_GPU_COUNT"] = "2"

    # Import our modules
    from dualgpuopt.gui.memory_profile_tab import MemoryProfileTab

    # Create the application
    root = tk.Tk()
    root.title("Memory Profiler")
    root.geometry("800x700")

    # Set up the main frame
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Create profile tab
    profile_tab = MemoryProfileTab(main_frame)
    profile_tab.pack(fill=tk.BOTH, expand=True)

    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    main()
