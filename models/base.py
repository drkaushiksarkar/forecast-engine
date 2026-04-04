"""Base model interfaces for forecasting and analytics."""
from __future__ import annotations
import abc
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    model_id: str
    model_type: str
    version: str = "1.0.0"
    parameters: dict[str, Any] = field(default_factory=dict)
    feature_columns: list[str] = field(default_factory=list)
    target_column: str = "value"

class BaseModel(abc.ABC):
    """Abstract base for all forecasting models."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self.is_fitted = False
        self._fit_time: float = 0.0
        self._metrics: dict[str, float] = {}

    @abc.abstractmethod
    def fit(self, X: Any, y: Any) -> None:
        ...

    @abc.abstractmethod
    def predict(self, X: Any) -> Any:
        ...

    @property
    def metrics(self) -> dict[str, float]:
        return self._metrics

    def save(self, path: str) -> None:
        raise NotImplementedError

    @classmethod
    def load(cls, path: str) -> BaseModel:
        raise NotImplementedError

class ModelRegistry:
    """Central registry for available models."""

    def __init__(self) -> None:
        self._models: dict[str, type[BaseModel]] = {}

    def register(self, name: str, model_cls: type[BaseModel]) -> None:
        self._models[name] = model_cls
        logger.info("Registered model: %s", name)

    def create(self, name: str, config: ModelConfig) -> BaseModel:
        if name not in self._models:
            raise KeyError(f"Model not found: {name}")
        return self._models[name](config)

    def list_models(self) -> list[str]:
        return list(self._models.keys())

registry = ModelRegistry()
