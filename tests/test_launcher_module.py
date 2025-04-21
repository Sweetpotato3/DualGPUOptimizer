"""
Tests for the Launcher module
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import tempfile
import json

# Add parent directory to path so we can import directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock tkinter before importing GUI modules
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['ttkbootstrap'] = MagicMock()

# Now import the module to be tested
from dualgpuopt.gui.launcher import launch_controller, parameter_resolver, model_validation, process_monitor, config_handler

class TestLaunchController(unittest.TestCase):
    """Tests for the Launch Controller module"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock the process monitor
        self.mock_process_monitor = MagicMock()
        self.patcher = patch('dualgpuopt.gui.launcher.launch_controller.ProcessMonitor', return_value=self.mock_process_monitor)
        self.patcher.start()

        # Mock the parameter resolver
        self.mock_parameter_resolver = MagicMock()
        self.mock_parameter_resolver.resolve_parameters.return_value = {
            'model_path': '/path/to/model',
            'context_size': 4096,
            'batch_size': 16,
            'gpu_split': '24:8',
            'command': 'python model.py --model /path/to/model --ctx 4096 --batch 16 --gpu-split 24:8'
        }
        self.resolver_patcher = patch('dualgpuopt.gui.launcher.launch_controller.ParameterResolver', return_value=self.mock_parameter_resolver)
        self.resolver_patcher.start()

        # Create a controller instance
        self.controller = launch_controller.LaunchController()

    def tearDown(self):
        """Tear down test fixtures"""
        self.patcher.stop()
        self.resolver_patcher.stop()

    def test_launch_model(self):
        """Test launch_model method"""
        # Test launching a model
        model_path = '/path/to/model'

        result = self.controller.launch_model(
            model_path=model_path,
            context_size=4096,
            batch_size=16,
            gpu_split='24:8'
        )

        # Should resolve parameters and start process
        self.mock_parameter_resolver.resolve_parameters.assert_called_once()
        self.mock_process_monitor.start_process.assert_called_once()

        # Should return True if successful
        self.assertTrue(result.success)

    def test_stop_model(self):
        """Test stop_model method"""
        # Test stopping a model
        self.controller.stop_model()

        # Should call stop_process on process monitor
        self.mock_process_monitor.stop_process.assert_called_once()

    def test_is_model_running(self):
        """Test is_model_running method"""
        # Test with running model
        self.mock_process_monitor.is_process_running.return_value = True
        self.assertTrue(self.controller.is_model_running())

        # Test with stopped model
        self.mock_process_monitor.is_process_running.return_value = False
        self.assertFalse(self.controller.is_model_running())

class TestParameterResolver(unittest.TestCase):
    """Tests for the Parameter Resolver module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a resolver instance
        self.resolver = parameter_resolver.ParameterResolver()

    def test_resolve_parameters(self):
        """Test resolve_parameters method"""
        # Test with valid parameters
        parameters = {
            'model_path': '/path/to/model',
            'context_size': 4096,
            'batch_size': 16,
            'gpu_split': '24:8'
        }

        result = self.resolver.resolve_parameters(parameters)

        # Should return a dictionary with resolved parameters
        self.assertIn('model_path', result)
        self.assertIn('context_size', result)
        self.assertIn('batch_size', result)
        self.assertIn('gpu_split', result)
        self.assertIn('command', result)

        # Command should include all parameters
        self.assertIn('/path/to/model', result['command'])
        self.assertIn('4096', result['command'])
        self.assertIn('16', result['command'])
        self.assertIn('24:8', result['command'])

    def test_build_command(self):
        """Test build_command method"""
        # Test with different model types

        # Test llama.cpp command
        parameters = {
            'model_path': '/path/to/llama.cpp/model.gguf',
            'context_size': 4096,
            'batch_size': 16,
            'gpu_split': '24:8'
        }

        command = self.resolver._build_command(parameters)

        # Command should include llama.cpp specific parameters
        self.assertIn('llama.cpp', command)
        self.assertIn('--ctx-size 4096', command)
        self.assertIn('--batch-size 16', command)
        self.assertIn('--gpu-split 24:8', command)

        # Test vLLM command
        parameters = {
            'model_path': '/path/to/vllm/model',
            'context_size': 4096,
            'batch_size': 16,
            'tensor_parallel_size': 2
        }

        command = self.resolver._build_command(parameters, model_type='vllm')

        # Command should include vLLM specific parameters
        self.assertIn('vllm', command)
        self.assertIn('--max-model-len 4096', command)
        self.assertIn('--tensor-parallel-size 2', command)

class TestModelValidation(unittest.TestCase):
    """Tests for the Model Validation module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a validator instance
        self.validator = model_validation.ModelValidator()

    def test_validate_model_path(self):
        """Test validate_model_path method"""
        # Test with valid path (mock exists check)
        with patch('os.path.exists', return_value=True):
            self.assertTrue(self.validator.validate_model_path('/valid/path/model.gguf'))

        # Test with invalid path
        with patch('os.path.exists', return_value=False):
            self.assertFalse(self.validator.validate_model_path('/invalid/path/model.gguf'))

        # Test with empty path
        self.assertFalse(self.validator.validate_model_path(''))

    def test_validate_context_size(self):
        """Test validate_context_size method"""
        # Test with valid context sizes
        self.assertTrue(self.validator.validate_context_size(1024))
        self.assertTrue(self.validator.validate_context_size(4096))
        self.assertTrue(self.validator.validate_context_size(8192))

        # Test with invalid context sizes
        self.assertFalse(self.validator.validate_context_size(0))
        self.assertFalse(self.validator.validate_context_size(-1))
        self.assertFalse(self.validator.validate_context_size(100000))  # Too large

    def test_validate_batch_size(self):
        """Test validate_batch_size method"""
        # Test with valid batch sizes
        self.assertTrue(self.validator.validate_batch_size(1))
        self.assertTrue(self.validator.validate_batch_size(16))
        self.assertTrue(self.validator.validate_batch_size(128))

        # Test with invalid batch sizes
        self.assertFalse(self.validator.validate_batch_size(0))
        self.assertFalse(self.validator.validate_batch_size(-1))
        self.assertFalse(self.validator.validate_batch_size(1025))  # Too large

class TestProcessMonitor(unittest.TestCase):
    """Tests for the Process Monitor module"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock subprocess
        self.mock_process = MagicMock()
        self.mock_process.poll.return_value = None  # Process running
        self.mock_popen = MagicMock(return_value=self.mock_process)
        self.patcher = patch('subprocess.Popen', self.mock_popen)
        self.patcher.start()

        # Create a monitor instance
        self.monitor = process_monitor.ProcessMonitor()

    def tearDown(self):
        """Tear down test fixtures"""
        self.patcher.stop()

    def test_start_process(self):
        """Test start_process method"""
        # Test starting a process
        command = 'python model.py --model /path/to/model'

        self.monitor.start_process(command)

        # Should call Popen
        self.mock_popen.assert_called_once()

        # Process should be set
        self.assertIsNotNone(self.monitor._process)

    def test_stop_process(self):
        """Test stop_process method"""
        # Start a process first
        self.monitor.start_process('dummy command')

        # Now stop it
        self.monitor.stop_process()

        # Should call terminate on the process
        self.mock_process.terminate.assert_called_once()

    def test_is_process_running(self):
        """Test is_process_running method"""
        # Test with no process
        self.assertFalse(self.monitor.is_process_running())

        # Test with running process
        self.monitor.start_process('dummy command')
        self.mock_process.poll.return_value = None  # Process still running
        self.assertTrue(self.monitor.is_process_running())

        # Test with terminated process
        self.mock_process.poll.return_value = 0  # Process terminated
        self.assertFalse(self.monitor.is_process_running())

class TestConfigHandler(unittest.TestCase):
    """Tests for the Config Handler module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temp file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()

        # Create a handler instance with the temp file
        self.handler = config_handler.ConfigHandler(config_path=self.temp_file.name)

        # Sample configuration
        self.sample_config = {
            'model_path': '/path/to/model',
            'context_size': 4096,
            'batch_size': 16,
            'gpu_split': '24:8'
        }

    def tearDown(self):
        """Tear down test fixtures"""
        # Remove temp file
        os.unlink(self.temp_file.name)

    def test_save_and_load_config(self):
        """Test save_config and load_config methods"""
        # Save configuration
        self.handler.save_config(self.sample_config)

        # Load configuration
        loaded_config = self.handler.load_config()

        # Should match the saved config
        self.assertEqual(loaded_config['model_path'], self.sample_config['model_path'])
        self.assertEqual(loaded_config['context_size'], self.sample_config['context_size'])
        self.assertEqual(loaded_config['batch_size'], self.sample_config['batch_size'])
        self.assertEqual(loaded_config['gpu_split'], self.sample_config['gpu_split'])

    def test_get_recent_models(self):
        """Test get_recent_models method"""
        # Save multiple configurations with different model paths
        config1 = self.sample_config.copy()
        config1['model_path'] = '/path/to/model1'

        config2 = self.sample_config.copy()
        config2['model_path'] = '/path/to/model2'

        config3 = self.sample_config.copy()
        config3['model_path'] = '/path/to/model3'

        # Save each config
        self.handler.save_config(config1)
        self.handler.save_config(config2)
        self.handler.save_config(config3)

        # Get recent models
        recent_models = self.handler.get_recent_models()

        # Should have all three models in reverse order
        self.assertEqual(len(recent_models), 3)
        self.assertEqual(recent_models[0], '/path/to/model3')
        self.assertEqual(recent_models[1], '/path/to/model2')
        self.assertEqual(recent_models[2], '/path/to/model1')

if __name__ == "__main__":
    unittest.main()