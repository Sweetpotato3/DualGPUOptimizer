"""
Evaluation script for French legal LLM using LexGLUE-FR.
"""
from datasets import load_dataset
from transformers import pipeline
import argparse
import json
import logging
from typing import Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def evaluate_lexglue_fr(model_path: str, output_file: str = None, max_samples: int = None) -> Dict[str, float]:
    """
    Evaluate model performance on LexGLUE-FR dataset.
    
    Args:
        model_path: Path to the model
        output_file: Optional path to save results
        max_samples: Maximum number of samples to evaluate (for testing)
        
    Returns:
        Dictionary with accuracy metrics
    """
    logger.info(f"Loading model from {model_path}")
    
    # Load the model for text classification
    try:
        pipe = pipeline(
            'text-classification', 
            model=model_path, 
            tokenizer=model_path, 
            device=0
        )
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise
    
    # Load LexGLUE-FR dataset
    logger.info("Loading LexGLUE-FR dataset")
    try:
        lex_dataset = load_dataset('HuggingFaceH4/lex_glue_fr', split='validation')
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise
    
    # Limit samples if specified (for debugging/testing)
    if max_samples and max_samples > 0:
        lex_dataset = lex_dataset.select(range(min(max_samples, len(lex_dataset))))
    
    logger.info(f"Evaluating on {len(lex_dataset)} samples")
    
    correct = 0
    predictions = []
    
    # Process samples
    for i, example in enumerate(lex_dataset):
        if i % 10 == 0:
            logger.info(f"Processing sample {i+1}/{len(lex_dataset)}")
        
        try:
            # Make prediction
            prediction = pipe(
                example['text'], 
                truncation=True, 
                max_length=512
            )[0]['label']
            
            # Check if correct
            is_correct = prediction == example['label']
            correct += int(is_correct)
            
            # Store prediction
            predictions.append({
                'text': example['text'][:100] + '...',  # Truncate for readability
                'true_label': example['label'],
                'predicted_label': prediction,
                'correct': is_correct
            })
            
        except Exception as e:
            logger.error(f"Error processing sample {i}: {e}")
            continue
    
    # Calculate metrics
    accuracy = correct / len(lex_dataset) if len(lex_dataset) > 0 else 0
    
    # Prepare results
    results = {
        'accuracy': accuracy,
        'correct_count': correct,
        'total_samples': len(lex_dataset),
        'model_path': model_path
    }
    
    logger.info(f"Evaluation complete: {results}")
    
    # Save detailed results if output file is specified
    if output_file:
        detailed_results = {
            'metrics': results,
            'predictions': predictions
        }
        
        with open(output_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        logger.info(f"Detailed results saved to {output_file}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate French legal LLM on LexGLUE-FR")
    parser.add_argument('--model', required=True, help='Path to the model')
    parser.add_argument('--output', help='Path to save detailed results')
    parser.add_argument('--max-samples', type=int, help='Maximum number of samples to evaluate')
    args = parser.parse_args()
    
    results = evaluate_lexglue_fr(args.model, args.output, args.max_samples)
    
    # Print results to stdout as JSON
    print(json.dumps(results, indent=2)) 