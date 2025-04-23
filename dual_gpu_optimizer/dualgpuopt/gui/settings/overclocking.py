"""
GPU overclocking settings component for the DualGPUOptimizer.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict, Any, Callable, Optional

# Try to import ttkbootstrap components
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *

    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk

    TTKBOOTSTRAP_AVAILABLE = False

from dualgpuopt.gpu_info import GPU
from dualgpuopt.services.event_service import event_bus
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.error_service import error_service
from dualgpuopt.commands.command_base import command_manager
from dualgpuopt.commands.gpu_commands import ApplyOverclockCommand


class OverclockingFrame(ttk.LabelFrame):
    """Frame containing GPU overclocking settings."""

    def __init__(
        self,
        parent: ttk.Frame,
        gpus: List[GPU],
        pad: int = 16,
        on_status_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Initialize the overclocking frame.

        Args:
            parent: Parent frame
            gpus: List of GPU objects
            pad: Padding value
            on_status_change: Callback for status updates
        """
        super().__init__(parent, text="GPU Overclocking")
        self.parent = parent
        self.gpus = gpus
        self.pad = pad
        self.on_status_change = on_status_change
        self.logger = logging.getLogger("dualgpuopt.gui.settings.overclocking")

        # Create danger zone styling for overclocking section
        if TTKBOOTSTRAP_AVAILABLE:
            self.configure(bootstyle="danger")
        else:
            # Apply custom styling for non-ttkbootstrap
            style = ttk.Style()
            style.configure("Danger.TLabelframe", bordercolor="#c0392b", borderwidth=2)
            style.configure("Danger.TLabelframe.Label", foreground="#c0392b")
            self.configure(style="Danger.TLabelframe")

        self.grid(sticky="ew", pady=(0, self.pad), padx=self.pad)
        self.columnconfigure(1, weight=1)

        self._create_gpu_selection()
        self._create_oc_sliders()
        self._create_oc_buttons()
        self._create_warning_info()

        # Register event handlers
        self._register_event_handlers()

        # Initialize the fan control state
        self._toggle_fan_control()

    def _register_event_handlers(self) -> None:
        """Register event handlers for events."""
        event_bus.subscribe("command_history_updated", self._update_command_history)
        event_bus.subscribe(
            "command_executed:apply_overclock", self._handle_overclock_result
        )

    def _update_command_history(self, data: Dict[str, Any]) -> None:
        """
        Update the command history UI.

        Args:
            data: Command history data
        """
        # Enable/disable the undo button based on history
        can_undo = data.get("can_undo", False)
        if hasattr(self, "undo_button"):
            self.undo_button["state"] = "normal" if can_undo else "disabled"

    def _handle_overclock_result(self, data: Dict[str, Any]) -> None:
        """
        Handle the result of an overclock command.

        Args:
            data: Overclock result data
        """
        success = data.get("success", False)

        if success and self.on_status_change:
            self.on_status_change(
                f"Overclock applied to GPU {data.get('gpu_index', '?')}"
            )

    def _create_gpu_selection(self) -> None:
        """Create GPU selection controls."""
        ttk.Label(self, text="GPU:").grid(
            row=0, column=0, sticky="w", padx=self.pad, pady=5
        )
        self.oc_gpu_var = tk.StringVar()
        gpu_values = [f"GPU {i}: {gpu.short_name}" for i, gpu in enumerate(self.gpus)]
        self.oc_gpu_combo = ttk.Combobox(
            self,
            textvariable=self.oc_gpu_var,
            values=gpu_values,
            width=20,
            state="readonly",
        )
        if gpu_values:
            self.oc_gpu_combo.current(0)
        self.oc_gpu_combo.grid(row=0, column=1, sticky="w", padx=self.pad, pady=5)
        self.oc_gpu_combo.bind("<<ComboboxSelected>>", self._update_oc_controls)

    def _create_oc_sliders(self) -> None:
        """Create overclocking slider controls."""
        oc_sliders_frame = ttk.Frame(self)
        oc_sliders_frame.grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=self.pad, pady=5
        )
        oc_sliders_frame.columnconfigure(1, weight=1)

        # Core Clock Offset slider
        ttk.Label(oc_sliders_frame, text="Core Clock Offset:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.core_clock_var = tk.IntVar(value=0)
        self.core_clock_scale = ttk.Scale(
            oc_sliders_frame,
            from_=-200,
            to=200,
            orient="horizontal",
            variable=self.core_clock_var,
            command=lambda v: self._update_label(
                self.core_clock_label, f"{int(float(v))} MHz"
            ),
        )
        self.core_clock_scale.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.core_clock_label = ttk.Label(oc_sliders_frame, text="0 MHz", width=8)
        self.core_clock_label.grid(row=0, column=2, padx=5, pady=2)

        # Memory Clock Offset slider
        ttk.Label(oc_sliders_frame, text="Memory Clock Offset:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.memory_clock_var = tk.IntVar(value=0)
        self.memory_clock_scale = ttk.Scale(
            oc_sliders_frame,
            from_=-1000,
            to=1500,
            orient="horizontal",
            variable=self.memory_clock_var,
            command=lambda v: self._update_label(
                self.memory_clock_label, f"{int(float(v))} MHz"
            ),
        )
        self.memory_clock_scale.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.memory_clock_label = ttk.Label(oc_sliders_frame, text="0 MHz", width=8)
        self.memory_clock_label.grid(row=1, column=2, padx=5, pady=2)

        # Power Limit slider
        ttk.Label(oc_sliders_frame, text="Power Limit:").grid(
            row=2, column=0, sticky="w", pady=2
        )
        self.power_limit_var = tk.IntVar(value=100)
        self.power_limit_scale = ttk.Scale(
            oc_sliders_frame,
            from_=50,
            to=120,
            orient="horizontal",
            variable=self.power_limit_var,
            command=lambda v: self._update_label(
                self.power_limit_label, f"{int(float(v))}%"
            ),
        )
        self.power_limit_scale.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.power_limit_label = ttk.Label(oc_sliders_frame, text="100%", width=8)
        self.power_limit_label.grid(row=2, column=2, padx=5, pady=2)

        # Fan Control slider
        ttk.Label(oc_sliders_frame, text="Fan Speed:").grid(
            row=3, column=0, sticky="w", pady=2
        )
        self.fan_speed_var = tk.IntVar(value=0)
        self.fan_speed_scale = ttk.Scale(
            oc_sliders_frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.fan_speed_var,
            command=lambda v: self._update_label(
                self.fan_speed_label, f"{int(float(v))}%"
            ),
        )
        self.fan_speed_scale.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        self.fan_speed_label = ttk.Label(oc_sliders_frame, text="Auto", width=8)
        self.fan_speed_label.grid(row=3, column=2, padx=5, pady=2)

        # Auto fan checkbox or Switch (if ttkbootstrap available)
        self.auto_fan_var = tk.BooleanVar(value=True)
        if TTKBOOTSTRAP_AVAILABLE:
            # Create a standard button that simulates a toggle switch
            auto_fan_check = ttk.Checkbutton(
                oc_sliders_frame,
                text="Auto Fan",
                variable=self.auto_fan_var,
                style="success.TCheckbutton",
                command=self._toggle_fan_control,
            )
        else:
            auto_fan_check = ttk.Checkbutton(
                oc_sliders_frame,
                text="Auto Fan",
                variable=self.auto_fan_var,
                command=self._toggle_fan_control,
            )
        auto_fan_check.grid(row=3, column=3, padx=5, pady=2)

    def _create_oc_buttons(self) -> None:
        """Create overclocking action buttons."""
        oc_buttons_frame = ttk.Frame(self)
        oc_buttons_frame.grid(
            row=2, column=0, columnspan=3, sticky="ew", padx=self.pad, pady=5
        )

        ttk.Button(
            oc_buttons_frame, text="Apply Overclock", command=self._apply_overclock
        ).grid(row=0, column=0, padx=5, pady=5)

        ttk.Button(oc_buttons_frame, text="Reset", command=self._reset_overclock).grid(
            row=0, column=1, padx=5, pady=5
        )

        self.undo_button = ttk.Button(
            oc_buttons_frame,
            text="Undo",
            command=self._undo_last_command,
            state="disabled",  # Will be enabled when commands are available
        )
        self.undo_button.grid(row=0, column=2, padx=5, pady=5)

    def _create_warning_info(self) -> None:
        """Create warning information section."""
        warning_frame = ttk.Frame(self)
        warning_frame.grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=self.pad, pady=5
        )

        warning_text = (
            "Warning: Overclocking may void warranty and can potentially damage hardware. "
            "Use at your own risk. Ensure your cooling is adequate."
        )
        warning_label = ttk.Label(
            warning_frame, text=warning_text, wraplength=400, justify="left"
        )
        warning_label.grid(row=0, column=0, sticky="w")

    def _update_label(self, label: ttk.Label, text: str) -> None:
        """
        Update a label with the given text.

        Args:
            label: Label widget to update
            text: New text for the label
        """
        label.config(text=text)

    def _toggle_fan_control(self) -> None:
        """Enable or disable fan control based on the auto fan checkbox."""
        if self.auto_fan_var.get():
            self.fan_speed_scale.config(state="disabled")
            self.fan_speed_label.config(text="Auto")
        else:
            self.fan_speed_scale.config(state="normal")
            value = int(self.fan_speed_var.get())
            self.fan_speed_label.config(text=f"{value}%")

    def _update_oc_controls(self, event=None) -> None:
        """Update overclocking controls when GPU selection changes."""
        selected = self.oc_gpu_var.get()
        if not selected:
            return

        # Extract GPU index from selection
        try:
            gpu_idx = int(selected.split(":")[0].replace("GPU", "").strip())

            # Get saved overclock settings for this GPU from config
            gpu_oc = config_service.get("gpu_overclock", {}).get(str(gpu_idx), {})

            # Update sliders with saved values
            self.core_clock_var.set(gpu_oc.get("core", 0))
            self.memory_clock_var.set(gpu_oc.get("memory", 0))
            self.power_limit_var.set(gpu_oc.get("power", 100))
            self.fan_speed_var.set(gpu_oc.get("fan", 0))
            self.auto_fan_var.set(gpu_oc.get("auto_fan", True))

            # Update labels
            self._update_label(
                self.core_clock_label, f"{self.core_clock_var.get()} MHz"
            )
            self._update_label(
                self.memory_clock_label, f"{self.memory_clock_var.get()} MHz"
            )
            self._update_label(self.power_limit_label, f"{self.power_limit_var.get()}%")

            # Update fan control
            self._toggle_fan_control()

            # Update status
            if self.on_status_change:
                self.on_status_change(f"Loaded settings for GPU {gpu_idx}")

        except (ValueError, IndexError) as e:
            error_service.handle_error(
                e,
                level="WARNING",
                title="GPU Selection Error",
                show_dialog=False,
                context={"operation": "update_oc_controls", "selection": selected},
            )

    def _apply_overclock(self) -> None:
        """Apply overclocking settings to the selected GPU."""
        selected = self.oc_gpu_var.get()
        if not selected:
            return

        # Extract GPU index from selection
        try:
            gpu_idx = int(selected.split(":")[0].replace("GPU", "").strip())

            # Get the GPU settings
            core_offset = self.core_clock_var.get()
            memory_offset = self.memory_clock_var.get()
            power_limit = self.power_limit_var.get()
            fan_speed = self.fan_speed_var.get() if not self.auto_fan_var.get() else 0
            auto_fan = self.auto_fan_var.get()

            # Create overclocking command
            command = ApplyOverclockCommand(
                gpu_idx, core_offset, memory_offset, power_limit, fan_speed, auto_fan
            )

            # Update status
            if self.on_status_change:
                self.on_status_change(f"Applying overclock to GPU {gpu_idx}...")

            # Execute command
            command_manager.execute(command)

        except (ValueError, IndexError) as e:
            error_service.handle_error(
                e,
                level="ERROR",
                title="Overclock Error",
                context={"operation": "apply_overclock"},
            )

    def _reset_overclock(self) -> None:
        """Reset overclocking settings to default values."""
        self.core_clock_var.set(0)
        self.memory_clock_var.set(0)
        self.power_limit_var.set(100)
        self.fan_speed_var.set(0)
        self.auto_fan_var.set(True)

        self._update_label(self.core_clock_label, "0 MHz")
        self._update_label(self.memory_clock_label, "0 MHz")
        self._update_label(self.power_limit_label, "100%")
        self._toggle_fan_control()

        # If a GPU is selected, also remove its saved overclock settings
        selected = self.oc_gpu_var.get()
        if selected and "gpu_overclock" in config_service.config:
            try:
                gpu_idx = int(selected.split(":")[0].replace("GPU", "").strip())
                if str(gpu_idx) in config_service.config["gpu_overclock"]:
                    del config_service.config["gpu_overclock"][str(gpu_idx)]
                    config_service.save()

                    # Publish event that GPU overclock was reset
                    event_bus.publish("gpu_overclock_reset", {"gpu_index": gpu_idx})

                    # Update status
                    if self.on_status_change:
                        self.on_status_change(f"Reset overclock for GPU {gpu_idx}")

            except (ValueError, IndexError) as e:
                error_service.handle_error(
                    e,
                    level="WARNING",
                    title="Reset Error",
                    show_dialog=False,
                    context={"operation": "reset_overclock"},
                )

    def _undo_last_command(self) -> None:
        """Undo the last command."""
        result = command_manager.undo()
        if result:
            if self.on_status_change:
                self.on_status_change("Last operation undone")
        else:
            messagebox.showerror(
                "Undo Failed",
                "Failed to undo the last operation",
                parent=self.winfo_toplevel(),
            )

    def get_current_settings(self) -> Dict[str, Any]:
        """
        Get current overclocking settings.

        Returns:
            Dictionary with current settings
        """
        selected = self.oc_gpu_var.get()
        if not selected:
            return {}

        try:
            gpu_idx = int(selected.split(":")[0].replace("GPU", "").strip())
            return {
                "gpu_index": gpu_idx,
                "core_offset": self.core_clock_var.get(),
                "memory_offset": self.memory_clock_var.get(),
                "power_limit": self.power_limit_var.get(),
                "fan_speed": self.fan_speed_var.get(),
                "auto_fan": self.auto_fan_var.get(),
            }
        except (ValueError, IndexError):
            return {}
