"""
smart_batch.py
==============

Asynchronous, length‑aware inference scheduler.

Features
--------
* **Back‑pressure:** configurable backlog limit guards RAM.
* **Multiple heuristics:** pluggable bucket policies
  (power‑of‑two *or* token‑ratio).
* **Structured logging / Prometheus metrics** for ops tracing.
* **GPU OOM retry:** one automatic retry after cache purge.

Example
-------
>>> async def call(inputs): ...
>>> sb = SmartBatcher(call, bucket_policy=pow2_bucket())
>>> fut = await sb.enqueue({"input_ids":[...], "future":asyncio.get_event_loop().create_future()})
>>> result = await fut
"""
from __future__ import annotations

import asyncio
import time
import typing as _t
from collections import defaultdict

from dualgpuopt.log import get as _log
from dualgpuopt.metrics import BATCH_LAT, QUEUE_DEPTH
from dualgpuopt.batch.heuristics import BucketPolicy, pow2_bucket

Request: _t.TypeAlias = dict[str, _t.Any]
_logger = _log("smart_batch")


class SmartBatcher:
    """Length‑aware async batching queue."""

    def __init__(
        self,
        model_call: "InferenceFn",
        *,
        max_tokens: int = 8192,
        interval_ms: int = 5,
        bucket_policy: BucketPolicy | None = None,
        max_queue: int = 10_000,
    ) -> None:
        self.model_call = model_call
        self._max_tok = max_tokens
        self._int = interval_ms / 1_000
        self._bucket = bucket_policy or pow2_bucket()
        self._max_q = max_queue

        self._buckets: dict[int, list[Request]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._flusher_task: asyncio.Task[None] | None = None

    # public API ---------------------------------------------------------
    async def enqueue(self, req: Request) -> asyncio.Future:
        """Add request; returns its future."""
        if self._queue_depth() >= self._max_q:
            raise asyncio.QueueFull("SmartBatch backlog limit reached")

        bid = self._bucket(len(req["input_ids"]))
        fut: asyncio.Future = req["future"]
        QUEUE_DEPTH.labels(bucket=bid).inc()

        async with self._lock:
            self._buckets[bid].append(req)
            if not self._flusher_task or self._flusher_task.done():
                self._flusher_task = asyncio.create_task(self._flush_loop())
        return fut

    # internal -----------------------------------------------------------
    async def _flush_loop(self) -> None:
        await asyncio.sleep(self._int)
        async with self._lock:
            for bid, lst in list(self._buckets.items()):
                batch, rest = self._split_tokens(lst)
                self._buckets[bid] = rest
                if batch:
                    asyncio.create_task(self._run_batch(batch, bid))

    async def _run_batch(self, batch: list[Request], bid: int) -> None:
        t0 = time.perf_counter()
        try:
            outs = await self._safe_infer([r["input_ids"] for r in batch])
            for req, out in zip(batch, outs):
                req["future"].set_result(out)
        except Exception as exc:  # noqa: BLE001
            for req in batch:
                req["future"].set_exception(exc)
            _logger.exception("Batch %s failed: %s", bid, exc)
        finally:
            BATCH_LAT.labels(bucket=str(bid)).observe((time.perf_counter() - t0) * 1e3)

    async def _safe_infer(self, inputs: list[list[int]]) -> list[str]:
        try:
            return await self.model_call(inputs)
        except RuntimeError as err:
            if "CUDA out of memory" not in str(err):
                raise
            _logger.warning("OOM caught – retrying after cache clear")
            import torch

            torch.cuda.empty_cache()
            return await self.model_call(inputs)

    def _split_tokens(self, lst: list[Request]) -> tuple[list[Request], list[Request]]:
        total, batch, rest = 0, [], []
        for req in lst:
            ln = len(req["input_ids"])
            target = rest if total + ln > self._max_tok else batch
            target.append(req)
            total += ln
        return batch, rest

    def _queue_depth(self) -> int:
        return sum(len(v) for v in self._buckets.values())


class InferenceFn(_t.Protocol):
    async def __call__(self, inputs: list[list[int]]) -> list[str]:
        ...
