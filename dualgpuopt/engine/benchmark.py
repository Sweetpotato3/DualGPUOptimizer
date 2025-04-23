"""
dualgpuopt.engine.benchmark
Benchmark tracking system for model inference performance.

Tracks and persists performance metrics for different models, providing
historical data for model comparison and optimization.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("dualgpuopt.engine.benchmark")

# Default location for the benchmark database
DEFAULT_DB_PATH = os.path.expanduser("~/.dualgpuopt/benchmarks.db")

DB = Path.home() / ".dualgpuopt" / "benchmarks.db"
DB.parent.mkdir(exist_ok=True)

_conn = sqlite3.connect(DB, check_same_thread=False, timeout=30)
_conn.execute("PRAGMA journal_mode=WAL")
_lock = threading.Lock()

# --- schema creation only once ---
with _lock, _conn:
    _conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS models(
            id INTEGER PRIMARY KEY, model TEXT, backend TEXT, cfg TEXT,
            UNIQUE(model,backend,cfg)
        );
        CREATE TABLE IF NOT EXISTS bench(
            id INTEGER PRIMARY KEY, mid INT, ts INT,
            tok REAL, util REAL, mem REAL,
            FOREIGN KEY(mid) REFERENCES models(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS ix_bench_mid_ts ON bench(mid,ts DESC);
    """,
    )


def _get_mid(model: str, backend: str, cfg: str) -> int:
    with _lock, _conn:
        cur = _conn.execute(
            "SELECT id FROM models WHERE model=? AND backend=? AND cfg=?",
            (model, backend, cfg),
        ).fetchone()
        if cur:
            return cur[0]
        return _conn.execute(
            "INSERT INTO models(model,backend,cfg) VALUES(?,?,?)",
            (model, backend, cfg),
        ).lastrowid


def add(model: str, backend: str, tokps: float, **kw):
    cfg_json = json.dumps(kw.get("cfg")) if kw.get("cfg") is not None else None
    mid = _get_mid(model, backend, cfg_json)
    with _lock, _conn:
        _conn.execute(
            "INSERT INTO bench(mid,ts,tok,util,mem) VALUES(?,?,?,?,?)",
            (mid, int(time.time()), tokps, kw.get("util"), kw.get("mem")),
        )


class BenchmarkDB:
    """
    Database for storing model benchmark data.

    Maintains a SQLite database of inference performance metrics
    for different models and configurations.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the benchmark database.

        Args:
        ----
            db_path: Path to the database file (defaults to ~/.dualgpuopt/benchmarks.db)

        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ensure the database file exists and has the required schema."""
        # Create parent directory if needed
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)

        # Connect and create tables if needed
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_path TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    config TEXT,
                    UNIQUE(model_path, backend, config)
                )
            """,
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL,
                    tokens_per_second REAL NOT NULL,
                    gpu_utilization REAL,
                    memory_used REAL,
                    latency_ms REAL,
                    prompt_tokens INTEGER,
                    output_tokens INTEGER,
                    temperature REAL,
                    batch_size INTEGER,
                    context_size INTEGER,
                    FOREIGN KEY (model_id) REFERENCES models(id)
                )
            """,
            )

            # Create index for faster model lookups
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_benchmarks_model_id ON benchmarks(model_id)",
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_benchmarks_timestamp ON benchmarks(timestamp)",
            )

    def add_benchmark(
        self,
        model_path: str,
        backend: str,
        tokens_per_second: float,
        config: Optional[dict[str, Any]] = None,
        gpu_utilization: Optional[float] = None,
        memory_used: Optional[float] = None,
        latency_ms: Optional[float] = None,
        prompt_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        batch_size: Optional[int] = None,
        context_size: Optional[int] = None,
    ) -> int:
        """
        Add a benchmark record to the database.

        Args:
        ----
            model_path: Path or identifier of the model
            backend: Backend used (e.g., "vllm", "llama.cpp", "hf")
            tokens_per_second: Measured tokens per second
            config: Optional JSON-serializable configuration dictionary
            gpu_utilization: Optional GPU utilization percentage
            memory_used: Optional memory used in MB
            latency_ms: Optional latency in milliseconds
            prompt_tokens: Optional number of tokens in the prompt
            output_tokens: Optional number of tokens in the output
            temperature: Optional temperature setting
            batch_size: Optional batch size
            context_size: Optional context size

        Returns:
        -------
            The ID of the newly created benchmark record

        """
        # Serialize config to JSON if provided
        config_json = json.dumps(config) if config else None

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get or create model ID
            cursor = conn.execute(
                "SELECT id FROM models WHERE model_path = ? AND backend = ? AND config = ?",
                (model_path, backend, config_json),
            )
            model_row = cursor.fetchone()

            if model_row:
                model_id = model_row["id"]
            else:
                cursor = conn.execute(
                    "INSERT INTO models (model_path, backend, config) VALUES (?, ?, ?)",
                    (model_path, backend, config_json),
                )
                model_id = cursor.lastrowid

            # Insert benchmark
            timestamp = int(time.time())
            cursor = conn.execute(
                """
                INSERT INTO benchmarks (
                    model_id, timestamp, tokens_per_second, gpu_utilization,
                    memory_used, latency_ms, prompt_tokens, output_tokens,
                    temperature, batch_size, context_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_id,
                    timestamp,
                    tokens_per_second,
                    gpu_utilization,
                    memory_used,
                    latency_ms,
                    prompt_tokens,
                    output_tokens,
                    temperature,
                    batch_size,
                    context_size,
                ),
            )

            return cursor.lastrowid

    def get_model_benchmarks(
        self,
        model_path: str,
        backend: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get benchmark data for a specific model.

        Args:
        ----
            model_path: Path or identifier of the model
            backend: Optional backend filter
            limit: Maximum number of records to return (default 10)

        Returns:
        -------
            List of benchmark records

        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = """
                SELECT
                    b.id, b.timestamp, b.tokens_per_second, b.gpu_utilization,
                    b.memory_used, b.latency_ms, b.prompt_tokens, b.output_tokens,
                    b.temperature, b.batch_size, b.context_size,
                    m.model_path, m.backend, m.config
                FROM benchmarks b
                JOIN models m ON b.model_id = m.id
                WHERE m.model_path = ?
            """
            params = [model_path]

            if backend:
                query += " AND m.backend = ?"
                params.append(backend)

            query += " ORDER BY b.timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)

            result = []
            for row in cursor:
                record = dict(row)
                if record["config"]:
                    record["config"] = json.loads(record["config"])
                timestamp = record.pop("timestamp")
                record["timestamp"] = timestamp
                record["datetime"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                result.append(record)

            return result

    def get_latest_benchmark(
        self,
        model_path: str,
        backend: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Get the most recent benchmark for a model.

        Args:
        ----
            model_path: Path or identifier of the model
            backend: Optional backend filter

        Returns:
        -------
            Most recent benchmark record or None if not found

        """
        benchmarks = self.get_model_benchmarks(model_path, backend, limit=1)
        return benchmarks[0] if benchmarks else None

    def get_fastest_models(self, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get the fastest models by average tokens per second.

        Args:
        ----
            limit: Maximum number of models to return

        Returns:
        -------
            List of model records with average performance metrics

        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = """
                SELECT
                    m.model_path, m.backend, m.config,
                    AVG(b.tokens_per_second) as avg_tokens_per_second,
                    MAX(b.tokens_per_second) as max_tokens_per_second,
                    AVG(b.gpu_utilization) as avg_gpu_utilization,
                    AVG(b.memory_used) as avg_memory_used,
                    COUNT(b.id) as benchmark_count,
                    MAX(b.timestamp) as last_benchmark
                FROM models m
                JOIN benchmarks b ON m.id = b.model_id
                GROUP BY m.id
                ORDER BY avg_tokens_per_second DESC
                LIMIT ?
            """

            cursor = conn.execute(query, (limit,))

            result = []
            for row in cursor:
                record = dict(row)
                if record["config"]:
                    record["config"] = json.loads(record["config"])
                timestamp = record.pop("last_benchmark")
                record["last_benchmark"] = timestamp
                record["last_benchmark_datetime"] = datetime.fromtimestamp(timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S",
                )
                result.append(record)

            return result

    def clear_benchmarks(
        self,
        model_path: Optional[str] = None,
        older_than_days: Optional[int] = None,
    ) -> int:
        """
        Clear benchmark records from the database.

        Args:
        ----
            model_path: Optional model path to only clear benchmarks for this model
            older_than_days: Optional, only clear benchmarks older than this many days

        Returns:
        -------
            Number of benchmark records deleted

        """
        with sqlite3.connect(self.db_path) as conn:
            query = "DELETE FROM benchmarks"
            params = []

            where_clauses = []

            if model_path:
                where_clauses.append("model_id IN (SELECT id FROM models WHERE model_path = ?)")
                params.append(model_path)

            if older_than_days:
                cutoff_timestamp = int(time.time()) - (older_than_days * 86400)
                where_clauses.append("timestamp < ?")
                params.append(cutoff_timestamp)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            cursor = conn.execute(query, params)
            return cursor.rowcount


# Global benchmark database instance
benchmark_db = BenchmarkDB()


def record_benchmark(model_path: str, backend: str, tokens_per_second: float, **kwargs) -> int:
    """
    Record a benchmark for a model.

    Convenience function that uses the global benchmark database instance.

    Args:
    ----
        model_path: Path or identifier of the model
        backend: Backend used (e.g., "vllm", "llama.cpp", "hf")
        tokens_per_second: Measured tokens per second
        **kwargs: Additional benchmark metrics

    Returns:
    -------
        The ID of the newly created benchmark record

    """
    return benchmark_db.add_benchmark(model_path, backend, tokens_per_second, **kwargs)


def get_model_performance(
    model_path: str,
    backend: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Get the latest performance metrics for a model.

    Convenience function that uses the global benchmark database instance.

    Args:
    ----
        model_path: Path or identifier of the model
        backend: Optional backend filter

    Returns:
    -------
        The most recent benchmark for the model, or None if not found

    """
    return benchmark_db.get_latest_benchmark(model_path, backend)


def get_fastest_models(limit: int = 5) -> list[dict[str, Any]]:
    """
    Get the fastest models by average tokens per second.

    Convenience function that uses the global benchmark database instance.

    Args:
    ----
        limit: Maximum number of models to return

    Returns:
    -------
        List of model records with average performance metrics

    """
    return benchmark_db.get_fastest_models(limit)
