"""
Tkinter front‑end.  No business logic – pulls helpers from gpu_info / optimizer.
"""
from __future__ import annotations

import json
import pathlib
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from dualgpuopt import gpu_info, optimizer, configio
from dualgpuopt.telemetry import start_stream
from dualgpuopt.runner import Runner
from dualgpuopt.tray import init_tray


class DualGpuApp(ttk.Frame):
    PAD = 8

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=self.PAD)
        self.model_var = tk.StringVar(value="dolphin‑2.5‑mixtral‑8x7b.Q3_K_M.gguf")
        self.ctx_var = tk.IntVar(value=65536)
        self.runner = None
        self.tele_hist: list[tuple[int, int]] = []  # (gpu0_load, gpu1_load)

        # Load config and presets
        self.cfg = configio.load_cfg()
        preset_path = pathlib.Path(__file__).parent / "presets" / "mixtral.json"
        self.presets = json.load(preset_path.open())
        
        if self.cfg["last_model"]:
            self.model_var.set(self.cfg["last_model"])

        self.gpus = gpu_info.probe_gpus()
        if len(self.gpus) < 2:
            messagebox.showerror("Error", "Need ≥ 2 GPUs – aborting")
            master.destroy()
            return

        self._build_ui()
        self._refresh_outputs()
        
        # Setup telemetry
        self.tele_q = start_stream(1.0)
        self.after(1000, self._tick_chart)
        
        # Setup tray
        init_tray(self)

    # ---------- UI builders ----------
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        
        # Use notebook for tabs
        nb = ttk.Notebook(self)
        opt_frame = ttk.Frame(nb, padding=self.PAD)
        
        # Move existing UI elements to opt_frame
        self._build_optimizer_tab(opt_frame)
        
        # Add tabs
        nb.add(opt_frame, text="Optimiser")
        self.launch_frame = ttk.Frame(nb, padding=self.PAD)
        self._build_launch_tab(self.launch_frame)
        nb.add(self.launch_frame, text="Launch")
        nb.pack(fill="both", expand=True)

    def _build_optimizer_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)

        # GPU Treeview
        tv = ttk.Treeview(parent, columns=("name", "total", "free"), show="headings")
        for col, hdr in zip(("name", "total", "free"),
                            ("Name", "Total (MiB)", "Free (MiB)")):
            tv.heading(col, text=hdr)
            tv.column(col, anchor="center")
        for g in self.gpus:
            tv.insert("", "end", values=(g.name, g.mem_total, g.mem_free))
        tv.grid(sticky="ew", pady=(0, self.PAD))

        # Model path frame with preset selection
        path_frame = ttk.Frame(parent)
        ttk.Label(path_frame, text="Model path / repo:").pack(side="left")
        ttk.Entry(path_frame, textvariable=self.model_var, width=60).pack(side="left", expand=1, fill="x")
        ttk.Button(path_frame, text="Browse…", command=self._browse).pack(side="right")
        
        # Add preset selection
        self.preset_cmb = ttk.Combobox(path_frame, width=18, values=list(self.presets.keys()))
        self.preset_cmb.set("choose‑preset")
        self.preset_cmb.bind("<<ComboboxSelected>>", self._preset_selected)
        self.preset_cmb.pack(side="right")
        
        path_frame.grid(sticky="ew", pady=(0, self.PAD))
        parent.columnconfigure(0, weight=1)

        # Ctx + buttons
        ctl = ttk.Frame(parent)
        ttk.Label(ctl, text="Context size:").pack(side="left")
        ttk.Spinbox(ctl, from_=2048, to=131072, textvariable=self.ctx_var, width=8).pack(side="left")
        ttk.Button(ctl, text="Generate", command=self._refresh_outputs).pack(side="right")
        ctl.grid(sticky="ew", pady=(0, self.PAD))

        # Output text
        self.text = tk.Text(parent, height=10, wrap="word")
        self.text.grid(sticky="nsew")
        parent.rowconfigure(parent.grid_size()[1]-1, weight=1)

        # Copy + save env
        btm = ttk.Frame(parent)
        ttk.Button(btm, text="Copy llama.cpp", command=lambda: self._copy("llama")).pack(side="left")
        ttk.Button(btm, text="Copy vLLM", command=lambda: self._copy("vllm")).pack(side="left")
        ttk.Button(btm, text="Save env file", command=self._save_env).pack(side="right")
        btm.grid(sticky="ew", pady=(self.PAD, 0))

    def _build_launch_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        
        # Control buttons
        btn_frame = ttk.Frame(parent)
        ttk.Button(btn_frame, text="Launch llama.cpp", command=lambda: self._start_runner("llama")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Launch vLLM", command=lambda: self._start_runner("vllm")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Stop", command=self._stop_runner).pack(side="left", padx=5)
        btn_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.PAD))
        
        # Log output
        log_frame = ttk.LabelFrame(parent, text="Execution Log")
        self.log_box = tk.Text(log_frame, height=15, wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        log_frame.grid(row=1, column=0, sticky="nsew")
        
        # GPU utilization chart
        chart_frame = ttk.LabelFrame(parent, text="GPU Utilization")
        self.chart = tk.Canvas(chart_frame, height=120, bg="#202020")
        self.chart.pack(fill="both", expand=True)
        chart_frame.grid(row=2, column=0, sticky="ew", pady=(self.PAD, 0))
        
        # Start log refreshing
        self.after(500, self._pump_log)

    # ---------- callbacks ----------
    def _browse(self) -> None:
        path = filedialog.askopenfilename(title="Select model / folder")
        if path:
            self.model_var.set(path)
            # Update config
            self.cfg["last_model"] = path
            configio.save_cfg(self.cfg)

    def _refresh_outputs(self) -> None:
        split = optimizer.split_string(self.gpus)
        llama_cmd = optimizer.llama_command(self.model_var.get(), self.ctx_var.get(), split)
        vllm_cmd = optimizer.vllm_command(self.model_var.get(), len(self.gpus))
        out = (
            f"# gpu‑split suggestion\n{split}\n\n"
            f"# llama.cpp\n{llama_cmd}\n\n"
            f"# vLLM\n{vllm_cmd}\n"
        )
        self.text.delete("1.0", "end")
        self.text.insert("1.0", out)

    def _copy(self, which: str) -> None:
        content = self.text.get("1.0", "end").splitlines()
        if which == "llama":
            snippet = "\n".join(line for line in content if line.startswith("./main"))
        else:
            snippet = "\n".join(line for line in content if line.startswith("python -m vllm"))
        self.clipboard_clear()
        self.clipboard_append(snippet)
        messagebox.showinfo("Copied", f"{which} command copied to clipboard!")

    def _save_env(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Save env file",
            defaultextension=".sh" if not tk.sys.platform.startswith("win") else ".ps1",
            filetypes=[("Shell script", "*.sh"), ("PowerShell", "*.ps1"), ("All", "*.*")]
        )
        if filename:
            optimizer.make_env_file(self.gpus, pathlib.Path(filename))
            messagebox.showinfo("Saved", f"Env file saved → {filename}")
    
    def _preset_selected(self, *_) -> None:
        key = self.preset_cmb.get()
        pre = self.presets[key]
        self.model_var.set(pre["model"])
        self.ctx_var.set(pre.get("ctx", 65536))
    
    def _start_runner(self, which: str) -> None:
        if self.runner:
            self.runner.stop()
        split = optimizer.split_string(self.gpus)
        cmd = optimizer.llama_command(self.model_var.get(), self.ctx_var.get(), split) if which=="llama" \
            else optimizer.vllm_command(self.model_var.get(), len(self.gpus))
        self.runner = Runner(cmd)
        self.runner.start()
        self.log_box.delete("1.0", "end")
    
    def _stop_runner(self) -> None:
        if self.runner:
            self.runner.stop()
            self.log_box.insert("end", "Process stopped.\n")
            self.log_box.see("end")
    
    def _pump_log(self) -> None:
        if self.runner:
            try:
                while True:
                    line = self.runner.q.get_nowait()
                    self.log_box.insert("end", line+"\n")
                    self.log_box.see("end")
            except queue.Empty:
                pass
        self.after(500, self._pump_log)
    
    def _tick_chart(self) -> None:
        try:
            tele = self.tele_q.get_nowait()
            self.tele_hist.append((tele.load[0], tele.load[1]))
            self.tele_hist = self.tele_hist[-120:]  # keep 2 min
            self.chart.delete("all")
            w = self.chart.winfo_width()
            if w > 1:  # Ensure chart is visible
                step = w/len(self.tele_hist)
                for i, (l0, l1) in enumerate(self.tele_hist):
                    x = int(i*step)
                    self.chart.create_line(x, 120, x, 120-l0, fill="#33ff55")
                    self.chart.create_line(x, 120-l0, x, 120-l0-l1, fill="#00b0ff")
        except queue.Empty:
            pass
        except IndexError:
            # Handle case where not enough GPUs
            pass
        self.after(1000, self._tick_chart)


def run_app() -> None:
    root = tk.Tk()
    root.title("Dual‑GPU Optimiser")
    root.minsize(800, 480)
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        # Fall back to default theme if clam not available
        pass
    DualGpuApp(root).pack(fill="both", expand=True)
    root.mainloop() 