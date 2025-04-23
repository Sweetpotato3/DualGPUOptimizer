from __future__ import annotations

import pathlib
import shutil
import socket
import subprocess
import time
from typing import Iterable


# ------------------------------------------------------ #
def _port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


# ------------------------------------------------------ #
class LlamaCppBackend:
    def load(self, model: str, *, port=8001, gpu_layers=None, offload_dir=None, **_kw):
        self.port = port
        args = ["llama.cpp", "-m", model, "--server", "--port", str(port)]
        if gpu_layers is not None:
            args += ["--gpu-layers", str(gpu_layers)]
        if offload_dir:  # mmap enables OS‑level SSD paging
            args += ["--mmap"]
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL)
        while not _port_open(port):
            time.sleep(0.25)

    def stream(self, prompt, **kw) -> Iterable[str]:
        import json

        import requests
        import sseclient

        r = requests.post(
            f"http://127.0.0.1:{self.port}/completion",
            json={"prompt": prompt, "n_predict": kw.get("max_tokens", 128)},
            stream=True,
            timeout=30,
        )
        for ev in sseclient.SSEClient(r):
            tok = json.loads(ev.data)["content"]
            if tok:
                yield tok

    def unload(self):
        self.proc.terminate()

    def health(self):
        return _port_open(self.port)


# ------------------------------------------------------ #
class VLLMBackend:
    def load(self, model, *, port=8000, gpu_util=0.88, swap=0, quant=None, **_kw):
        self.port = port
        cmd = [
            shutil.which("python"),
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            model,
            "--port",
            str(port),
            "--gpu-memory-util",
            str(gpu_util),
        ]
        if swap:
            cmd += ["--swap-space", str(swap)]
        if quant == "awq":
            cmd += ["--quantization", "awq", "--dtype", "auto"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
        while not _port_open(port):
            time.sleep(0.25)

    def stream(self, prompt, **kw):
        import json

        import requests
        import sseclient

        js = {
            "model": "local",
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kw.get("max_tokens", 128),
        }
        r = requests.post(
            f"http://127.0.0.1:{self.port}/v1/chat/completions",
            json=js,
            stream=True,
            timeout=60,
        )
        for ev in sseclient.SSEClient(r):
            tok = json.loads(ev.data)["choices"][0]["delta"].get("content", "")
            if tok:
                yield tok

    def unload(self):
        self.proc.terminate()

    def health(self):
        return _port_open(self.port)


# ------------------------------------------------------ #
class HFBackend:
    def load(self, model: str, *, device_map="auto", offload_dir=None, **_kw):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if offload_dir:
            pathlib.Path(offload_dir).mkdir(parents=True, exist_ok=True)
        self.tok = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model,
            torch_dtype="auto",
            low_cpu_mem_usage=True,
            device_map=device_map,
            offload_folder=offload_dir,
        )

    def stream(self, prompt, **kw):
        ids = self.tok(prompt, return_tensors="pt").to("cuda")
        gen = self.model.generate(**ids, max_new_tokens=kw.get("max_tokens", 128))
        out = self.tok.decode(gen[0], skip_special_tokens=True)
        yield out[len(prompt) :]

    def unload(self):
        del self.model

    def health(self):
        return True


# ------------------------------------------------------ #
class Engine:
    _cls_map = {
        "gguf": LlamaCppBackend,
        "awq": VLLMBackend,
        "safetensors": HFBackend,
        "bin": HFBackend,
    }

    def load(self, path_or_id: str, **kw):
        suf = pathlib.Path(path_or_id).suffix.lower().lstrip(".")
        if suf == "safetensors" and "awq" in path_or_id.lower():
            suf = "awq"
        self.backend = self._cls_map.get(suf, HFBackend)()
        self.backend.load(path_or_id, **kw)

    def stream(self, prompt: str, **kw):
        return self.backend.stream(prompt, **kw)

    def unload(self):
        self.backend.unload()

    def health(self):
        return self.backend.health()
