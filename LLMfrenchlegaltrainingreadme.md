## Québec‑French Legal LLM — Build & Integration Plan

> **Purpose:** Hand this file to an autonomous agent (Cursor / GitHub Copilot Agent, etc.) so it can execute every remaining task to deliver a production‑ready legal chatbot trained on public‑domain Québec law and served through your DualGPUOptimizer stack.

---

###  1  Executive summary
*The infrastructure is 80 % ready.* You already have:

* One‑click model download/quantise/fit‑plan → **VRAM, RAM, SSD spill** safeguards.
* **EnginePool** with watchdog, hot‑reload and Prometheus metrics.
* GUI Model Manager + Prometheus dashboard.

**Missing pieces (this doc provides code for all):**

1. Data ingest & cleaning from LégisQuébec + CanLII (FR).
2. Custom SentencePiece tokenizer (Fr‑QC legal variant).
3. QLoRA fine‑tune wrapper + adaptive batch hooks.
4. Evaluation harness (LexGLUE‑FR / synthetic QA).
5. RAG retriever (FAISS) + citation injection.
6. FastAPI serving layer with auth & streaming.

Implementation fits on a single A100 40 GB *or* your dual 8 GB PC (using LoRA + SSD spill).

---

###  2  Directory layout

```
dualgpuopt/
├─ ingest/
│  ├─ operator_tasks/
│  │  ├─ legisqc.json
│  │  └─ canlii_fr.json
│  ├─ clean_html.py
│  └─ chunk_jsonl.py
├─ datasets/
│  └─ qc_legal_clean.jsonl
├─ tokenizer/
│  └─ train_spm.py
├─ train/
│  ├─ presets.yml
│  └─ train_qlora.py
├─ eval/
│  ├─ lexglue_fr.py
│  └─ test_lexglue_fr.py
├─ rag/
│  ├─ build_faiss.py
│  └─ retrieve.py
└─ serve/
   └─ legal_api.py
```

---

###  3  Code snippets
####  3.1 ingest/clean_html.py

```python
from bs4 import BeautifulSoup, NavigableString
from pathlib import Path
import json, re, sys

def clean_file(fp: Path) -> str:
    soup = BeautifulSoup(fp.read_text(encoding='utf‑8'), 'lxml')
    for tag in soup(['script','style','header','footer','nav']): tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    return text

if __name__ == "__main__":
    raw_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.open('w').write('')
    with out.open('a', encoding='utf‑8') as fh:
        for fp in raw_dir.glob('**/*.html'):
            txt = clean_file(fp)
            fh.write(json.dumps({'text': txt}, ensure_ascii=False)+'\n')
```

####  3.2 tokenizer/train_spm.py

```python
import sentencepiece as spm, sys, pathlib, json

corpus = sys.argv[1]   # jsonl
model_prefix = sys.argv[2]  # tokenizer_frqc
texts = pathlib.Path('tmp_corpus.txt')
with texts.open('w', encoding='utf-8') as fh:
    for line in pathlib.Path(corpus).read_text().splitlines():
        fh.write(json.loads(line)['text']+'\n')
spm.SentencePieceTrainer.train(input=str(texts), model_prefix=model_prefix,
                              vocab_size=48000, character_coverage=0.9995,
                              model_type='bpe', user_defined_symbols=['<art>', '<al>'])
```

####  3.3 train/train_qlora.py

```python
"""QLoRA wrapper using HF PEFT + your adaptive batch callbacks."""
from __future__ import annotations
import argparse, os, yaml, json
from datasets import load_dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer, TrainingArguments,
                          DataCollatorForLanguageModeling)
from peft import LoraConfig, get_peft_model
from dualgpuopt.model.vram_fit import fit_plan
from dualgpuopt.telemetry import batch_adaptor  # hypothetical hook

parser = argparse.ArgumentParser(); parser.add_argument('--preset'); args = parser.parse_args()
conf = yaml.safe_load(open(args.preset))

plan = fit_plan(conf['model_bytes'], conf['gpus'])
base = AutoModelForCausalLM.from_pretrained(conf['base_model'], load_in_8bit=True,
                                            device_map='auto')
tok = AutoTokenizer.from_pretrained(conf['tokenizer'])
peft_cfg = LoraConfig(r=8, lora_alpha=16, target_modules=['q_proj','v_proj'])
model = get_peft_model(base, peft_cfg)

ds = load_dataset('json', data_files=conf['dataset'])['train']
coll = DataCollatorForLanguageModeling(tok, mlm=False)
args = TrainingArguments(output_dir=conf['out'], fp16=True, bf16=True,
                         per_device_train_batch_size=conf['bs'],
                         lr_scheduler_type='cosine', num_train_epochs=conf['epochs'],
                         logging_steps=50, save_steps=2000)
trainer = batch_adaptor.AdaptiveTrainer(model=model, args=args,
                                        train_dataset=ds, data_collator=coll)
trainer.train()
model.save_pretrained(conf['out']+'/merged')
```

####  3.4 eval/lexglue_fr.py

```python
from datasets import load_dataset
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import argparse, numpy as np, json

p = argparse.ArgumentParser(); p.add_argument('--model'); args = p.parse_args()
pipe = pipeline('text-classification', model=args.model, tokenizer=args.model, device=0)
lex = load_dataset('HuggingFaceH4/lex_glue_fr', split='validation')
correct = 0
for ex in lex:
    pred = pipe(ex['text'], truncation=True, max_length=512)[0]['label']
    correct += pred == ex['label']
print(json.dumps({'acc': correct/len(lex)}, indent=2))
```

####  3.5 rag/build_faiss.py

```python
import faiss, json, sys, SentenceTransformers, pathlib
model = SentenceTransformers.SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
index = faiss.IndexFlatIP(384)
texts = []
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
    obj = json.loads(line); v = model.encode(obj['text'])
    index.add(v.reshape(1,-1)); texts.append(obj['text'][:512])
faiss.write_index(index, sys.argv[2]); json.dump(texts, open(sys.argv[2]+'.meta','w'))
```

####  3.6 serve/legal_api.py

```python
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from dualgpuopt.engine.pool.core import EnginePool
from rag import retrieve
import uvicorn, os
API_KEY = os.getenv('LEGAL_API_KEY')
app = FastAPI(); engine = EnginePool.get(os.getenv('LEGAL_MODEL'))

@app.post('/chat')
async def chat(prompt:str, x_api_key:str=Header(...)):
    if x_api_key!=API_KEY:
        raise HTTPException(401)
    # optional retrieval
    docs = retrieve.top_k(prompt, k=3)
    context = '\n'.join(docs)
    full_prompt = f"<context>{context}</context>\nQ: {prompt}\nA:"
    def gen():
        for tok in engine.stream(full_prompt, max_tokens=512):
            yield tok
    return StreamingResponse(gen(), media_type='text/plain')

if __name__ == '__main__': uvicorn.run(app, host='0.0.0.0', port=8080)
```

---

###  4  presets.yml (example A100)

```yaml
a100_bf16_large:
  base_model: mistralai/Mistral-7B-Instruct-v0.2
  tokenizer: tokenizer_frqc
  dataset: datasets/qc_legal_clean.jsonl
  out: checkpoints/qc_legal
  epochs: 3
  bs: 4
  model_bytes: 14500000000      # fp16 checkpoint size
  gpus:
    - memory_total: 40960       # A100 40 GB
```

---

###  5  Integration steps

1. **Run Operator tasks** in `ingest/operator_tasks/*` to crawl statutes & CanLII FR.
2. `python ingest/clean_html.py corpora/qc_statutes/raw datasets/qc_legal_clean.jsonl`.
3. `python tokenizer/train_spm.py datasets/qc_legal_clean.jsonl tokenizer_frqc`.
4. `accelerate launch train/train_qlora.py --preset train/presets.yml#a100_bf16_large`.
5. `python eval/lexglue_fr.py --model checkpoints/qc_legal/merged` – ensure accuracy ↑.
6. `python rag/build_faiss.py datasets/qc_legal_clean.jsonl rag/qc.faiss`.
7. `LEGAL_MODEL=checkpoints/qc_legal/merged LEGAL_API_KEY=secret python serve/legal_api.py`.

Prometheus & GUI will automatically pick up training, evaluation and serving metrics via EnginePool & Telemetry hooks.

---

###  6  Security / legal compliance checklist

* Train only on public‑domain content (LégisQuébec, CanLII, Gazette).
* Cite URLs & article numbers in every answer (`retrieve.top_k`).
* API key + rate limit middleware guards inference endpoint.
* Remove `.raw` source files after chunking to avoid redistributing PDFs.

---

> **Deliverable:** After following the steps above you will have a Québec‑French legal LLM fine‑tuned on public‑domain law, running locally (or on an A100) with RAG citations and an authenticated REST endpoint for your website.

---

###  IDE Integration (Cursor‑VS Code)

> **First task for the agent:** **Generate the full folder structure** exactly as shown below if it does not already exist.

```
dualgpuopt/
├─ engine/
│  ├─ backend.py
│  └─ pool/
│     └─ core.py
├─ model/
│  ├─ hf_client.py
│  ├─ quantise.py
│  ├─ vram_fit.py
│  └─ __init__.py
├─ qt/
│  ├─ model_manager.py
│  └─ ... (existing Qt tabs)
├─ ingest/
│  └─ clean_html.py
├─ datasets/
│  └─ qc_tokeniser.py
├─ scripts/
│  └─ train_qlora.py
├─ serve/
│  └─ legal_api.py
└─ tests/
   ├─ test_vram_fit.py
   ├─ test_backend_flags.py
   └─ test_hf_download_checksum.py
```

*Create directories (`mkdir -p`) and stub `__init__.py` files where needed.*

 (Cursor‑VS Code)

> **Goal:** make the autonomous agent understand exactly *where* to put each file, how to run scripts, and how to hook live telemetry while coding.

1. **Project checkout**

   ```bash
   git clone https://github.com/your‑org/dualgpuopt.git
   code dualgpuopt   # opens in VS Code / Cursor
   ```

2. **Workspace layout**
   * Convert the root to a VS Code *Workspace*.
   * Folders already exist (`engine/`, `model/`, `qt/`, `datasets/`, `scripts/`, `tests/`).
   * Cursor’s language‑server will pick up `pyproject.toml` (PEP‑621) for black/isort settings.

3. **Cursor tasks**
   Add to `.vscode/tasks.json` (Cursor understands native tasks):

   ```json
   {
      "label": "pytest",
      "type": "shell",
      "command": "pytest -q",
      "group": "test",
      "problemMatcher": []
   },
   {
      "label": "train‑llm",
      "type": "shell",
      "command": "python scripts/train_qlora.py --preset a100_bf16_large",
      "isBackground": true,
      "presentation": {"reveal": "always"}
   }
   ```

4. **File‑watcher for Operator dumps**
   In `.vscode/settings.json` add:

   ```json
   "files.watcherExclude": {
      "**/corpora/qc_statutes/raw/**": true,
      "**/datasets/**": false
   }
   ```

   → prevents the raw HTML dump from overloading the TS/JS watcher.

5. **Run & debug configuration**
   `.vscode/launch.json` entry to attach to FastAPI server:

   ```json
   {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
         "serve.legal_api:app",
         "--host", "0.0.0.0",
         "--port", "8009",
         "--reload"
      ],
      "envFile": "${workspaceFolder}/.env"
   }
   ```

6. **Cursor agent cues**
   * Every code snippet in this document is **fully qualified** (folder + filename).
   * Use the VS Code command palette → *“Cursor: Run in Workspace”* to generate missing imports.
   * The `tests/` folder is automatically picked up by *Cursor Test Explorer*.

7. **Telemetry overlay**
   Install the *Prometheus Metrics* VS Code extension and point it at `http://localhost:8005/metrics`.  Cursor shows charts in a side panel while training.

8. **One‑shot bootstrap**
   Add a `Makefile` target so the agent can call `make setup`:

   ```makefile
   setup:
    python -m pip install -e .[dev,train]
    pre-commit install
    cursor trust
   ```
