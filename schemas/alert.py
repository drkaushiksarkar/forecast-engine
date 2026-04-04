"""Alert and notification schemas for early warning systems."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertType(str, Enum):
    OUTBREAK = "outbreak"
    THRESHOLD_BREACH = "threshold_breach"
    ANOMALY = "anomaly"
    FORECAST_WARNING = "forecast_warning"
    DATA_QUALITY = "data_quality"
    SYSTEM = "system"

@dataclass
class Alert:
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    entity: str
    indicator: str = ""
    value: float | None = None
    threshold: float | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return not self.resolved

    def acknowledge(self, user: str) -> None:
        self.acknowledged = True
        self.metadata["acknowledged_by"] = user
        self.metadata["acknowledged_at"] = datetime.utcnow().isoformat()

    def resolve(self, user: str, resolution: str) -> None:
        self.resolved = True
        self.metadata["resolved_by"] = user
        self.metadata["resolution"] = resolution

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id, "type": self.alert_type.value,
            "severity": self.severity.value, "title": self.title,
            "entity": self.entity, "active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

@dataclass
class AlertRule:
    rule_id: str
    indicator: str
    condition: str
    threshold: float
    severity: AlertSeverity
    cooldown_hours: int = 24
    enabled: bool = True

    def evaluate(self, value: float) -> bool:
        if not self.enabled:
            return False
        ops = {"gt": value > self.threshold, "gte": value >= self.threshold,
               "lt": value < self.threshold, "lte": value <= self.threshold,
               "eq": value == self.threshold}
        return ops.get(self.condition, False)
