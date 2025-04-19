@echo off
echo Starting DualGPUOptimizer...

:: Set PyTorch environment variables
set CUDA_VISIBLE_DEVICES=0,1
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
set PYTORCH_ENABLE_OBSOLETE_CUDA_COMPAT=1

:: Activate the virtual environment and run
call .venv\Scripts\activate.bat
python run_optimizer.py

pause 