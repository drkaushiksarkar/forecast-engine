"""Tests for metrics collection."""
import pytest
from utils.metrics import Counter, Gauge, Histogram, MetricsRegistry, timed


class TestCounter:
    def test_initial_value(self):
        c = Counter("req_total")
        assert c.value == 0

    def test_increment(self):
        c = Counter("req_total")
        c.inc()
        assert c.value == 1

    def test_increment_by_amount(self):
        c = Counter("req_total")
        c.inc(5)
        assert c.value == 5

    def test_multiple_increments(self):
        c = Counter("req_total")
        c.inc(3)
        c.inc(7)
        assert c.value == 10


class TestGauge:
    def test_set_value(self):
        g = Gauge("connections")
        g.set(42)
        assert g.value == 42

    def test_increment_decrement(self):
        g = Gauge("connections")
        g.inc(5)
        g.dec(2)
        assert g.value == 3

    def test_default_zero(self):
        g = Gauge("connections")
        assert g.value == 0


class TestHistogram:
    def test_observe(self):
        h = Histogram("latency")
        h.observe(0.5)
        h.observe(1.5)
        assert h.stats["count"] == 2
        assert h.stats["sum"] == 2.0

    def test_bucket_counting(self):
        h = Histogram("latency", buckets=(0.1, 0.5, 1.0))
        h.observe(0.05)
        h.observe(0.3)
        h.observe(0.8)
        h.observe(5.0)
        assert h.stats["count"] == 4


class TestMetricsRegistry:
    def test_counter_creation(self):
        reg = MetricsRegistry()
        c = reg.counter("test_counter")
        c.inc()
        assert reg.counter("test_counter").value == 1

    def test_gauge_creation(self):
        reg = MetricsRegistry()
        g = reg.gauge("test_gauge")
        g.set(99)
        assert reg.gauge("test_gauge").value == 99

    def test_collect(self):
        reg = MetricsRegistry()
        reg.counter("c1").inc(3)
        reg.gauge("g1").set(7)
        data = reg.collect()
        assert data["counters"]["c1"] == 3
        assert data["gauges"]["g1"] == 7


class TestTimedDecorator:
    def test_records_timing(self):
        @timed("test_fn_duration")
        def fast_fn():
            return 42
        result = fast_fn()
        assert result == 42
