# Québec-French Legal LLM

## Overview

This implementation adds a specialized Québec-French Legal LLM capability to the DualGPUOptimizer framework. It enables training, fine-tuning, and serving a legal-domain language model optimized for French-Canadian legal texts, with support for both high-end GPUs (A100) and consumer-grade hardware (dual GPUs with 8GB each).

## Key Features

1. **Data Pipeline**
   - Crawlers for LégisQuébec and CanLII French content
   - HTML cleaning and preprocessing
   - Document chunking with smart overlap

2. **Custom Tokenization**
   - SentencePiece-based tokenizer trained on legal French text
   - Legal-specific tokens for articles, paragraphs, etc.

3. **Efficient Fine-tuning**
   - QLoRA parameter-efficient fine-tuning
   - Adaptive batch sizing based on GPU telemetry
   - Memory-optimized training with dual-GPU support

4. **Evaluation Framework**
   - LexGLUE-FR benchmark integration
   - Detailed metrics and performance analysis

5. **RAG Implementation**
   - FAISS vector database for legal text retrieval
   - Citation injection for legal authority
   - Configurable context expansion

6. **Production API**
   - FastAPI with token-based authentication
   - Response streaming for better UX
   - Rate limiting and security considerations
   - Prometheus metrics integration

## Directory Structure

```
dualgpuopt/
├─ ingest/            # Data ingestion and processing
├─ tokenizer/         # Custom tokenizer training
├─ train/             # QLoRA fine-tuning
├─ eval/              # Model evaluation
├─ rag/               # Retrieval-augmented generation
└─ serve/             # API serving layer
```

## Setup and Usage

1. **Requirements Installation**
   ```
   pip install -r dualgpuopt/requirements_legal.txt
   ```

2. **Running the Pipeline**

   On Windows:
   ```
   run_legal_llm.bat --step all --preset dual_gpu_small
   ```

   On Linux/macOS:
   ```
   ./run_legal_llm.sh --step all --preset dual_gpu_small
   ```

3. **Step-by-Step Execution**
   - `--step prep`: Install dependencies
   - `--step ingest`: Process legal text data
   - `--step tokenize`: Train custom tokenizer
   - `--step train`: Fine-tune model with QLoRA
   - `--step evaluate`: Run evaluation on LexGLUE-FR
   - `--step rag`: Build FAISS index for retrieval
   - `--step serve`: Start the API server

4. **Model Configuration**

   The system includes presets for different hardware configurations:
   - `a100_bf16_large`: For A100 40GB GPU
   - `dual_gpu_small`: For dual consumer GPUs (8GB each)
   - `rtx_cpu_offload`: For single GPU with CPU/disk offload

## Integration with DualGPUOptimizer

This implementation leverages key DualGPUOptimizer features:

- **Engine Pool**: Hot-swapping model instances with health monitoring
- **Telemetry**: Real-time GPU metrics for adaptive batch sizing
- **Memory Planning**: Optimal tensor distribution across GPUs
- **VRAM Fit**: Context size calculations for different hardware
- **Prometheus Integration**: Real-time monitoring of training and serving

## Legal Compliance

The system is designed with legal compliance in mind:

- Only trained on public-domain content
- Citations included with every response
- Secured API with proper authentication
- Raw source files removed after processing

## Further Resources

For more detailed information, refer to:
- [README_LEGAL_LLM.md](dualgpuopt/README_LEGAL_LLM.md): Detailed documentation
- [run_legal_llm.bat](run_legal_llm.bat) / [run_legal_llm.sh](run_legal_llm.sh): Helper scripts
- [requirements_legal.txt](dualgpuopt/requirements_legal.txt): Dependencies
