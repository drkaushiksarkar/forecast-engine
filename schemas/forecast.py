"""Forecast output schemas and model metadata."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any

@dataclass
class ForecastPoint:
    date: date
    predicted: float
    lower_ci: float
    upper_ci: float
    confidence: float = 0.95

    @property
    def interval_width(self) -> float:
        return self.upper_ci - self.lower_ci

@dataclass
class ForecastResult:
    model_id: str
    indicator: str
    entity: str
    horizon: int
    points: list[ForecastPoint] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    training_end: date | None = None
    created_at: str = ""

    def mae(self, actuals: list[float]) -> float:
        if len(actuals) != len(self.points):
            raise ValueError("Length mismatch")
        return sum(abs(a - p.predicted) for a, p in zip(actuals, self.points)) / len(actuals)

    def rmse(self, actuals: list[float]) -> float:
        if len(actuals) != len(self.points):
            raise ValueError("Length mismatch")
        mse = sum((a - p.predicted) ** 2 for a, p in zip(actuals, self.points)) / len(actuals)
        return mse ** 0.5

    def coverage(self, actuals: list[float]) -> float:
        if not actuals:
            return 0.0
        covered = sum(1 for a, p in zip(actuals, self.points) if p.lower_ci <= a <= p.upper_ci)
        return covered / len(actuals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id, "indicator": self.indicator,
            "entity": self.entity, "horizon": self.horizon,
            "n_points": len(self.points), "metrics": self.metrics,
        }

@dataclass
class ModelMetadata:
    model_id: str
    model_type: str
    version: str
    parameters: dict[str, Any] = field(default_factory=dict)
    training_samples: int = 0
    features: list[str] = field(default_factory=list)
    performance: dict[str, float] = field(default_factory=dict)
