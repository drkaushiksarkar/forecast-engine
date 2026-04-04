"""Tests for alert service."""
import time
import pytest
from services.alert_service import AlertService


class TestAlertService:
    def setup_method(self):
        self.service = AlertService()
        self.service.add_rule({
            "rule_id": "high_cases", "indicator": "MALARIA_CASES",
            "condition": "gt", "threshold": 1000, "severity": "high",
            "cooldown_hours": 0.001, "enabled": True,
        })

    def test_trigger_alert(self):
        alerts = self.service.evaluate("MALARIA_CASES", "BGD", 1500)
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "high"
        assert alerts[0]["value"] == 1500

    def test_no_trigger_below_threshold(self):
        alerts = self.service.evaluate("MALARIA_CASES", "BGD", 500)
        assert len(alerts) == 0

    def test_cooldown_prevents_duplicate(self):
        self.service.evaluate("MALARIA_CASES", "BGD", 1500)
        alerts = self.service.evaluate("MALARIA_CASES", "BGD", 2000)
        assert len(alerts) == 0

    def test_acknowledge_alert(self):
        self.service.evaluate("MALARIA_CASES", "BGD", 1500)
        assert self.service.acknowledge("high_cases:BGD", "analyst1") is True

    def test_resolve_alert(self):
        self.service.evaluate("MALARIA_CASES", "BGD", 1500)
        assert self.service.resolve("high_cases:BGD", "Cases declining") is True
        assert self.service.active_count == 0

    def test_stats(self):
        stats = self.service.get_stats()
        assert stats["total_rules"] == 1
        assert stats["active"] == 0

    def test_disabled_rule(self):
        self.service.add_rule({
            "rule_id": "disabled", "indicator": "MALARIA_CASES",
            "condition": "gt", "threshold": 100, "enabled": False,
        })
        alerts = self.service.evaluate("MALARIA_CASES", "BGD", 500)
        assert len(alerts) == 0
