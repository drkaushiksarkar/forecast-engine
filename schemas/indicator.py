"""Indicator schema definitions for health intelligence data."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class IndicatorDomain(str, Enum):
    HEALTH = "health"
    CLIMATE = "climate"
    ECONOMICS = "economics"
    DEMOGRAPHICS = "demographics"

class AggregationMethod(str, Enum):
    SUM = "sum"
    MEAN = "mean"
    WEIGHTED_MEAN = "weighted_mean"
    MEDIAN = "median"
    RATE = "rate"

@dataclass
class IndicatorSchema:
    code: str
    name: str
    domain: IndicatorDomain
    unit: str
    aggregation: AggregationMethod = AggregationMethod.MEAN
    description: str = ""
    source: str = ""
    frequency: str = "annual"
    decimal_places: int = 2
    min_value: float | None = None
    max_value: float | None = None
    tags: list[str] = field(default_factory=list)

    def validate_value(self, value: float) -> bool:
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code, "name": self.name, "domain": self.domain.value,
            "unit": self.unit, "aggregation": self.aggregation.value,
            "description": self.description, "source": self.source,
            "frequency": self.frequency, "tags": self.tags,
        }

CORE_INDICATORS = [
    IndicatorSchema("MALARIA_CASES", "Confirmed malaria cases", IndicatorDomain.HEALTH, "cases", AggregationMethod.SUM, min_value=0),
    IndicatorSchema("MALARIA_DEATHS", "Malaria deaths", IndicatorDomain.HEALTH, "deaths", AggregationMethod.SUM, min_value=0),
    IndicatorSchema("INCIDENCE_RATE", "Malaria incidence rate", IndicatorDomain.HEALTH, "per 1000", AggregationMethod.RATE, min_value=0),
    IndicatorSchema("TEMP_MEAN", "Mean temperature", IndicatorDomain.CLIMATE, "celsius", AggregationMethod.MEAN, min_value=-60, max_value=60),
    IndicatorSchema("PRECIP_TOTAL", "Total precipitation", IndicatorDomain.CLIMATE, "mm", AggregationMethod.SUM, min_value=0),
    IndicatorSchema("GDP_PER_CAPITA", "GDP per capita PPP", IndicatorDomain.ECONOMICS, "USD", AggregationMethod.MEAN, min_value=0),
    IndicatorSchema("POPULATION", "Total population", IndicatorDomain.DEMOGRAPHICS, "persons", AggregationMethod.SUM, min_value=0),
]
