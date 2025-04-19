"""
Main entry point for the DualGPUOptimizer.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.layout import Layout
from rich.text import Text

from dualgpuopt.gui import run_app
from dualgpuopt.logconfig import setup_logging
from dualgpuopt import gpu_info, optimizer, configio


# Initialize rich console
console = Console()


def cli_optimize(args: argparse.Namespace) -> int:
    """Run in CLI mode to generate optimization config."""
    # Setup logging
    logger = setup_logging(
        verbose=args.verbose,
        log_file=pathlib.Path.home() / ".dualgpuopt" / "logs" / "optimizer.log"
    )
    
    print("\n===== DualGPUOptimizer - LLM Workload Optimization v0.2.0 =====\n")
    
    try:
        print("Detecting GPUs...")
        gpus = gpu_info.probe_gpus()
        
        if len(gpus) < 2:
            print("Error: At least 2 GPUs are required for optimization")
            return 1
            
        # Show detected GPUs
        print("\nDetected GPUs:")
        for g in gpus:
            print(f"  GPU {g.index}: {g.name} - {g.mem_total} MiB total, {g.mem_free} MiB free")
        
        # Generate split configuration
        split = optimizer.split_string(gpus)
        tensor_fractions = optimizer.tensor_fractions(gpus)
        
        print(f"\nRecommended GPU Split: {split}")
        
        if args.model_path:
            ctx = args.context_size or 65536
            llama_cmd = optimizer.llama_command(args.model_path, ctx, split)
            vllm_cmd = optimizer.vllm_command(args.model_path, len(gpus))
            
            print("\nGenerated Commands:")
            print(f"  llama.cpp: {llama_cmd}")
            print(f"  vLLM: {vllm_cmd}")
            
            # Write env file if requested
            if args.env_file:
                env_path = pathlib.Path(args.env_file)
                optimizer.make_env_file(gpus, env_path)
                print(f"\nEnvironment variables written to: {env_path}")
        else:
            print("\nNo model path specified. Use --model-path to generate framework-specific commands.")
        
        return 0
            
    except Exception as err:
        logger.error(f"Optimization failed: {err}", exc_info=args.verbose)
        print(f"Error: {err}")
        return 1


def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DualGPUOptimizer - Optimize LLM workloads across multiple GPUs"
    )
    
    # Mode selection
    parser.add_argument(
        "--cli", action="store_true",
        help="Run in command-line mode (no GUI)"
    )
    
    # Common options
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-splash", action="store_true",
        help="Disable splash screen on startup"
    )
    
    # CLI mode options
    parser.add_argument(
        "-m", "--model-path", type=str,
        help="Path to model file or repository"
    )
    parser.add_argument(
        "-c", "--context-size", type=int,
        help="Context size (default: 65536)"
    )
    parser.add_argument(
        "-e", "--env-file", type=str,
        help="Write environment variables to this file"
    )
    
    return parser.parse_args(args)


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Setup logging regardless of mode
    log_file = pathlib.Path.home() / ".dualgpuopt" / "logs" / "gui.log"
    logger = setup_logging(
        verbose=args.verbose,
        log_file=log_file
    )
    
    try:
        if args.cli:
            return cli_optimize(args)
        else:
            # GUI mode
            # Show splash screen
            if not args.no_splash:
                print("\n===== DualGPUOptimizer - LLM Workload Optimization v0.2.0 =====")
                print("Starting GUI application...\n")
                # You could add a real splash screen with tkinter here if desired
                
            # Launch GUI
            run_app()
            return 0
    except Exception as err:
        logger.error(f"Application error: {err}", exc_info=args.verbose)
        print(f"Error: {err}")
        print("For more details, check the log file at: {log_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 