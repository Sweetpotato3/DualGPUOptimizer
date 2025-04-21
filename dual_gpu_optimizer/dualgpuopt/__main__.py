"""
Main entry point for the DualGPUOptimizer.
"""

from __future__ import annotations

import logging
import os
import pathlib
import sys
import traceback

# Setup minimal logging first
os.makedirs(pathlib.Path.home() / ".dualgpuopt" / "logs", exist_ok=True)
log_path = pathlib.Path.home() / ".dualgpuopt" / "logs" / "startup.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("dualgpuopt.startup")

# Try to import the required modules
try:
    import argparse
    from typing import List

    # Check for rich module
    try:
        import importlib.util

        if importlib.util.find_spec("rich") is None:
            raise ImportError("rich module not found")

        from rich.console import Console

        logger.info("Successfully imported rich module")
    except ImportError as e:
        logger.error(f"Failed to import rich module: {e}")
        print("Error: Missing 'rich' module. Try installing it with: pip install rich")
        sys.exit(1)

    # Try to import optional dependencies
    try:
        pass

        logger.info("Successfully imported torch")
        TORCH_AVAILABLE = True
    except ImportError:
        logger.warning(
            "Optional dependency 'torch' not found - some features will be disabled"
        )
        TORCH_AVAILABLE = False

    try:
        pass

        logger.info("Successfully imported prometheus_client")
        PROMETHEUS_AVAILABLE = True
    except ImportError:
        logger.warning(
            "Optional dependency 'prometheus_client' not found - "
            "metrics will be disabled"
        )
        PROMETHEUS_AVAILABLE = False

    # Try to import application modules
    try:
        from dualgpuopt import gpu_info, optimizer
        from dualgpuopt.gui import run_app
        from dualgpuopt.logconfig import setup_logging

        logger.info("Successfully imported application modules")
    except ImportError as e:
        logger.error(f"Failed to import application modules: {e}")
        print(
            "Error: Application modules not found. Please ensure the package is "
            "installed with: pip install -e ./dual_gpu_optimizer"
        )
        sys.exit(1)

    # Initialize rich console
    console = Console()

    def cli_optimize(args: argparse.Namespace) -> int:
        """Run in CLI mode to generate optimization config."""
        # Setup logging
        logger = setup_logging(
            verbose=args.verbose,
            log_file=pathlib.Path.home() / ".dualgpuopt" / "logs" / "optimizer.log",
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
                print(
                    f"  GPU {g.index}: {g.name} - {g.mem_total} MiB total, "
                    f"{g.mem_free} MiB free"
                )

            # Generate split configuration
            split = optimizer.split_string(gpus)
            optimizer.tensor_fractions(gpus)

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
                print(
                    "\nNo model path specified. Use --model-path to generate "
                    "framework-specific commands."
                )

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
            "--cli", action="store_true", help="Run in command-line mode (no GUI)"
        )

        # Common options
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Enable verbose logging"
        )

        parser.add_argument(
            "--no-splash", action="store_true", help="Disable splash screen on startup"
        )

        parser.add_argument(
            "--mock",
            action="store_true",
            help="Use mock GPU data instead of real hardware",
        )

        # CLI mode options
        parser.add_argument(
            "-m", "--model-path", type=str, help="Path to model file or repository"
        )
        parser.add_argument(
            "-c", "--context-size", type=int, help="Context size (default: 65536)"
        )
        parser.add_argument(
            "-e",
            "--env-file",
            type=str,
            help="Write environment variables to this file",
        )

        return parser.parse_args(args)

    def main() -> int:
        """Main entry point."""
        global logger
        args = parse_args()

        # Enable mock mode if requested
        if args.mock:
            os.environ["DGPUOPT_MOCK_GPUS"] = "1"
            logger.info("Mock GPU mode enabled by command-line flag")

        # Setup logging regardless of mode
        log_file = pathlib.Path.home() / ".dualgpuopt" / "logs" / "gui.log"
        app_logger = setup_logging(verbose=args.verbose, log_file=log_file)

        try:
            if args.cli:
                return cli_optimize(args)
            else:
                # GUI mode
                # Show splash screen
                if not args.no_splash:
                    print(
                        "\n===== DualGPUOptimizer - LLM Workload Optimization "
                        "v0.2.0 ====="
                    )
                    print("Starting GUI application...\n")

                # Launch GUI
                run_app()
                return 0
        except Exception as err:
            app_logger.error(f"Application error: {err}", exc_info=args.verbose)
            print(f"Error: {err}")
            print(f"For more details, check the log file at: {log_file}")
            return 1

    if __name__ == "__main__":
        sys.exit(main())

except Exception as e:
    # Catch-all for any startup errors
    error_message = f"Critical startup error: {str(e)}\n{traceback.format_exc()}"
    try:
        logger.critical(error_message)
    except Exception:
        # If even the logger fails, write to a file directly
        with open(log_path, "a") as f:
            f.write(f"{error_message}\n")

    print(f"Critical error during startup: {str(e)}")
    print(f"Check log file at: {log_path}")

    # Keep console open if running the exe directly
    if getattr(sys, "frozen", False):
        input("Press Enter to exit...")

    sys.exit(1)
