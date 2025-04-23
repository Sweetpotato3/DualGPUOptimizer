$env:PYTHONPATH = "$PSScriptRoot\dual_gpu_optimizer"
python -m pytest dual_gpu_optimizer/tests/test_config.py -v
