from dualgpuopt.model.vram_fit import fit_plan

def test_hetero_split():
    gpus = [{"memory_total": 16384}, {"memory_total": 8192}]
    plan = fit_plan(model_bytes=7_000_000_000, gpus=gpus)
    ratios = plan["split_ratios"]
    assert abs(sum(ratios) - 1.0) < 1e-6
    # big card should get at least 60 % for 2× memory
    assert ratios[0] > ratios[1]
    # context sizes dictionary present
    assert "context_sizes" in plan 