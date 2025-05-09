"""
Stateless helpers to turn GPU info → split strings, env files, commands.
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import List

from dualgpuopt.gpu_info import GPU


def split_string(gpus: List[GPU]) -> str:
    return ",".join(str(g.mem_total_gb) for g in gpus)


def tensor_fractions(gpus: List[GPU]) -> list[float]:
    top = max(g.mem_total for g in gpus)
    return [round(g.mem_total / top, 3) for g in gpus]


def make_env_file(gpus: List[GPU], filename: Path) -> Path:
    env = textwrap.dedent(
        f"""
        # Auto‑generated by dualgpuopt
        CUDA_VISIBLE_DEVICES={','.join(str(g.index) for g in gpus)}
        NCCL_P2P_DISABLE=0
        NCCL_IB_DISABLE=1
        NCCL_NET_GDR_LEVEL=2
        OMP_NUM_THREADS={os.cpu_count()//2}
        PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
        """
    ).strip()
    filename.write_text(env, encoding="utf‑8")
    return filename


def llama_command(model_path: str, ctx: int, split: str) -> str:
    return (
        f"./main -m {model_path} "
        f"--gpu-split {split} --n-gpu-layers 999 --ctx-size {ctx}"
    )


def vllm_command(model_path: str, tp: int) -> str:
    return (
        "python -m vllm.entrypoints.openai.api_server "
        f"--model {model_path} --dtype float16 "
        f"--tensor-parallel-size {tp} --gpu-memory-utilization 0.9"
    )
