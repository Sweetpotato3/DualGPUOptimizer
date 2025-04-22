"""QLoRA wrapper using HF PEFT + adaptive batch callbacks."""
from __future__ import annotations
import argparse
import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    TrainingArguments,
    DataCollatorForLanguageModeling,
    Trainer
)
from peft import LoraConfig, get_peft_model, PeftModel

# Import DualGPUOptimizer components
try:
    from dualgpuopt.model.vram_fit import fit_plan
    from dualgpuopt.telemetry import batch_adaptor  # For adaptive batch sizing
    HAVE_DUALGPU = True
except ImportError:
    HAVE_DUALGPU = False
    print("Warning: DualGPUOptimizer not found, running without GPU optimization")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(preset_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if '#' in preset_path:
        path, section = preset_path.split('#')
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        return config[section]
    else:
        with open(preset_path, 'r') as f:
            return yaml.safe_load(f)

def prepare_dataset(config: Dict[str, Any], tokenizer):
    """Load and prepare dataset for training."""
    dataset = load_dataset('json', data_files=config['dataset'])['train']
    
    # Function to tokenize inputs
    def tokenize_function(examples):
        # Tokenization with appropriate truncation and padding
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=2048,  # Adjust based on context length needs
            return_tensors="pt"
        )
    
    # Apply tokenization
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text"]
    )
    
    return tokenized_dataset

def train(config: Dict[str, Any], output_dir: Optional[str] = None):
    """Run QLoRA training with the specified configuration."""
    # Configure output directory
    if output_dir:
        config['out'] = output_dir
    
    # Create output directory if it doesn't exist
    os.makedirs(config['out'], exist_ok=True)
    
    # Save configuration for reference
    with open(os.path.join(config['out'], 'training_config.json'), 'w') as f:
        json.dump(config, f, indent=2)
    
    # Apply GPU memory planning if available
    device_map = "auto"
    if HAVE_DUALGPU:
        plan = fit_plan(config['model_bytes'], config.get('gpus', None))
        logger.info(f"GPU Memory Plan: {plan}")
        
        # Save the plan for reference
        with open(os.path.join(config['out'], 'gpu_plan.json'), 'w') as f:
            json.dump(plan, f, indent=2)
    
    # Load base model with 8-bit quantization for efficiency
    logger.info(f"Loading base model: {config['base_model']}")
    base_model = AutoModelForCausalLM.from_pretrained(
        config['base_model'],
        load_in_8bit=True,  # Use 8-bit quantization for memory efficiency
        device_map=device_map,
        torch_dtype=torch.float16
    )
    
    # Load tokenizer
    logger.info(f"Loading tokenizer: {config['tokenizer']}")
    tokenizer = AutoTokenizer.from_pretrained(
        config['tokenizer'] if '/' in config['tokenizer'] else config['base_model'],
        use_fast=True
    )
    
    # Configure QLoRA
    logger.info("Configuring QLoRA parameters")
    peft_config = LoraConfig(
        r=8,  # Rank
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],  # Target specific modules
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # Apply LoRA adapters
    logger.info("Applying LoRA adapters to model")
    model = get_peft_model(base_model, peft_config)
    
    # Print trainable parameters info
    model.print_trainable_parameters()
    
    # Prepare dataset
    logger.info(f"Loading dataset: {config['dataset']}")
    tokenized_dataset = prepare_dataset(config, tokenizer)
    
    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False  # We're doing causal language modeling
    )
    
    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=config['out'],
        overwrite_output_dir=True,
        per_device_train_batch_size=config.get('bs', 4),
        gradient_accumulation_steps=config.get('gradient_accumulation_steps', 1),
        learning_rate=config.get('learning_rate', 2e-4),
        weight_decay=config.get('weight_decay', 0.01),
        adam_beta1=0.9,
        adam_beta2=0.999,
        max_grad_norm=1.0,
        num_train_epochs=config.get('epochs', 3),
        lr_scheduler_type=config.get('lr_scheduler', 'cosine'),
        warmup_ratio=config.get('warmup_ratio', 0.03),
        log_level="info",
        logging_strategy="steps",
        logging_steps=50,
        save_strategy="steps",
        save_steps=2000,
        save_total_limit=3,
        fp16=True,
        bf16=config.get('bf16', False),
        seed=42,
        report_to=["tensorboard"],
    )
    
    # Create trainer (use AdaptiveTrainer if available)
    if HAVE_DUALGPU and hasattr(batch_adaptor, 'AdaptiveTrainer'):
        logger.info("Using AdaptiveTrainer with dynamic batch sizing")
        trainer = batch_adaptor.AdaptiveTrainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )
    else:
        logger.info("Using standard HuggingFace Trainer")
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )
    
    # Start training
    logger.info("Starting QLoRA training")
    trainer.train()
    
    # Save the final model
    merged_output_dir = os.path.join(config['out'], 'merged')
    os.makedirs(merged_output_dir, exist_ok=True)
    
    logger.info(f"Saving trained model to: {merged_output_dir}")
    model.save_pretrained(merged_output_dir)
    tokenizer.save_pretrained(merged_output_dir)
    
    # Save model card with training information
    with open(os.path.join(merged_output_dir, 'README.md'), 'w') as f:
        f.write(f"# Québec-French Legal LLM\n\n")
        f.write(f"This model was fine-tuned from {config['base_model']} on {config['dataset']} ")
        f.write(f"using QLoRA for {config.get('epochs', 3)} epochs.\n\n")
        f.write("## Training Configuration\n\n")
        f.write("```yaml\n")
        yaml.dump(config, f)
        f.write("```\n")
    
    logger.info("Training completed successfully!")
    return merged_output_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QLoRA training for French legal LLM")
    parser.add_argument('--preset', required=True, help='Path to preset config file, optionally with section (file.yml#section)')
    parser.add_argument('--output-dir', help='Override output directory from preset')
    args = parser.parse_args()
    
    config = load_config(args.preset)
    train(config, args.output_dir) 