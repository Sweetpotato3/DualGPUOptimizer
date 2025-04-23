import json
import pathlib
import statistics

import datasets
import torch
import transformers

from dualgpuopt.engine.pool.core import EnginePool

DEV_CSV = pathlib.Path("datasets/lexglue_fr_dev.csv")
CKPT    = pathlib.Path("checkpoints/legal-lora/full")

def test_macro_f1(tmp_path):
    assert CKPT.exists(), "Checkpoint missing – run training first"
    model = EnginePool.get(str(CKPT))          # warm from cache
    tok   = transformers.AutoTokenizer.from_pretrained(CKPT)
    y_true, y_pred = [], []
    for row in datasets.load_dataset("csv", data_files=str(DEV_CSV), split="train"):
        lab = row["label"]; txt = row["text"][:2048]
        out = "".join(model.stream(txt, max_tokens=32)).lower()
        y_true.append(lab)
        y_pred.append("favorable" if "rejeté" not in out else "rejeté")
    f1 = _macro_f1(y_true, y_pred)
    assert f1 >= 0.25, f"F1 too low: {f1:.2f}"

def _macro_f1(y, ŷ):
    from sklearn.metrics import f1_score; return f1_score(y, ŷ, average="macro")
