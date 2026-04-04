"""Request tracking and observability middleware."""
from __future__ import annotations
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

@dataclass
class RequestContext:
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    start_time: float = field(default_factory=time.monotonic)
    client_id: str = ""
    endpoint: str = ""
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def elapsed_ms(self) -> float:
        return (time.monotonic() - self.start_time) * 1000

    def to_log_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id, "client_id": self.client_id,
            "endpoint": self.endpoint, "method": self.method,
            "elapsed_ms": round(self.elapsed_ms, 2), "tags": self.tags,
        }


class RequestTracker:
    """Tracks request lifecycle for observability."""

    def __init__(self) -> None:
        self._active: dict[str, RequestContext] = {}
        self._history: list[dict[str, Any]] = []
        self._max_history = 10000

    def start(self, endpoint: str, method: str = "GET", client_id: str = "") -> RequestContext:
        ctx = RequestContext(endpoint=endpoint, method=method, client_id=client_id)
        self._active[ctx.request_id] = ctx
        logger.info("Request started: %s %s [%s]", method, endpoint, ctx.request_id)
        return ctx

    def end(self, request_id: str, status: int = 200) -> dict[str, Any]:
        ctx = self._active.pop(request_id, None)
        if ctx is None:
            return {}
        record = {**ctx.to_log_dict(), "status": status}
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        logger.info("Request completed: %s %s [%s] %dms status=%d",
                     ctx.method, ctx.endpoint, ctx.request_id,
                     round(ctx.elapsed_ms), status)
        return record

    @property
    def active_count(self) -> int:
        return len(self._active)

    def get_stats(self) -> dict[str, Any]:
        if not self._history:
            return {"total": 0, "active": self.active_count}
        latencies = [r["elapsed_ms"] for r in self._history]
        return {
            "total": len(self._history),
            "active": self.active_count,
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "p99_ms": round(sorted(latencies)[int(len(latencies) * 0.99)], 2),
            "error_rate": sum(1 for r in self._history if r["status"] >= 400) / len(self._history),
        }
