#!/bin/bash
# Run script for Quebec-French Legal LLM components

set -e

# Auto-detect GPU configuration and set preset
if nvidia-smi --query-gpu=memory.total --format=csv,noheader | grep -q 40000; then
    PRESET=a100_bf16_large
else
    PRESET=auto_hetero
fi

echo "Selected preset: $PRESET"

# Parse command line arguments
STEP="all"
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
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--step <step>] [--preset <preset>]"
            echo "Steps: prep, ingest, tokenize, train, evaluate, rag, serve, all"
            exit 1
            ;;
    esac
done

BASE_DIR=$(pwd)
DATASETS_DIR="$BASE_DIR/datasets"
CORPUS_DIR="$BASE_DIR/corpora"

# Create necessary directories
mkdir -p "$DATASETS_DIR" "$CORPUS_DIR/qc_statutes/raw" "$CORPUS_DIR/canlii_fr/raw"

# Run a specific step or all steps
case $STEP in
    prep)
        echo "Installing dependencies..."
        pip install -r dualgpuopt/requirements_legal.txt
        ;;
    ingest)
        echo "Running data ingestion..."
        python -m dualgpuopt.ingest.operator_tasks.legisqc
        python -m dualgpuopt.ingest.operator_tasks.canlii_fr
        python -m dualgpuopt.ingest.clean_html "$CORPUS_DIR/qc_statutes/raw" "$DATASETS_DIR/qc_legal_clean.jsonl"
        ;;
    tokenize)
        echo "Training custom tokenizer..."
        python -m dualgpuopt.tokenizer.train_spm "$DATASETS_DIR/qc_legal_clean.jsonl" tokenizer_frqc
        ;;
    train)
        echo "Running QLoRA fine-tuning with preset $PRESET..."
        accelerate launch -m dualgpuopt.train.train_qlora --preset "dualgpuopt/train/presets.yml#$PRESET"
        ;;
    evaluate)
        echo "Evaluating model on LexGLUE-FR..."
        python -m dualgpuopt.eval.lexglue_fr --model checkpoints/qc_legal/merged
        ;;
    rag)
        echo "Building FAISS index for RAG..."
        python -m dualgpuopt.rag.build_faiss "$DATASETS_DIR/qc_legal_clean.jsonl" rag/qc.faiss
        ;;
    serve)
        echo "Starting FastAPI server..."
        export LEGAL_MODEL=checkpoints/qc_legal/merged
        export LEGAL_API_KEY=${LEGAL_API_KEY:-secret}
        export FAISS_INDEX=rag/qc.faiss
        python -m dualgpuopt.serve.legal_api
        ;;
    all)
        echo "Running full pipeline with preset $PRESET..."
        # Install dependencies
        pip install -r dualgpuopt/requirements_legal.txt

        # Data ingestion
        python -m dualgpuopt.ingest.operator_tasks.legisqc
        python -m dualgpuopt.ingest.operator_tasks.canlii_fr
        python -m dualgpuopt.ingest.clean_html "$CORPUS_DIR/qc_statutes/raw" "$DATASETS_DIR/qc_legal_clean.jsonl"

        # Tokenizer training
        python -m dualgpuopt.tokenizer.train_spm "$DATASETS_DIR/qc_legal_clean.jsonl" tokenizer_frqc

        # Training
        accelerate launch -m dualgpuopt.train.train_qlora --preset "dualgpuopt/train/presets.yml#$PRESET"

        # Evaluation
        python -m dualgpuopt.eval.lexglue_fr --model checkpoints/qc_legal/merged

        # RAG setup
        python -m dualgpuopt.rag.build_faiss "$DATASETS_DIR/qc_legal_clean.jsonl" rag/qc.faiss

        # Start server
        export LEGAL_MODEL=checkpoints/qc_legal/merged
        export LEGAL_API_KEY=${LEGAL_API_KEY:-secret}
        export FAISS_INDEX=rag/qc.faiss
        python -m dualgpuopt.serve.legal_api
        ;;
    *)
        echo "Unknown step: $STEP"
        echo "Available steps: prep, ingest, tokenize, train, evaluate, rag, serve, all"
        exit 1
        ;;
esac

echo "Completed step: $STEP"
