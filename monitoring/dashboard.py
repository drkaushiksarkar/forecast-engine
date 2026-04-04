"""Monitoring dashboard data collectors."""
from __future__ import annotations
import time
from typing import Any

class SystemMetrics:
    """Collects system-level metrics for monitoring dashboards."""

    def __init__(self) -> None:
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        self._latencies: list[float] = []

    def record_request(self, latency_ms: float, error: bool = False) -> None:
        self._request_count += 1
        self._latencies.append(latency_ms)
        if error:
            self._error_count += 1
        if len(self._latencies) > 10000:
            self._latencies = self._latencies[-5000:]

    def get_dashboard_data(self) -> dict[str, Any]:
        uptime = time.time() - self._start_time
        avg_latency = sum(self._latencies) / len(self._latencies) if self._latencies else 0
        p95 = sorted(self._latencies)[int(len(self._latencies) * 0.95)] if len(self._latencies) > 20 else 0
        p99 = sorted(self._latencies)[int(len(self._latencies) * 0.99)] if len(self._latencies) > 100 else 0
        return {
            "uptime_seconds": round(uptime, 0),
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95, 2),
            "p99_latency_ms": round(p99, 2),
            "requests_per_second": round(self._request_count / max(uptime, 1), 2),
        }


class DataQualityMonitor:
    """Monitors data quality metrics across sources."""

    def __init__(self) -> None:
        self._source_stats: dict[str, dict[str, Any]] = {}

    def record_ingestion(self, source: str, records: int, valid: int, errors: int) -> None:
        self._source_stats[source] = {
            "last_ingestion": time.time(),
            "records": records,
            "valid": valid,
            "errors": errors,
            "quality_score": valid / max(records, 1),
        }

    def get_quality_report(self) -> dict[str, Any]:
        return {
            "sources": self._source_stats,
            "total_sources": len(self._source_stats),
            "avg_quality": sum(s["quality_score"] for s in self._source_stats.values()) / max(len(self._source_stats), 1),
        }
