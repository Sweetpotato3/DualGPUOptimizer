# Québec-French Legal LLM Integration

This document provides instructions for setting up and using the Québec-French Legal LLM integration with DualGPUOptimizer.

## Overview

The Québec-French Legal LLM is a specialized language model fine-tuned on French-language legal documents from Québec. It integrates with DualGPUOptimizer for efficient training, evaluation, and deployment, with features including:

- Data ingestion from LégisQuébec and CanLII (French)
- Custom SentencePiece tokenizer for French-Canadian legal text
- QLoRA fine-tuning with adaptive batch sizing
- Evaluation using LexGLUE-FR
- RAG retrieval with FAISS and citation injection
- FastAPI serving layer with authentication

## Setup

### 1. Requirements

Ensure you have the following dependencies installed:

```bash
pip install -r requirements_legal.txt
```

Or install components individually:

```bash
# Core dependencies
pip install peft datasets sentencepiece transformers accelerate

# RAG dependencies
pip install faiss-cpu sentence-transformers

# Serving dependencies
pip install fastapi uvicorn
```

### 2. Directory Structure

The integration consists of the following components:

```
dualgpuopt/
├─ ingest/            # Data ingestion and processing
├─ tokenizer/         # Custom tokenizer training
├─ train/             # QLoRA fine-tuning
├─ eval/              # Model evaluation
├─ rag/               # Retrieval-augmented generation
└─ serve/             # API serving layer
```

### 3. Data Collection

Run the Operator tasks to collect data from LégisQuébec and CanLII:

```bash
# Create directories for corpora
mkdir -p corpora/qc_statutes/raw corpora/canlii_fr/raw

# Run data collection (implementation details may vary)
python -m dualgpuopt.ingest.operator_tasks legisqc.json
python -m dualgpuopt.ingest.operator_tasks canlii_fr.json
```

### 4. Data Processing

Clean the collected HTML files and prepare the dataset:

```bash
# Clean HTML files
python -m dualgpuopt.ingest.clean_html corpora/qc_statutes/raw datasets/qc_legal_clean.jsonl

# Chunk the documents (optional)
python -m dualgpuopt.ingest.chunk_jsonl datasets/qc_legal_clean.jsonl datasets/qc_legal_chunks.jsonl --max-length 512 --overlap 64
```

### 5. Tokenizer Training

Train a custom SentencePiece tokenizer on the legal corpus:

```bash
python -m dualgpuopt.tokenizer.train_spm datasets/qc_legal_clean.jsonl tokenizer_frqc
```

### 6. Fine-tuning

Fine-tune the model using QLoRA:

```bash
# With a single A100
accelerate launch -m dualgpuopt.train.train_qlora --preset dualgpuopt/train/presets.yml#a100_bf16_large

# With dual consumer GPUs
accelerate launch -m dualgpuopt.train.train_qlora --preset dualgpuopt/train/presets.yml#dual_gpu_small
```

### 7. Evaluation

Evaluate the model on the LexGLUE-FR dataset:

```bash
python -m dualgpuopt.eval.lexglue_fr --model checkpoints/qc_legal/merged --output eval_results.json
```

### 8. RAG Index Building

Build a FAISS index for retrieval-augmented generation:

```bash
python -m dualgpuopt.rag.build_faiss datasets/qc_legal_clean.jsonl rag/qc.faiss
```

### 9. API Server

Start the FastAPI server for model serving:

```bash
# Set environment variables
export LEGAL_MODEL=checkpoints/qc_legal/merged
export LEGAL_API_KEY=your_secret_key
export FAISS_INDEX=rag/qc.faiss

# Start server
python -m dualgpuopt.serve.legal_api
```

## Usage

### API Endpoints

The API server provides the following endpoints:

- **POST /api/chat**: Main endpoint for legal queries with RAG
  ```
  curl -X POST "http://localhost:8080/api/chat" \
       -H "Content-Type: application/json" \
       -H "X-API-Key: your_secret_key" \
       -d '{"prompt": "Quelles sont les conditions pour un divorce au Québec?", "use_rag": true}'
  ```

- **GET /api/health**: Health check endpoint
  ```
  curl "http://localhost:8080/api/health"
  ```

- **POST /api/token**: Create new API tokens (admin only)
  ```
  curl -X POST "http://localhost:8080/api/token" \
       -H "Content-Type: application/json" \
       -d '{"admin_key": "admin_secret_key", "expires_in": 86400}'
  ```

### Environment Variables

Configure the API server with these environment variables:

| Variable            | Description                       | Default           |
|---------------------|-----------------------------------|-------------------|
| LEGAL_MODEL         | Path to the fine-tuned model      | models/qc_legal   |
| LEGAL_API_KEY       | API key for authentication        | dev_key           |
| FAISS_INDEX         | Path to the FAISS index           | rag/qc.faiss      |
| ENABLE_RAG          | Enable/disable RAG                | true              |
| MAX_TOKENS          | Maximum tokens to generate        | 512               |
| RATE_LIMIT          | Requests per minute limit         | 60                |
| ADMIN_API_KEY       | Admin key for token generation    | (none)            |
| PORT                | Server port                       | 8080              |

## Legal Compliance

The Québec-French Legal LLM is designed with legal compliance in mind:

- Only trained on public-domain content from LégisQuébec, CanLII, and the Gazette
- Citations included in every response to indicate source material
- API access controlled through authentication and rate limiting
- Raw source files removed after processing to avoid redistribution of copyrighted material

## Troubleshooting

- **Missing dependencies**: Run `pip install -r requirements_legal.txt`
- **GPU memory issues**: Use a smaller preset or enable CPU/disk offload
- **Model loading failures**: Check if the model path is correct and the model is properly saved
- **API authentication errors**: Verify API key is correctly set and passed in the header

For more information, refer to the DualGPUOptimizer documentation. 