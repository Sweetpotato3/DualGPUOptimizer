"""
Main entry point for the DualGPUOptimizer.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import List

from dualgpuopt.gui import run_app
from dualgpuopt.logconfig import setup_logging
from dualgpuopt import gpu_info, optimizer, configio


def cli_optimize(args: argparse.Namespace) -> int:
    """Run in CLI mode to generate optimization config."""
    # Setup logging
    logger = setup_logging(
        verbose=args.verbose,
        log_file=pathlib.Path.home() / ".dualgpuopt" / "logs" / "optimizer.log"
    )
    
    # Detect GPUs
    try:
        gpus = gpu_info.probe_gpus()
        if len(gpus) < 2:
            logger.error("At least 2 GPUs are required for optimization")
            return 1
            
        logger.info(f"Detected {len(gpus)} GPUs:")
        for g in gpus:
            logger.info(f"  [{g.index}] {g.name}: {g.mem_total} MiB total, {g.mem_free} MiB free")
        
        # Generate split configuration
        split = optimizer.split_string(gpus)
        logger.info(f"Recommended GPU split: {split}")
        
        # Generate commands
        if args.model_path:
            ctx = args.context_size or 65536
            llama_cmd = optimizer.llama_command(args.model_path, ctx, split)
            vllm_cmd = optimizer.vllm_command(args.model_path, len(gpus))
            
            logger.info("Generated commands:")
            logger.info(f"llama.cpp: {llama_cmd}")
            logger.info(f"vLLM: {vllm_cmd}")
            
            # Write env file if requested
            if args.env_file:
                env_path = pathlib.Path(args.env_file)
                optimizer.make_env_file(gpus, env_path)
                logger.info(f"Environment variables written to: {env_path}")
                
        return 0
        
    except Exception as err:
        logger.error(f"Optimization failed: {err}", exc_info=args.verbose)
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
    
    if args.cli:
        return cli_optimize(args)
    else:
        # GUI mode
        setup_logging(
            verbose=args.verbose,
            log_file=pathlib.Path.home() / ".dualgpuopt" / "logs" / "gui.log"
        )
        run_app()
        return 0


if __name__ == "__main__":
    sys.exit(main()) 