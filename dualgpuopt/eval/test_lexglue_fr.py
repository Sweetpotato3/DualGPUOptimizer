"""
Unit tests for the lexglue_fr evaluation module.
"""
import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

from datasets import Dataset

# Import the module to test
from dualgpuopt.eval.lexglue_fr import evaluate_lexglue_fr

class TestLexGlueEvaluation(unittest.TestCase):
    """Test cases for the LexGLUE evaluation module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock dataset
        self.mock_dataset = Dataset.from_dict({
            'text': [
                'Le tribunal rejette la demande.',
                'La cour accorde l\'ordonnance.',
                'Le juge statue en faveur du défendeur.'
            ],
            'label': ['REJECT', 'ACCEPT', 'REJECT']
        })
        
        # Create a temporary file for output testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_file = os.path.join(self.temp_dir.name, 'results.json')
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @patch('transformers.pipeline')
    @patch('datasets.load_dataset')
    def test_perfect_accuracy(self, mock_load_dataset, mock_pipeline):
        """Test evaluation with perfect predictions."""
        # Configure mocks
        mock_load_dataset.return_value = self.mock_dataset
        
        # Mock the pipeline to always return the correct label
        mock_pipe = MagicMock()
        mock_pipe.side_effect = lambda text, truncation, max_length: [
            {'label': 'REJECT' if 'rejette' in text else 'ACCEPT'}
        ]
        mock_pipeline.return_value = mock_pipe
        
        # Run evaluation
        results = evaluate_lexglue_fr('fake/model/path', self.output_file)
        
        # Check results
        self.assertEqual(results['accuracy'], 1.0)
        self.assertEqual(results['correct_count'], 3)
        self.assertEqual(results['total_samples'], 3)
        
        # Verify output file
        with open(self.output_file, 'r') as f:
            saved_results = json.load(f)
        
        self.assertEqual(saved_results['metrics']['accuracy'], 1.0)
        self.assertEqual(len(saved_results['predictions']), 3)
    
    @patch('transformers.pipeline')
    @patch('datasets.load_dataset')
    def test_partial_accuracy(self, mock_load_dataset, mock_pipeline):
        """Test evaluation with some incorrect predictions."""
        # Configure mocks
        mock_load_dataset.return_value = self.mock_dataset
        
        # Mock the pipeline to return incorrect label for one example
        mock_pipe = MagicMock()
        mock_pipe.side_effect = lambda text, truncation, max_length: [
            {'label': 'ACCEPT' if 'tribunal' in text else 'REJECT'}
        ]
        mock_pipeline.return_value = mock_pipe
        
        # Run evaluation
        results = evaluate_lexglue_fr('fake/model/path')
        
        # Check results (2 out of 3 incorrect = 33.33% accuracy)
        self.assertAlmostEqual(results['accuracy'], 1/3)
        self.assertEqual(results['correct_count'], 1)
        self.assertEqual(results['total_samples'], 3)
    
    @patch('transformers.pipeline')
    @patch('datasets.load_dataset')
    def test_max_samples(self, mock_load_dataset, mock_pipeline):
        """Test evaluation with max_samples parameter."""
        # Configure mocks
        mock_load_dataset.return_value = self.mock_dataset
        
        mock_pipe = MagicMock()
        mock_pipe.side_effect = lambda text, truncation, max_length: [{'label': 'REJECT'}]
        mock_pipeline.return_value = mock_pipe
        
        # Run evaluation with max_samples=1
        results = evaluate_lexglue_fr('fake/model/path', max_samples=1)
        
        # Should only process the first sample
        self.assertEqual(results['total_samples'], 1)
    
    @patch('transformers.pipeline')
    @patch('datasets.load_dataset')
    def test_exception_handling(self, mock_load_dataset, mock_pipeline):
        """Test handling of exceptions during evaluation."""
        # Configure mocks
        mock_load_dataset.return_value = self.mock_dataset
        
        # Mock the pipeline to raise an exception on the second sample
        mock_pipe = MagicMock()
        mock_pipe.side_effect = lambda text, truncation, max_length: [
            {'label': 'REJECT'}
        ] if 'tribunal' in text else RuntimeError("Test error")
        mock_pipeline.return_value = mock_pipe
        
        # Run evaluation
        results = evaluate_lexglue_fr('fake/model/path')
        
        # Should only have one correct prediction out of three samples
        self.assertEqual(results['correct_count'], 1)
        self.assertEqual(results['total_samples'], 3)
        self.assertAlmostEqual(results['accuracy'], 1/3)

if __name__ == '__main__':
    unittest.main() 