from __future__ import annotations

import time
from typing import Callable

import pytest


def wait_until(predicate: Callable[[], bool], timeout=1.0, step=0.01):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        if predicate():
            return True
        time.sleep(step)
    return False


@pytest.fixture(scope="function")
def collector():
    data = []
    return data, lambda v: data.append(v)
