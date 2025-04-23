from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

import bitsandbytes as bnb
import datasets
import peft
import torch
import transformers
from prometheus_client import Gauge

from dualgpuopt.engine.metrics import record_model_load_time
from dualgpuopt.model.vram_fit import fit_plan

TOK_S = Gauge("train_tokens_sec", "...")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", required=True)
    ap.add_argument("--dataset_path", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--epochs", type=int, default=3)
    args = ap.parse_args()

    plan = fit_plan(Path(args.base_model).stat().st_size, [{"memory_total": torch.cuda.get_device_properties(0).total_memory/1024**2}])
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        args.base_model, trust_remote_code=True,
        tokenizer_file="datasets/tokenizer_qc/spm.model" if Path("datasets/tokenizer_qc/spm.model").exists() else None
    )

    ds = datasets.load_dataset("json", data_files=args.dataset_path, split="train")
    ds = ds.map(lambda x: tokenizer(x["text"]), remove_columns=["text"])

    model = transformers.AutoModelForCausalLM.from_pretrained(
        args.base_model,
        load_in_8bit=True,
        device_map="auto",
        quantization_config=bnb.QuantizationConfig(load_in_8bit=True)
    )
    lora_cfg = peft.LoraConfig(r=64, lora_alpha=16, lora_dropout=0.05)
    model = peft.get_peft_model(model, lora_cfg)

    # adaptive batch – aim at 90 % VRAM
    max_batch = int(os.environ.get("PER_DEVICE_BATCH", int(plan["gpu_layers"]/4) if "gpu_layers" in plan else 64))
    train_args = transformers.TrainingArguments(
        args.output_dir, num_train_epochs=args.epochs,
        per_device_train_batch_size=max_batch,
        optim="paged_adamw_32bit",
        save_strategy="epoch", logging_steps=25,
        report_to=[]
    )

    def tok_sec_callback(logs):
        if "loss" in logs:
            step = logs["global_step"]
            epoch = logs.get("epoch", 0)
            total_epochs = args.epochs
            pct = min(99, int(epoch * 100 / total_epochs)) if total_epochs > 0 else 0

            tok_s = logs["train_runtime"] and logs["train_tokens_processed"]/logs["train_runtime"]
            loss = logs.get("loss", 0.0)

            if tok_s:
                TOK_S.set(tok_s)
                print(f"Epoch {math.floor(epoch)}/{total_epochs} | Step {step} {pct}% | tok/s:{tok_s:.1f} loss:{loss:.4f}")

    trainer = transformers.Trainer(model, train_args, train_dataset=ds, callbacks=[tok_sec_callback])
    start = time.time(); trainer.train(); dur = time.time()-start

    model.save_pretrained(args.output_dir+"/full")          # merged adapter
    record_model_load_time(args.base_model, "QLoRA", dur)
    print("Training complete")

if __name__ == "__main__":
    main()
