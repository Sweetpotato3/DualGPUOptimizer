"""QLoRA wrapper using HF PEFT + adaptive batch callbacks."""
from __future__ import annotations

import argparse
import json
import logging
import os
from typing import Any, Optional

import torch
import yaml
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(preset_path: str) -> dict[str, Any]:
    """Load configuration from YAML file."""
    if "#" in preset_path:
        path, section = preset_path.split("#")
        with open(path) as f:
            config = yaml.safe_load(f)
        return config[section]
    with open(preset_path) as f:
        return yaml.safe_load(f)


def prepare_dataset(config: dict[str, Any], tokenizer):
    """Load and prepare dataset for training."""
    dataset = load_dataset("json", data_files=config["dataset"])["train"]

    # Function to tokenize inputs
    def tokenize_function(examples):
        # Tokenization with appropriate truncation and padding
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=2048,  # Adjust based on context length needs
            return_tensors="pt",
        )

    # Apply tokenization
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text"],
    )

    return tokenized_dataset


def train(config: dict[str, Any], output_dir: Optional[str] = None):
    """Run QLoRA training with the specified configuration."""
    # Configure output directory
    if output_dir:
        config["out"] = output_dir

    # Create output directory if it doesn't exist
    os.makedirs(config["out"], exist_ok=True)

    # Save configuration for reference
    with open(os.path.join(config["out"], "training_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    # Apply GPU memory planning if available
    device_map = "auto"
    if HAVE_DUALGPU:
        gpu_cfg = None if config.get("gpus") in (None, "auto") else config["gpus"]
        plan = fit_plan(config["model_bytes"], gpu_cfg)
        logger.info(f"GPU Memory Plan: {plan}")

        # Save the plan for reference
        with open(os.path.join(config["out"], "gpu_plan.json"), "w") as f:
            json.dump(plan, f, indent=2)

    # Load base model with 8-bit quantization for efficiency
    logger.info(f"Loading base model: {config['base_model']}")
    load_kwargs = dict(device_map=device_map)
    if config.get("quantization") == "int8":
        load_kwargs["load_in_8bit"] = True
    else:
        load_kwargs["torch_dtype"] = torch.bfloat16 if config.get("bf16") else torch.float16
    base_model = AutoModelForCausalLM.from_pretrained(
        config["base_model"],
        **load_kwargs,
    )

    # Load tokenizer
    logger.info(f"Loading tokenizer: {config['tokenizer']}")
    tokenizer = AutoTokenizer.from_pretrained(
        config["tokenizer"] if "/" in config["tokenizer"] else config["base_model"],
        use_fast=True,
    )

    # Configure QLoRA
    logger.info("Configuring QLoRA parameters")
    peft_config = LoraConfig(
        r=8,  # Rank
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],  # Target specific modules
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
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
        mlm=False,  # We're doing causal language modeling
    )

    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=config["out"],
        overwrite_output_dir=True,
        per_device_train_batch_size=config.get("bs", 4),
        gradient_accumulation_steps=config.get("gradient_accumulation_steps", 1),
        learning_rate=config.get("learning_rate", 2e-4),
        weight_decay=config.get("weight_decay", 0.01),
        adam_beta1=0.9,
        adam_beta2=0.999,
        max_grad_norm=1.0,
        num_train_epochs=config.get("epochs", 3),
        lr_scheduler_type=config.get("lr_scheduler", "cosine"),
        warmup_ratio=config.get("warmup_ratio", 0.03),
        log_level="info",
        logging_strategy="steps",
        logging_steps=50,
        save_strategy="steps",
        save_steps=2000,
        save_total_limit=3,
        fp16=config.get("quantization") != "int8" and not config.get("bf16", False),
        bf16=config.get("bf16", False),
        seed=42,
        report_to=["tensorboard"],
    )

    # Safety check: adjust batch size if too large for available GPUs
    device_count = torch.cuda.device_count() if torch.cuda.is_available() else 1
    total_batch_size = training_args.per_device_train_batch_size * device_count
    if total_batch_size > 16:
        logger.warning(
            f"Total batch size ({total_batch_size}) is too large, increasing gradient accumulation"
        )
        training_args.gradient_accumulation_steps *= 2
        logger.info(
            f"Adjusted gradient accumulation steps to {training_args.gradient_accumulation_steps}"
        )

    # Create trainer (use AdaptiveTrainer if available)
    if HAVE_DUALGPU and hasattr(batch_adaptor, "AdaptiveTrainer"):
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
    merged_output_dir = os.path.join(config["out"], "merged")
    os.makedirs(merged_output_dir, exist_ok=True)

    logger.info(f"Saving trained model to: {merged_output_dir}")
    model.save_pretrained(merged_output_dir)
    tokenizer.save_pretrained(merged_output_dir)

    # Save model card with training information
    with open(os.path.join(merged_output_dir, "README.md"), "w") as f:
        f.write("# Québec-French Legal LLM\n\n")
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
    parser.add_argument(
        "--preset",
        required=True,
        help="Path to preset config file, optionally with section (file.yml#section)",
    )
    parser.add_argument("--output-dir", help="Override output directory from preset")
    args = parser.parse_args()

    config = load_config(args.preset)
    train(config, args.output_dir)
