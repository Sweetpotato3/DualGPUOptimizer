@echo off
:: run_legal_llm.bat - Helper script for Québec-French Legal LLM

:: Set default values
set PRESET=a100_bf16_large
set STEP=all
set DATA_DIR=corpora
set OUTPUT_DIR=datasets
set MODEL_DIR=checkpoints\qc_legal
set INDEX_DIR=rag
set PORT=8080

:: Parse command line arguments
:parse_args
if "%~1"=="" goto :start_process
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
if "%~1"=="--data-dir" (
    set DATA_DIR=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--output-dir" (
    set OUTPUT_DIR=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--model-dir" (
    set MODEL_DIR=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--index-dir" (
    set INDEX_DIR=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--port" (
    set PORT=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    echo Usage: %0 [options]
    echo Options:
    echo   --step STEP       Step to run (prep, ingest, tokenize, train, evaluate, rag, serve, all)
    echo   --preset PRESET   Training preset to use (a100_bf16_large, dual_gpu_small, etc.)
    echo   --data-dir DIR    Directory for raw data
    echo   --output-dir DIR  Directory for processed data
    echo   --model-dir DIR   Directory for model checkpoints
    echo   --index-dir DIR   Directory for RAG indices
    echo   --port PORT       Port for API server
    exit /b 0
)
echo Unknown option: %~1
exit /b 1

:start_process
:: Create necessary directories
if not exist %DATA_DIR%\qc_statutes\raw mkdir %DATA_DIR%\qc_statutes\raw
if not exist %DATA_DIR%\canlii_fr\raw mkdir %DATA_DIR%\canlii_fr\raw
if not exist %OUTPUT_DIR% mkdir %OUTPUT_DIR%
if not exist %MODEL_DIR% mkdir %MODEL_DIR%
if not exist %INDEX_DIR% mkdir %INDEX_DIR%

echo Running Québec-French Legal LLM: Step=%STEP%, Preset=%PRESET%

:: Process steps
if "%STEP%"=="prep" goto :step_prep
if "%STEP%"=="ingest" goto :step_ingest
if "%STEP%"=="tokenize" goto :step_tokenize
if "%STEP%"=="train" goto :step_train
if "%STEP%"=="evaluate" goto :step_evaluate
if "%STEP%"=="rag" goto :step_rag
if "%STEP%"=="serve" goto :step_serve
if "%STEP%"=="all" goto :step_all
echo Unknown step: %STEP%
exit /b 1

:step_all
call :step_prep
call :step_ingest
call :step_tokenize
call :step_train
call :step_evaluate
call :step_rag
call :step_serve
goto :eof

:step_prep
echo === Preparing environment ===
pip install -r dualgpuopt\requirements_legal.txt
exit /b 0

:step_ingest
echo === Data ingestion ===
echo Crawling LégisQuébec...
python -m dualgpuopt.ingest.clean_html %DATA_DIR%\qc_statutes\raw %OUTPUT_DIR%\qc_legal_clean.jsonl

echo Chunking documents...
python -m dualgpuopt.ingest.chunk_jsonl %OUTPUT_DIR%\qc_legal_clean.jsonl %OUTPUT_DIR%\qc_legal_chunks.jsonl --max-length 512 --overlap 64
exit /b 0

:step_tokenize
echo === Training tokenizer ===
python -m dualgpuopt.tokenizer.train_spm %OUTPUT_DIR%\qc_legal_clean.jsonl tokenizer_frqc
exit /b 0

:step_train
echo === Training model ===
accelerate launch -m dualgpuopt.train.train_qlora --preset dualgpuopt\train\presets.yml#%PRESET%
exit /b 0

:step_evaluate
echo === Evaluating model ===
python -m dualgpuopt.eval.lexglue_fr --model %MODEL_DIR%\merged --output %OUTPUT_DIR%\eval_results.json
echo Evaluation results:
type %OUTPUT_DIR%\eval_results.json
exit /b 0

:step_rag
echo === Building RAG index ===
python -m dualgpuopt.rag.build_faiss %OUTPUT_DIR%\qc_legal_clean.jsonl %INDEX_DIR%\qc.faiss
exit /b 0

:step_serve
echo === Starting API server ===
:: Generate a random API key if not specified
if "%LEGAL_API_KEY%"=="" (
    for /f "delims=" %%a in ('powershell -Command "[System.Guid]::NewGuid().ToString(\"N\")"') do set LEGAL_API_KEY=%%a
    echo Generated API key: %LEGAL_API_KEY%
)

set LEGAL_MODEL=%MODEL_DIR%\merged
set FAISS_INDEX=%INDEX_DIR%\qc.faiss
set PORT=%PORT%

python -m dualgpuopt.serve.legal_api
exit /b 0

echo Done! 