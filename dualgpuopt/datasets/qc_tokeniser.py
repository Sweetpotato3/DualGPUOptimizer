from __future__ import annotations

import itertools
import json
import uuid
from pathlib import Path

import sentencepiece as spm

RAW_DIR   = Path("datasets/raw_qc")
TOK_DIR   = Path("datasets/tokenizer_qc"); TOK_DIR.mkdir(parents=True, exist_ok=True)
SPM_MODEL = TOK_DIR/"spm.model"

def iter_text():
    for txt in RAW_DIR.rglob("*.txt"):
        yield txt.read_text(encoding="utf-8", errors="ignore")

def train():
    corpus_file = TOK_DIR/f"tmp_{uuid.uuid4().hex}.txt"
    corpus_file.write_text("\n".join(itertools.islice(iter_text(), 10_000_000)))
    spm.SentencePieceTrainer.Train(
        input=str(corpus_file),
        model_prefix=str(TOK_DIR/"spm"),
        vocab_size=50_000,
        character_coverage=0.9995,
        model_type="bpe",
        user_defined_symbols=["§", "«", "»"]
    )
    corpus_file.unlink()

if __name__ == "__main__":
    train()
    print("Trained tokenizer at", SPM_MODEL)
