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
    
    # Header display
    console.print(
        Panel.fit(
            "[bold green]DualGPUOptimizer[/bold green] - LLM Workload Optimization",
            border_style="blue",
            title="v0.2.0"
        )
    )
    
    # Detect GPUs with progress feedback
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[green]Detecting GPUs...", total=1)
        
        try:
            gpus = gpu_info.probe_gpus()
            progress.update(task, advance=1)
            
            if len(gpus) < 2:
                progress.stop()
                console.print("[bold red]Error:[/bold red] At least 2 GPUs are required for optimization")
                return 1
                
            # Show detected GPUs in a table
            progress.stop()
            gpu_table = Table(title="Detected GPUs")
            gpu_table.add_column("Index", style="cyan")
            gpu_table.add_column("Name", style="green")
            gpu_table.add_column("Total Memory", style="magenta")
            gpu_table.add_column("Free Memory", style="yellow")
            
            for g in gpus:
                gpu_table.add_row(
                    str(g.index),
                    g.name,
                    f"{g.mem_total} MiB",
                    f"{g.mem_free} MiB"
                )
            
            console.print(gpu_table)
            
            # Generate and display optimization configuration
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Generating optimization config..."),
                console=console
            ) as progress2:
                task2 = progress2.add_task("Working...", total=None)
                
                # Generate split configuration
                split = optimizer.split_string(gpus)
                tensor_fractions = optimizer.tensor_fractions(gpus)
                
                # Prepare display data
                time.sleep(0.5)  # Small delay for visual effect
                progress2.stop()
                
                # Show optimization results
                layout = Layout()
                layout.split_column(
                    Layout(name="header", size=3),
                    Layout(name="main")
                )
                
                layout["header"].update(
                    Panel(
                        f"[bold]Recommended GPU Split:[/bold] {split}",
                        border_style="green"
                    )
                )
                
                if args.model_path:
                    ctx = args.context_size or 65536
                    llama_cmd = optimizer.llama_command(args.model_path, ctx, split)
                    vllm_cmd = optimizer.vllm_command(args.model_path, len(gpus))
                    
                    command_table = Table(title="Generated Commands")
                    command_table.add_column("Framework", style="cyan")
                    command_table.add_column("Command", style="green", no_wrap=False)
                    
                    command_table.add_row("llama.cpp", llama_cmd)
                    command_table.add_row("vLLM", vllm_cmd)
                    
                    layout["main"].update(command_table)
                    console.print(layout)
                    
                    # Write env file if requested
                    if args.env_file:
                        env_path = pathlib.Path(args.env_file)
                        with Progress(
                            SpinnerColumn(),
                            TextColumn(f"[cyan]Writing environment to {env_path}..."),
                            console=console
                        ) as progress3:
                            task3 = progress3.add_task("Writing...", total=None)
                            optimizer.make_env_file(gpus, env_path)
                            time.sleep(0.5)  # Small delay for visual effect
                            progress3.stop()
                        
                        console.print(f"[bold green]Environment variables written to:[/bold green] {env_path}")
                
                return 0
                
        except Exception as err:
            logger.error(f"Optimization failed: {err}", exc_info=args.verbose)
            console.print(f"[bold red]Error:[/bold red] {err}")
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