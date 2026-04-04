"""Tests for monitoring components."""
import pytest
from monitoring.dashboard import SystemMetrics, DataQualityMonitor


class TestSystemMetrics:
    def test_record_request(self):
        m = SystemMetrics()
        m.record_request(50.0)
        m.record_request(100.0, error=True)
        data = m.get_dashboard_data()
        assert data["total_requests"] == 2
        assert data["error_count"] == 1
        assert data["avg_latency_ms"] == 75.0

    def test_empty_dashboard(self):
        m = SystemMetrics()
        data = m.get_dashboard_data()
        assert data["total_requests"] == 0
        assert data["avg_latency_ms"] == 0


class TestDataQualityMonitor:
    def test_record_ingestion(self):
        m = DataQualityMonitor()
        m.record_ingestion("who_gho", 1000, 980, 20)
        report = m.get_quality_report()
        assert report["total_sources"] == 1
        assert report["sources"]["who_gho"]["quality_score"] == 0.98

    def test_multiple_sources(self):
        m = DataQualityMonitor()
        m.record_ingestion("who_gho", 1000, 980, 20)
        m.record_ingestion("world_bank", 500, 500, 0)
        report = m.get_quality_report()
        assert report["total_sources"] == 2
        assert report["avg_quality"] > 0.98
