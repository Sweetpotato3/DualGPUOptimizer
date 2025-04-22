"""
Unified backend engine that auto-detects model format and
selects appropriate runtime (llama.cpp, vLLM, or HF).
"""

from __future__ import annotations

import logging
import pathlib
import shutil
import socket
import subprocess
import time
from typing import Iterator, Optional, Protocol

log = logging.getLogger("backend")


class ModelBackend(Protocol):
    def load(self, model_path: str, **kwargs) -> None: ...
    def stream(self, prompt: str, **kwargs) -> Iterator[str]: ...
    def unload(self) -> None: ...
    def health(self) -> bool: ...


class LlamaCppBackend:
    """Backend for llama.cpp models (GGUF format)"""

    def __init__(self):
        self.proc = None
        self.url = None
        self.port = None

    def load(self, model_path: str, **kwargs):
        self.port = kwargs.get("port", 8001)
        gpu_layers = kwargs.get("gpu_layers", 0)
        split_mode = kwargs.get("split_mode", 0)

        cmd = [
            "llama.cpp",
            "-m",
            model_path,
            "--server",
            "--port",
            str(self.port),
            "--gpu-layers",
            str(gpu_layers),
        ]

        if split_mode > 0:
            cmd.extend(["--split-mode", str(split_mode)])

        log.info(f"Starting llama.cpp: {' '.join(cmd)}")
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
        self.url = f"http://127.0.0.1:{self.port}/completion"

        # Wait for server to start
        while not self._port_open(self.port):
            time.sleep(0.2)

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        import json

        import requests

        params = {
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }

        try:
            response = requests.post(self.url, json=params, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                if line.startswith(b"data: "):
                    data = json.loads(line[6:])
                    if "content" in data:
                        yield data["content"]
        except Exception as e:
            log.error(f"Error streaming from llama.cpp: {e}")
            yield f"[ERROR: {str(e)}]"

    def unload(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

    def health(self) -> bool:
        return self._port_open(self.port)

    def _port_open(self, port: int) -> bool:
        with socket.socket() as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0


class VLLMBackend:
    """Backend for vLLM models (AWQ and other quantized formats)"""

    def __init__(self):
        self.proc = None
        self.url = None
        self.port = None

    def load(self, model_path: str, **kwargs):
        self.port = kwargs.get("port", 8000)
        tensor_parallel = kwargs.get("tp", 2)
        quant = kwargs.get("quant", None)

        cmd = [
            shutil.which("python"),
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            model_path,
            "--tensor-parallel-size",
            str(tensor_parallel),
            "--port",
            str(self.port),
        ]

        if quant == "awq":
            cmd.extend(["--quantization", "awq"])

        log.info(f"Starting vLLM: {' '.join(cmd)}")
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
        self.url = f"http://127.0.0.1:{self.port}/v1/chat/completions"

        # Wait for server to start
        while not self._port_open(self.port):
            time.sleep(0.2)

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        import json

        import requests

        messages = [{"role": "user", "content": prompt}]

        params = {
            "model": "local",
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }

        try:
            response = requests.post(self.url, json=params, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if not line or line == b"data: [DONE]":
                    continue

                if line.startswith(b"data: "):
                    data = json.loads(line[6:])
                    content = data["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content
        except Exception as e:
            log.error(f"Error streaming from vLLM: {e}")
            yield f"[ERROR: {str(e)}]"

    def unload(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

    def health(self) -> bool:
        return self._port_open(self.port)

    def _port_open(self, port: int) -> bool:
        with socket.socket() as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0


class HFBackend:
    """Backend for HuggingFace Transformers models"""

    def __init__(self):
        self.model = None
        self.tokenizer = None

    def load(self, model_path: str, **kwargs):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            log.info(f"Loading HF model: {model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
            )
        except Exception as e:
            log.error(f"Error loading HF model: {e}")
            raise

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        if not self.model or not self.tokenizer:
            yield "[ERROR: Model not loaded]"
            return

        try:
            from threading import Thread

            from transformers import TextIteratorStreamer

            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            streamer = TextIteratorStreamer(
                self.tokenizer, skip_special_tokens=True, skip_prompt=True
            )

            gen_kwargs = {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs.get("attention_mask", None),
                "max_new_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "streamer": streamer,
            }

            # Run generation in a separate thread
            thread = Thread(target=self.model.generate, kwargs=gen_kwargs)
            thread.start()

            # Yield from streamer
            for text in streamer:
                yield text

        except Exception as e:
            log.error(f"Error streaming from HF model: {e}")
            yield f"[ERROR: {str(e)}]"

    def unload(self):
        import gc

        self.model = None
        self.tokenizer = None
        gc.collect()

    def health(self) -> bool:
        return True


class Engine:
    """Unified model engine that selects appropriate backend"""

    def __init__(self):
        self.backend: Optional[ModelBackend] = None

    def _select_backend(self, model_path: str) -> ModelBackend:
        """Select appropriate backend based on model path"""
        path = pathlib.Path(model_path)
        ext = path.suffix.lower().lstrip(".")
        path_lower = model_path.lower()

        # Select backend based on file extension or path content
        if ext == "gguf" or "gguf" in path_lower:
            return LlamaCppBackend()
        elif "awq" in path_lower:
            return VLLMBackend()
        else:
            return HFBackend()

    def load(self, model_path: str, **kwargs) -> None:
        """Load model with appropriate backend based on file extension"""
        # Select the appropriate backend
        self.backend = self._select_backend(model_path)

        # Load the model
        self.backend.load(model_path, **kwargs)

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream tokens from the model"""
        if not self.backend:
            yield "[ERROR: No model loaded]"
            return

        yield from self.backend.stream(prompt, **kwargs)

    def unload(self) -> None:
        """Unload current model"""
        if self.backend:
            self.backend.unload()
            self.backend = None
