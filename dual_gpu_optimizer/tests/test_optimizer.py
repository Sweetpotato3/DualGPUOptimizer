"""
Test suite for the optimizer module.
"""

import pytest

from dualgpuopt.optimizer import split_string, tensor_fractions, llama_command, vllm_command, make_env_file
from dualgpuopt.gpu_info import GPU


# Test fixture for creating GPU objects
@pytest.fixture
def mock_gpus():
    return [
        GPU(0, "NVIDIA RTX 4090", 24576, 24000),  # 24GB GPU
        GPU(1, "NVIDIA RTX 3090", 24576, 24000),  # 24GB GPU
        GPU(2, "NVIDIA RTX 3080", 10240, 10000),  # 10GB GPU
    ]


@pytest.fixture
def mock_gpus_mixed():
    return [
        GPU(0, "NVIDIA RTX 4090", 24576, 24000),  # 24GB GPU
        GPU(1, "NVIDIA RTX 3080", 10240, 10000),  # 10GB GPU
        GPU(2, "NVIDIA A100", 40960, 40000),      # 40GB GPU
    ]


def test_split_string_equal_gpus(mock_gpus):
    """Test split string generation with equal GPUs."""
    # Take just the first two equal GPUs
    equal_gpus = mock_gpus[:2]
    assert split_string(equal_gpus) == "24,24"


def test_split_string_mixed_gpus(mock_gpus_mixed):
    """Test split string generation with mixed GPU sizes."""
    assert split_string(mock_gpus_mixed) == "24,10,40"


def test_tensor_fractions_equal(mock_gpus):
    """Test tensor fractions with equal GPUs."""
    # Take just the first two equal GPUs
    equal_gpus = mock_gpus[:2]
    assert tensor_fractions(equal_gpus) == [1.0, 1.0]


def test_tensor_fractions_mixed(mock_gpus_mixed):
    """Test tensor fractions with mixed GPU sizes."""
    fractions = tensor_fractions(mock_gpus_mixed)
    assert len(fractions) == 3
    assert fractions[0] == pytest.approx(0.6, abs=0.01)  # 24GB / 40GB
    assert fractions[1] == pytest.approx(0.25, abs=0.01) # 10GB / 40GB
    assert fractions[2] == pytest.approx(1.0, abs=0.01)  # 40GB / 40GB


def test_llama_command():
    """Test llama.cpp command generation."""
    model_path = "models/llama-7b.gguf"
    ctx_size = 4096
    split = "24,10"

    command = llama_command(model_path, ctx_size, split)

    assert model_path in command
    assert f"--gpu-split {split}" in command
    assert f"--ctx-size {ctx_size}" in command
    assert "--n-gpu-layers 999" in command


def test_vllm_command():
    """Test vLLM command generation."""
    model_path = "Mistral-7B-Instruct-v0.1"
    num_gpus = 3

    command = vllm_command(model_path, num_gpus)

    assert model_path in command
    assert f"--tensor-parallel-size {num_gpus}" in command
    assert "--dtype float16" in command


def test_make_env_file(mock_gpus, tmp_path):
    """Test environment file creation."""
    env_file = tmp_path / "env.sh"

    # Create env file
    result = make_env_file(mock_gpus, env_file)

    # Check result is the path
    assert result == env_file

    # Check file exists
    assert env_file.exists()

    # Check content
    content = env_file.read_text()
    assert "CUDA_VISIBLE_DEVICES=0,1,2" in content
    assert "NCCL_P2P_DISABLE=0" in content
    assert "OMP_NUM_THREADS" in content