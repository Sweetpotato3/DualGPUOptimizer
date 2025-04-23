#!/bin/bash
# run_legal_llm.sh - Helper script for Québec-French Legal LLM

# Set default values
PRESET="a100_bf16_large"
STEP="all"
DATA_DIR="corpora"
OUTPUT_DIR="datasets"
MODEL_DIR="checkpoints/qc_legal"
INDEX_DIR="rag"
PORT=8080

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --step)
      STEP="$2"
      shift 2
      ;;
    --preset)
      PRESET="$2"
      shift 2
      ;;
    --data-dir)
      DATA_DIR="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --model-dir)
      MODEL_DIR="$2"
      shift 2
      ;;
    --index-dir)
      INDEX_DIR="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --step STEP       Step to run (prep, ingest, tokenize, train, evaluate, rag, serve, all)"
      echo "  --preset PRESET   Training preset to use (a100_bf16_large, dual_gpu_small, etc.)"
      echo "  --data-dir DIR    Directory for raw data"
      echo "  --output-dir DIR  Directory for processed data"
      echo "  --model-dir DIR   Directory for model checkpoints"
      echo "  --index-dir DIR   Directory for RAG indices"
      echo "  --port PORT       Port for API server"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create necessary directories
mkdir -p $DATA_DIR/qc_statutes/raw $DATA_DIR/canlii_fr/raw $OUTPUT_DIR $MODEL_DIR $INDEX_DIR

echo "Running Québec-French Legal LLM: Step=$STEP, Preset=$PRESET"

case $STEP in
  prep|all)
    echo "=== Preparing environment ==="
    pip install -r dualgpuopt/requirements_legal.txt
    ;;
esac

case $STEP in
  ingest|all)
    echo "=== Data ingestion ==="
    echo "Crawling LégisQuébec..."
    python -m dualgpuopt.ingest.clean_html $DATA_DIR/qc_statutes/raw $OUTPUT_DIR/qc_legal_clean.jsonl

    echo "Chunking documents..."
    python -m dualgpuopt.ingest.chunk_jsonl $OUTPUT_DIR/qc_legal_clean.jsonl $OUTPUT_DIR/qc_legal_chunks.jsonl --max-length 512 --overlap 64
    ;;
esac

case $STEP in
  tokenize|all)
    echo "=== Training tokenizer ==="
    python -m dualgpuopt.tokenizer.train_spm $OUTPUT_DIR/qc_legal_clean.jsonl tokenizer_frqc
    ;;
esac

case $STEP in
  train|all)
    echo "=== Training model ==="
    accelerate launch -m dualgpuopt.train.train_qlora --preset dualgpuopt/train/presets.yml#$PRESET
    ;;
esac

case $STEP in
  evaluate|all)
    echo "=== Evaluating model ==="
    python -m dualgpuopt.eval.lexglue_fr --model $MODEL_DIR/merged --output $OUTPUT_DIR/eval_results.json
    echo "Evaluation results:"
    cat $OUTPUT_DIR/eval_results.json
    ;;
esac

case $STEP in
  rag|all)
    echo "=== Building RAG index ==="
    python -m dualgpuopt.rag.build_faiss $OUTPUT_DIR/qc_legal_clean.jsonl $INDEX_DIR/qc.faiss
    ;;
esac

case $STEP in
  serve|all)
    echo "=== Starting API server ==="
    # Generate a random API key if not specified
    if [ -z "$LEGAL_API_KEY" ]; then
      export LEGAL_API_KEY=$(openssl rand -hex 16)
      echo "Generated API key: $LEGAL_API_KEY"
    fi

    export LEGAL_MODEL=$MODEL_DIR/merged
    export FAISS_INDEX=$INDEX_DIR/qc.faiss
    export PORT=$PORT

    python -m dualgpuopt.serve.legal_api
    ;;
esac

echo "Done!"
