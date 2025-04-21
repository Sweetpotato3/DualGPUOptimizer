import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Import the optimizer module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dualgpuopt.optimizer import calculate_tensor_splits

class TestGpuSplit:
    """Test cases for the GPU split calculation functionality."""
    
    def test_equal_gpu_split(self, mock_gpu_list):
        """Test split calculation with equal GPU memory."""
        # Make both GPUs have the same memory
        mock_gpu_list[0].total_memory = 10 * 1024 * 1024 * 1024
        mock_gpu_list[0].available_memory = 8 * 1024 * 1024 * 1024
        mock_gpu_list[1].total_memory = 10 * 1024 * 1024 * 1024
        mock_gpu_list[1].available_memory = 8 * 1024 * 1024 * 1024
        
        model_size = 7 * 1024 * 1024 * 1024  # 7GB model
        
        # Call the function under test
        splits = calculate_tensor_splits(mock_gpu_list, model_size)
        
        # Verify equal split (approx 50-50)
        assert len(splits) == 2
        assert abs(splits[0] - 0.5) < 0.05
        assert abs(splits[1] - 0.5) < 0.05
        assert sum(splits) == pytest.approx(1.0)
    
    def test_unequal_gpu_split(self, mock_gpu_list):
        """Test split calculation with unequal GPU memory."""
        # Use default mock GPUs which have different memory
        model_size = 14 * 1024 * 1024 * 1024  # 14GB model
        
        # Call the function under test
        splits = calculate_tensor_splits(mock_gpu_list, model_size)
        
        # Verify proportional split (approx 37.5-62.5 based on 6GB and 10GB available)
        assert len(splits) == 2
        assert abs(splits[0] - 0.375) < 0.05
        assert abs(splits[1] - 0.625) < 0.05
        assert sum(splits) == pytest.approx(1.0)
    
    def test_single_gpu(self, mock_gpu_info):
        """Test with a single GPU."""
        model_size = 4 * 1024 * 1024 * 1024  # 4GB model
        
        # Call the function under test with a single GPU
        splits = calculate_tensor_splits([mock_gpu_info], model_size)
        
        # Verify a single split of 1.0
        assert len(splits) == 1
        assert splits[0] == pytest.approx(1.0)
    
    def test_model_too_large(self, mock_gpu_list):
        """Test when model is too large for available memory."""
        # Total available is 16GB (6GB + 10GB)
        model_size = 20 * 1024 * 1024 * 1024  # 20GB model
        
        # Expect ValueError or similar exception
        with pytest.raises(Exception):
            calculate_tensor_splits(mock_gpu_list, model_size)
    
    def test_zero_gpu_count(self):
        """Test with zero GPUs."""
        model_size = 4 * 1024 * 1024 * 1024  # 4GB model
        
        # Expect ValueError or similar exception
        with pytest.raises(Exception):
            calculate_tensor_splits([], model_size)
    
    def test_with_overhead(self, mock_gpu_list):
        """Test split calculation with system overhead consideration."""
        # Patch the overhead constant or use environment variable
        with patch.dict(os.environ, {"DUALGPUOPT_SYSTEM_OVERHEAD": "1073741824"}):  # 1GB overhead
            model_size = 13 * 1024 * 1024 * 1024  # 13GB model
            
            # Call the function under test
            splits = calculate_tensor_splits(mock_gpu_list, model_size)
            
            # Verify splits account for overhead
            assert len(splits) == 2
            # Should be more weighted toward larger GPU due to overhead
            assert splits[0] < 0.375  # Less than raw ratio
            assert splits[1] > 0.625  # More than raw ratio
            assert sum(splits) == pytest.approx(1.0) 