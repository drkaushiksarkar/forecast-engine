"""Observability stack: structured logging, metrics collection, distributed tracing."""
from __future__ import annotations
import json, logging, sys, time, uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_span_id: ContextVar[str] = ContextVar("span_id", default="")

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {"timestamp": datetime.utcnow().isoformat() + "Z", "level": record.levelname,
                 "logger": record.name, "message": record.getMessage(), "module": record.module,
                 "function": record.funcName, "line": record.lineno}
        tid = _trace_id.get("")
        if tid: entry["trace_id"] = tid
        sid = _span_id.get("")
        if sid: entry["span_id"] = sid
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = {"type": type(record.exc_info[1]).__name__, "message": str(record.exc_info[1])}
        return json.dumps(entry, default=str)

def setup_structured_logging(level: str = "INFO", service_name: str = "app") -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return logger

@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.monotonic)
    end_time: Optional[float] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "OK"
    @property
    def duration_ms(self) -> float:
        end = self.end_time if self.end_time else time.monotonic()
        return (end - self.start_time) * 1000
    def set_attribute(self, key: str, value: Any) -> None: self.attributes[key] = value
    def add_event(self, name: str, attrs: Optional[dict] = None) -> None:
        self.events.append({"name": name, "timestamp": time.monotonic(), "attributes": attrs or {}})
    def end(self, status: str = "OK") -> None: self.end_time = time.monotonic(); self.status = status
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "trace_id": self.trace_id, "span_id": self.span_id,
                "parent_id": self.parent_id, "duration_ms": round(self.duration_ms, 2),
                "status": self.status, "attributes": self.attributes, "events": self.events}

class Tracer:
    def __init__(self, service_name: str = "app") -> None:
        self.service_name = service_name; self._spans: list[Span] = []; self._active: dict[str, Span] = {}
    def start_trace(self) -> str:
        tid = uuid.uuid4().hex[:32]; _trace_id.set(tid); return tid
    def start_span(self, name: str, parent_id: Optional[str] = None) -> Span:
        tid = _trace_id.get("") or self.start_trace()
        span = Span(name=name, trace_id=tid, parent_id=parent_id or _span_id.get("") or None)
        span.set_attribute("service.name", self.service_name)
        _span_id.set(span.span_id); self._active[span.span_id] = span; return span
    def end_span(self, span: Span, status: str = "OK") -> None:
        span.end(status); self._active.pop(span.span_id, None); self._spans.append(span)
        if span.parent_id: _span_id.set(span.parent_id)
    def get_traces(self) -> dict[str, list[dict]]:
        traces: dict[str, list[dict]] = {}
        for s in self._spans: traces.setdefault(s.trace_id, []).append(s.to_dict())
        return traces

@dataclass
class MetricPoint:
    name: str; value: float; timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict); metric_type: str = "gauge"

class MetricsCollector:
    def __init__(self) -> None:
        self._counters: dict[str, float] = {}; self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
    def increment(self, name: str, value: float = 1.0, labels: Optional[dict] = None) -> None:
        key = self._key(name, labels); self._counters[key] = self._counters.get(key, 0.0) + value
    def gauge(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        self._gauges[self._key(name, labels)] = value
    def observe(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        key = self._key(name, labels); self._histograms.setdefault(key, []).append(value)
    def _key(self, name: str, labels: Optional[dict]) -> str:
        if not labels: return name
        return f"{name}{{{','.join(f'{k}={v}' for k, v in sorted(labels.items()))}}}"
    def snapshot(self) -> dict[str, Any]:
        import statistics
        result: dict[str, Any] = {"counters": dict(self._counters), "gauges": dict(self._gauges), "histograms": {}}
        for k, v in self._histograms.items():
            if v: result["histograms"][k] = {"count": len(v), "sum": sum(v), "mean": statistics.mean(v),
                "p50": statistics.median(v), "min": min(v), "max": max(v)}
        return result
    def reset(self) -> None: self._counters.clear(); self._gauges.clear(); self._histograms.clear()
