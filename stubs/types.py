"""Type stubs and protocol definitions for static analysis support."""
from __future__ import annotations

from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeAlias,
    TypedDict,
    TypeVar,
    Union,
    runtime_checkable,
)


T = TypeVar("T")
NumericValue: TypeAlias = Union[int, float]
JSONPrimitive: TypeAlias = Union[str, int, float, bool, None]
JSONValue: TypeAlias = Union[JSONPrimitive, List["JSONValue"], Dict[str, "JSONValue"]]
GeoCoordinate: TypeAlias = Tuple[float, float]
DateRange: TypeAlias = Tuple[str, str]
ConfidenceLevel: TypeAlias = Literal["low", "medium", "high", "very_high"]


class TimeSeriesPoint(TypedDict):
    timestamp: str
    value: float
    quality: Optional[float]
    source: str


class ForecastPoint(TypedDict):
    timestamp: str
    predicted: float
    lower_bound: float
    upper_bound: float
    confidence: float


class IndicatorMetadata(TypedDict):
    code: str
    name: str
    unit: str
    source: str
    frequency: Literal["daily", "weekly", "monthly", "quarterly", "annual"]
    coverage_start: str
    coverage_end: str
    country_count: int


class AlertPayload(TypedDict):
    alert_id: str
    severity: Literal["info", "warning", "critical", "emergency"]
    indicator: str
    country_iso3: str
    message: str
    triggered_at: str
    threshold: float
    observed_value: float


class EvaluationMetrics(TypedDict):
    rmse: float
    mae: float
    mape: float
    r_squared: float
    coverage_probability: float
    mean_interval_width: float


class ModelConfig(TypedDict):
    model_type: str
    hyperparameters: Dict[str, Any]
    training_data_path: str
    validation_split: float
    random_seed: int


@runtime_checkable
class DataSource(Protocol):
    """Protocol for data source implementations."""

    @property
    def name(self) -> str: ...

    @property
    def available(self) -> bool: ...

    def fetch(
        self,
        indicator: str,
        country: str,
        start_date: str,
        end_date: str,
    ) -> list[TimeSeriesPoint]: ...

    def list_indicators(self) -> list[IndicatorMetadata]: ...

    def list_countries(self) -> list[str]: ...


@runtime_checkable
class ForecastModel(Protocol):
    """Protocol for forecast model implementations."""

    @property
    def name(self) -> str: ...

    def fit(self, data: Sequence[TimeSeriesPoint]) -> None: ...

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
    ) -> list[ForecastPoint]: ...

    def evaluate(
        self,
        test_data: Sequence[TimeSeriesPoint],
    ) -> EvaluationMetrics: ...


@runtime_checkable
class AlertEngine(Protocol):
    """Protocol for alert engine implementations."""

    def register_threshold(
        self,
        indicator: str,
        country: str,
        threshold: float,
        direction: Literal["above", "below"],
    ) -> str: ...

    def check(self, data_point: TimeSeriesPoint) -> Optional[AlertPayload]: ...

    def active_alerts(self) -> list[AlertPayload]: ...

    def acknowledge(self, alert_id: str) -> bool: ...


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol for cache backend implementations."""

    def get(self, key: str) -> Optional[JSONValue]: ...

    def set(self, key: str, value: JSONValue, ttl_seconds: int = 3600) -> None: ...

    def delete(self, key: str) -> bool: ...

    def clear(self) -> int: ...

    def keys(self, pattern: str = "*") -> list[str]: ...
