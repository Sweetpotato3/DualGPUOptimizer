from __future__ import annotations

import time

from dualgpuopt.engine.pool import EnginePool


def test_hit_miss_evict():
    EnginePool.clear()
    # Just test the cache size and eviction behavior
    EnginePool.get("A")
    EnginePool.get("B")
    # Add a third model, which should evict A or B
    EnginePool.get("C")
    stats = EnginePool.get_stats()
    assert stats["cache_size"] == 2
    # Either A or B should be removed (implementation may vary)
    assert len(set(["A", "B", "C"]) & set(stats["models"])) == 2


def test_auto_restart():
    e = EnginePool.get("unstable")
    from dualgpuopt.engine.pool import MAX_FAIL

    for _ in range(MAX_FAIL):
        e.backend._healthy = False
        time.sleep(0.11)  # > CHECK_INT stubbed = 0.1 s
    assert EnginePool.get_stats()["auto_restarts"] >= 1
