"""Tests for observability stack."""
import json, logging, time
import pytest

class TestStructuredFormatter:
    def test_formats_as_json(self):
        from observability.stack import StructuredFormatter
        f = StructuredFormatter()
        r = logging.LogRecord(name="test", level=logging.INFO, pathname="t.py", lineno=1, msg="test message", args=(), exc_info=None)
        parsed = json.loads(f.format(r))
        assert parsed["message"] == "test message"; assert parsed["level"] == "INFO"

class TestTracer:
    def test_span_lifecycle(self):
        from observability.stack import Tracer
        t = Tracer("test"); t.start_trace()
        span = t.start_span("op"); time.sleep(0.01); t.end_span(span)
        assert span.end_time is not None; assert span.duration_ms >= 10
    def test_nested_spans(self):
        from observability.stack import Tracer
        t = Tracer("test"); t.start_trace()
        parent = t.start_span("parent"); child = t.start_span("child")
        assert child.parent_id == parent.span_id
        t.end_span(child); t.end_span(parent)
        assert len(t.get_traces()) == 1

class TestMetricsCollector:
    def test_counter(self):
        from observability.stack import MetricsCollector
        c = MetricsCollector(); c.increment("req"); c.increment("req", 5.0)
        assert c.snapshot()["counters"]["req"] == 6.0
    def test_gauge(self):
        from observability.stack import MetricsCollector
        c = MetricsCollector(); c.gauge("temp", 36.6); c.gauge("temp", 37.2)
        assert c.snapshot()["gauges"]["temp"] == 37.2
    def test_histogram(self):
        from observability.stack import MetricsCollector
        c = MetricsCollector()
        for v in [0.1, 0.2, 0.15, 0.3, 0.25]: c.observe("lat", v)
        h = c.snapshot()["histograms"]["lat"]; assert h["count"] == 5
