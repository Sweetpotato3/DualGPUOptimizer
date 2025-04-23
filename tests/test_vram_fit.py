from dualgpuopt.model.vram_fit import fit_plan

GPU8 = [{"memory_total": 8 * 1024}]  # one 8 GB card
GPU24 = [{"memory_total": 24 * 1024}]  # one 24 GB card
GPU_DUAL = [{"memory_total": 8 * 1024}, {"memory_total": 12 * 1024}]


def test_gpu_only_plan():
    # 7 B ≈ 3.4 GiB fp16  → awq fits on 8 GB
    size = int(7 * 0.48 * 1e9)
    p = fit_plan(size, GPU8)
    assert p["quant"] == "awq" and not p["disk"]


def test_split_layers():
    # 33 B ≈ 16 GiB gguf; too big for 8 GB with direct fp16, but should fit with awq or gguf layers
    size = int(33 * 0.15 * 1e9)
    p = fit_plan(size, GPU8)
    assert p["quant"] in ("awq", "gguf") and not p["disk"]
    # If gguf with gpu_layers, verify layers are reasonable
    if p["quant"] == "gguf" and "gpu_layers" in p:
        assert 0 < p["gpu_layers"] < int(33 * 32)


def test_ram_offload():
    # 13 B on 24 GB machine should choose quantized model
    size = int(13 * 0.48 * 1e9)
    p = fit_plan(size, GPU24)
    assert p["quant"] in ("awq", "fp16") and not p["disk"]
    # If using offload, check for offload directory
    if p.get("device_map") == "balanced_low_0":
        assert p.get("offload_dir")


def test_disk_spill():
    # 70 B on 8 GB → expect some form of memory management
    size = int(70 * 0.48 * 1e9)
    p = fit_plan(size, GPU8)
    # Either disk spill with swap ≥ 1, or gguf with gpu_layers
    assert (p.get("disk") and p.get("swap", 0) >= 1) or (p["quant"] == "gguf" and "gpu_layers" in p)
