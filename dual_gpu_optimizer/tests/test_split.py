from dualgpuopt.optimizer import split_string, tensor_fractions
from dualgpuopt.gpu_info import GPU

def make(gb): return GPU(0,"dummy",gb*1024,gb*1024)

def test_split():
    gpus = [make(16), make(8)]
    assert split_string(gpus) == "16,8"
    assert tensor_fractions(gpus) == [1.0, 0.5] 