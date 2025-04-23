"""
Shared fixtures / monkey‑patches for our light‑weight test‑suite.
"""
from __future__ import annotations

import time

import pytest


###############################################################################
# Fast in‑memory backend to avoid spawning true servers/GPU code
###############################################################################
class FastMockBackend:
    port = 12345
    _healthy = True

    def load(self, *_a, **_k):
        time.sleep(0.01)

    def stream(self, prompt, **_):  # yield first 4 tokens quickly
        for w in prompt.split()[:4]:
            yield w + " "

    def unload(self):
        ...

    def health(self):
        return self._healthy


FAST = FastMockBackend()


@pytest.fixture(autouse=True)
def patch_backend(monkeypatch):
    """
    Force every new Engine instance to use `FastMockBackend`.
    """
    from dualgpuopt.engine.backend import Engine

    # Replace the actual load method with one that sets our mock backend
    original_load = Engine.load

    def mock_load(self, path_or_id, **kw):
        self.backend = FAST

    monkeypatch.setattr(Engine, "load", mock_load)

    # Patch CHECK_INT for faster watchdog tests
    try:
        import dualgpuopt.engine.pool

        monkeypatch.setattr(dualgpuopt.engine.pool, "CHECK_INT", 0.1)
    except (ImportError, AttributeError):
        pass
