@echo off
rem Run script for Quebec-French Legal LLM components

setlocal EnableDelayedExpansion

rem Auto-detect GPU configuration and set preset
for /f "tokens=*" %%a in ('nvidia-smi --query-gpu^=memory.total --format^=csv,noheader') do (
    set GPU_MEM=%%a
    set GPU_MEM=!GPU_MEM: =!
    if !GPU_MEM! geq 40000 (
        set PRESET=a100_bf16_large
    ) else (
        set PRESET=auto_hetero
    )
)

echo Selected preset: %PRESET%

rem Parse command line arguments
set STEP=all

:parse_args
if "%~1"=="" goto :end_parse
if "%~1"=="--step" (
    set STEP=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--preset" (
    set PRESET=%~2
    shift
    shift
    goto :parse_args
)
echo Unknown argument: %~1
echo Usage: %0 [--step ^<step^>] [--preset ^<preset^>]
echo Steps: prep, ingest, tokenize, train, evaluate, rag, serve, all
exit /b 1

:end_parse

set BASE_DIR=%CD%
set DATASETS_DIR=%BASE_DIR%\datasets
set CORPUS_DIR=%BASE_DIR%\corpora

rem Create necessary directories
if not exist "%DATASETS_DIR%" mkdir "%DATASETS_DIR%"
if not exist "%CORPUS_DIR%\qc_statutes\raw" mkdir "%CORPUS_DIR%\qc_statutes\raw"
if not exist "%CORPUS_DIR%\canlii_fr\raw" mkdir "%CORPUS_DIR%\canlii_fr\raw"

rem Run a specific step or all steps
if "%STEP%"=="prep" (
    echo Installing dependencies...
    pip install -r dualgpuopt\requirements_legal.txt
    goto :end
)

if "%STEP%"=="ingest" (
    echo Running data ingestion...
    python -m dualgpuopt.ingest.operator_tasks.legisqc
    python -m dualgpuopt.ingest.operator_tasks.canlii_fr
    python -m dualgpuopt.ingest.clean_html "%CORPUS_DIR%\qc_statutes\raw" "%DATASETS_DIR%\qc_legal_clean.jsonl"
    goto :end
)

if "%STEP%"=="tokenize" (
    echo Training custom tokenizer...
    python -m dualgpuopt.tokenizer.train_spm "%DATASETS_DIR%\qc_legal_clean.jsonl" tokenizer_frqc
    goto :end
)

if "%STEP%"=="train" (
    echo Running QLoRA fine-tuning with preset %PRESET%...
    accelerate launch -m dualgpuopt.train.train_qlora --preset "dualgpuopt\train\presets.yml#%PRESET%"
    goto :end
)

if "%STEP%"=="evaluate" (
    echo Evaluating model on LexGLUE-FR...
    python -m dualgpuopt.eval.lexglue_fr --model checkpoints\qc_legal\merged
    goto :end
)

if "%STEP%"=="rag" (
    echo Building FAISS index for RAG...
    python -m dualgpuopt.rag.build_faiss "%DATASETS_DIR%\qc_legal_clean.jsonl" rag\qc.faiss
    goto :end
)

if "%STEP%"=="serve" (
    echo Starting FastAPI server...
    set LEGAL_MODEL=checkpoints\qc_legal\merged
    set LEGAL_API_KEY=secret
    set FAISS_INDEX=rag\qc.faiss
    python -m dualgpuopt.serve.legal_api
    goto :end
)

if "%STEP%"=="all" (
    echo Running full pipeline with preset %PRESET%...

    rem Install dependencies
    pip install -r dualgpuopt\requirements_legal.txt

    rem Data ingestion
    python -m dualgpuopt.ingest.operator_tasks.legisqc
    python -m dualgpuopt.ingest.operator_tasks.canlii_fr
    python -m dualgpuopt.ingest.clean_html "%CORPUS_DIR%\qc_statutes\raw" "%DATASETS_DIR%\qc_legal_clean.jsonl"

    rem Tokenizer training
    python -m dualgpuopt.tokenizer.train_spm "%DATASETS_DIR%\qc_legal_clean.jsonl" tokenizer_frqc

    rem Training
    accelerate launch -m dualgpuopt.train.train_qlora --preset "dualgpuopt\train\presets.yml#%PRESET%"

    rem Evaluation
    python -m dualgpuopt.eval.lexglue_fr --model checkpoints\qc_legal\merged

    rem RAG setup
    python -m dualgpuopt.rag.build_faiss "%DATASETS_DIR%\qc_legal_clean.jsonl" rag\qc.faiss

    rem Start server
    set LEGAL_MODEL=checkpoints\qc_legal\merged
    set LEGAL_API_KEY=secret
    set FAISS_INDEX=rag\qc.faiss
    python -m dualgpuopt.serve.legal_api

    goto :end
)

echo Unknown step: %STEP%
echo Available steps: prep, ingest, tokenize, train, evaluate, rag, serve, all
exit /b 1

:end
echo Completed step: %STEP%
