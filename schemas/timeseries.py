"""Time series data schemas and transformations."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Sequence

class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

@dataclass
class TimeSeriesPoint:
    timestamp: date
    value: float
    quality_flag: str = "A"
    source: str = ""

@dataclass
class TimeSeries:
    indicator: str
    entity: str
    frequency: Frequency
    points: list[TimeSeriesPoint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def start_date(self) -> date | None:
        return self.points[0].timestamp if self.points else None

    @property
    def end_date(self) -> date | None:
        return self.points[-1].timestamp if self.points else None

    @property
    def length(self) -> int:
        return len(self.points)

    def values(self) -> list[float]:
        return [p.value for p in self.points]

    def slice(self, start: date, end: date) -> TimeSeries:
        filtered = [p for p in self.points if start <= p.timestamp <= end]
        return TimeSeries(self.indicator, self.entity, self.frequency, filtered, self.metadata)

    def resample(self, target: Frequency) -> TimeSeries:
        """Placeholder for frequency conversion."""
        return self

    def interpolate_gaps(self, method: str = "linear") -> TimeSeries:
        """Fill missing values using interpolation."""
        if not self.points:
            return self
        filled = list(self.points)
        for i in range(1, len(filled) - 1):
            if filled[i].quality_flag == "M":
                prev_val = filled[i - 1].value
                next_val = filled[i + 1].value
                filled[i] = TimeSeriesPoint(
                    filled[i].timestamp, (prev_val + next_val) / 2, "I", "interpolated",
                )
        return TimeSeries(self.indicator, self.entity, self.frequency, filled, self.metadata)

    def detect_outliers(self, z_threshold: float = 3.0) -> list[int]:
        vals = self.values()
        if len(vals) < 3:
            return []
        mean = sum(vals) / len(vals)
        std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
        if std == 0:
            return []
        return [i for i, v in enumerate(vals) if abs(v - mean) / std > z_threshold]
