"""Metrics collection and reporting for health intelligence services.

Provides counters, gauges, histograms, and timing decorators with
Prometheus-compatible exposition format.
"""
from __future__ import annotations

import functools
import threading
import time
from collections import defaultdict
from typing import Any, Callable


class Counter:
    """Monotonically increasing counter."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self._value = 0.0
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value += amount

    @property
    def value(self) -> float:
        return self._value


class Gauge:
    """Value that can go up and down."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self._value = 0.0
        self._lock = threading.Lock()

    def set(self, value: float) -> None:
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value -= amount

    @property
    def value(self) -> float:
        return self._value


class Histogram:
    """Tracks value distributions with configurable buckets."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(self, name: str, description: str = "", buckets: tuple[float, ...] | None = None) -> None:
        self.name = name
        self.description = description
        self._buckets = sorted(buckets or self.DEFAULT_BUCKETS)
        self._counts: dict[float, int] = {b: 0 for b in self._buckets}
        self._counts[float("inf")] = 0
        self._sum = 0.0
        self._count = 0
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        with self._lock:
            self._sum += value
            self._count += 1
            for b in self._buckets:
                if value <= b:
                    self._counts[b] += 1
            self._counts[float("inf")] += 1

    @property
    def stats(self) -> dict[str, Any]:
        return {"count": self._count, "sum": round(self._sum, 6), "buckets": dict(self._counts)}


class MetricsRegistry:
    """Central registry for all application metrics."""

    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(self, name: str, description: str = "") -> Counter:
        if name not in self._counters:
            self._counters[name] = Counter(name, description)
        return self._counters[name]

    def gauge(self, name: str, description: str = "") -> Gauge:
        if name not in self._gauges:
            self._gauges[name] = Gauge(name, description)
        return self._gauges[name]

    def histogram(self, name: str, description: str = "") -> Histogram:
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, description)
        return self._histograms[name]

    def collect(self) -> dict[str, Any]:
        return {
            "counters": {n: c.value for n, c in self._counters.items()},
            "gauges": {n: g.value for n, g in self._gauges.items()},
            "histograms": {n: h.stats for n, h in self._histograms.items()},
        }


registry = MetricsRegistry()


def timed(metric_name: str) -> Callable:
    """Decorator that records function execution time to a histogram."""
    hist = registry.histogram(metric_name)
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                hist.observe(time.perf_counter() - start)
        return wrapper
    return decorator
