"""Performance benchmarking framework for model and data pipeline evaluation."""
from __future__ import annotations

import gc
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Optional


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    mean_seconds: float
    median_seconds: float
    std_seconds: float
    min_seconds: float
    max_seconds: float
    ops_per_second: float
    memory_peak_mb: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"{self.name}: mean={self.mean_seconds:.4f}s, "
            f"median={self.median_seconds:.4f}s, "
            f"std={self.std_seconds:.4f}s, "
            f"ops/s={self.ops_per_second:.1f}"
        )


class BenchmarkTimer:
    """High-resolution timer for benchmarking."""

    def __init__(self) -> None:
        self._start: float = 0.0
        self._elapsed: float = 0.0

    def start(self) -> None:
        self._start = time.perf_counter_ns()

    def stop(self) -> float:
        self._elapsed = (time.perf_counter_ns() - self._start) / 1e9
        return self._elapsed

    @property
    def elapsed(self) -> float:
        return self._elapsed

    @contextmanager
    def measure(self) -> Generator[None, None, None]:
        self.start()
        try:
            yield
        finally:
            self.stop()


class BenchmarkSuite:
    """Suite for running and comparing benchmarks."""

    def __init__(self, warmup_iterations: int = 3, min_iterations: int = 10) -> None:
        self.warmup_iterations = warmup_iterations
        self.min_iterations = min_iterations
        self.results: list[BenchmarkResult] = []

    def run(
        self,
        name: str,
        func: Callable[[], Any],
        iterations: Optional[int] = None,
        setup: Optional[Callable[[], None]] = None,
        teardown: Optional[Callable[[], None]] = None,
    ) -> BenchmarkResult:
        iters = iterations or self.min_iterations
        for _ in range(self.warmup_iterations):
            if setup:
                setup()
            func()
            if teardown:
                teardown()
        gc.collect()
        gc.disable()
        timings: list[float] = []
        timer = BenchmarkTimer()
        try:
            for _ in range(iters):
                if setup:
                    setup()
                with timer.measure():
                    func()
                timings.append(timer.elapsed)
                if teardown:
                    teardown()
        finally:
            gc.enable()
        mean_t = statistics.mean(timings)
        result = BenchmarkResult(
            name=name,
            iterations=iters,
            mean_seconds=mean_t,
            median_seconds=statistics.median(timings),
            std_seconds=statistics.stdev(timings) if len(timings) > 1 else 0.0,
            min_seconds=min(timings),
            max_seconds=max(timings),
            ops_per_second=1.0 / mean_t if mean_t > 0 else float("inf"),
        )
        self.results.append(result)
        return result

    def compare(self, baseline_name: str, target_name: str) -> dict[str, Any]:
        baseline = next((r for r in self.results if r.name == baseline_name), None)
        target = next((r for r in self.results if r.name == target_name), None)
        if baseline is None or target is None:
            raise ValueError("Both benchmark results must exist for comparison")
        speedup = baseline.mean_seconds / target.mean_seconds if target.mean_seconds > 0 else float("inf")
        return {
            "baseline": baseline.name,
            "target": target.name,
            "speedup": round(speedup, 2),
            "baseline_mean": baseline.mean_seconds,
            "target_mean": target.mean_seconds,
            "improvement_pct": round((1 - target.mean_seconds / baseline.mean_seconds) * 100, 1)
            if baseline.mean_seconds > 0 else 0.0,
        }

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "name": r.name,
                "mean": round(r.mean_seconds, 6),
                "median": round(r.median_seconds, 6),
                "std": round(r.std_seconds, 6),
                "ops_per_second": round(r.ops_per_second, 1),
            }
            for r in sorted(self.results, key=lambda r: r.mean_seconds)
        ]


def benchmark(
    name: str,
    iterations: int = 100,
    warmup: int = 5,
) -> Callable:
    """Decorator for benchmarking functions."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> BenchmarkResult:
            suite = BenchmarkSuite(warmup_iterations=warmup, min_iterations=iterations)
            return suite.run(name, lambda: func(*args, **kwargs))
        wrapper.__benchmark__ = True
        wrapper.__benchmark_name__ = name
        return wrapper
    return decorator
