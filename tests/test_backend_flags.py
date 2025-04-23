from dualgpuopt.engine.backend import LlamaCppBackend, VLLMBackend


class _DummyPopen:
    def __init__(self, args, **_):
        self.args = args

    def terminate(self):
        pass


def test_llamacpp_gpu_layers_and_mmap(monkeypatch, tmp_path):
    # Mock _port_open to prevent waiting for a real port
    monkeypatch.setattr("dualgpuopt.engine.backend._port_open", lambda _: True)
    # Mock subprocess.Popen
    monkeypatch.setattr("subprocess.Popen", lambda a, **_: _DummyPopen(a))

    be = LlamaCppBackend()
    off = tmp_path / "off"
    be.load("model.gguf", gpu_layers=28, offload_dir=str(off))
    args = be.proc.args
    assert "--gpu-layers" in args and "28" in args
    assert "--mmap" in args


def test_vllm_swap_space(monkeypatch):
    # Mock _port_open to prevent waiting for a real port
    monkeypatch.setattr("dualgpuopt.engine.backend._port_open", lambda _: True)
    # Mock subprocess.Popen
    monkeypatch.setattr("subprocess.Popen", lambda a, **_: _DummyPopen(a))

    be = VLLMBackend()
    be.load("model.awq", swap=16, gpu_util=0.7, quant="awq")
    a = " ".join(be.proc.args)
    assert "--swap-space 16" in a and "--gpu-memory-util 0.7" in a
    assert "--quantization awq" in a
