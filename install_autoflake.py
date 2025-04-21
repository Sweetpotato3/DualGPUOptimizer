#!/usr/bin/env python3
"""
Helper script to install autoflake in the current Python environment.
"""
import subprocess
import sys

def main():
    print("Installing autoflake for pre-commit hooks...")
    
    try:
        # Try to import autoflake to check if it's already installed
        import autoflake
        print("autoflake is already installed!")
        return 0
    except ImportError:
        # Install autoflake if not already installed
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "autoflake"], check=True)
            print("autoflake successfully installed!")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"Error installing autoflake: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main())