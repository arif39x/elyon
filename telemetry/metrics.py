from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter


@dataclass(frozen=True)
class Timing:
    operation: str
    duration_ms: int


@contextmanager
def measure(operation: str):
    start = perf_counter()
    try:
        yield
    finally:
        duration_ms = int((perf_counter() - start) * 1000)
        _ = Timing(operation=operation, duration_ms=duration_ms)
