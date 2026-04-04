"""Alert service for outbreak detection and notification."""
from __future__ import annotations
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

class AlertService:
    """Manages alert lifecycle: creation, evaluation, routing, resolution."""

    def __init__(self) -> None:
        self._rules: list[dict[str, Any]] = []
        self._active_alerts: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []
        self._cooldowns: dict[str, float] = {}

    def add_rule(self, rule: dict[str, Any]) -> None:
        self._rules.append(rule)
        logger.info("Alert rule added: %s", rule.get("rule_id", "unknown"))

    def evaluate(self, indicator: str, entity: str, value: float) -> list[dict[str, Any]]:
        triggered = []
        for rule in self._rules:
            if rule.get("indicator") != indicator or not rule.get("enabled", True):
                continue
            cooldown_key = f"{rule['rule_id']}:{entity}"
            if cooldown_key in self._cooldowns:
                if time.time() - self._cooldowns[cooldown_key] < rule.get("cooldown_hours", 24) * 3600:
                    continue
            if self._check_condition(rule, value):
                alert = {
                    "rule_id": rule["rule_id"], "indicator": indicator,
                    "entity": entity, "value": value,
                    "threshold": rule["threshold"], "severity": rule.get("severity", "medium"),
                    "triggered_at": time.time(),
                }
                triggered.append(alert)
                self._active_alerts[f"{rule['rule_id']}:{entity}"] = alert
                self._cooldowns[cooldown_key] = time.time()
                logger.warning("Alert triggered: %s for %s (value=%.2f, threshold=%.2f)",
                               rule["rule_id"], entity, value, rule["threshold"])
        return triggered

    def _check_condition(self, rule: dict[str, Any], value: float) -> bool:
        threshold = rule["threshold"]
        condition = rule.get("condition", "gt")
        return {"gt": value > threshold, "gte": value >= threshold,
                "lt": value < threshold, "lte": value <= threshold,
                "eq": abs(value - threshold) < 1e-9}.get(condition, False)

    def acknowledge(self, alert_key: str, user: str) -> bool:
        if alert_key in self._active_alerts:
            self._active_alerts[alert_key]["acknowledged_by"] = user
            self._active_alerts[alert_key]["acknowledged_at"] = time.time()
            return True
        return False

    def resolve(self, alert_key: str, resolution: str) -> bool:
        if alert_key in self._active_alerts:
            alert = self._active_alerts.pop(alert_key)
            alert["resolved"] = True
            alert["resolution"] = resolution
            self._history.append(alert)
            return True
        return False

    @property
    def active_count(self) -> int:
        return len(self._active_alerts)

    def get_stats(self) -> dict[str, Any]:
        return {"active": self.active_count, "total_rules": len(self._rules), "history": len(self._history)}
