"""Ensemble model combining multiple forecasting approaches."""
from __future__ import annotations
import logging
from typing import Any
from models.base import BaseModel, ModelConfig

logger = logging.getLogger(__name__)

class WeightedEnsemble(BaseModel):
    """Combines predictions from multiple models with learned weights."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self._models: list[BaseModel] = []
        self._weights: list[float] = []

    def add_model(self, model: BaseModel, weight: float = 1.0) -> None:
        self._models.append(model)
        self._weights.append(weight)

    def fit(self, X: Any, y: Any) -> None:
        for model in self._models:
            model.fit(X, y)
        self.is_fitted = True
        self._optimize_weights(X, y)

    def predict(self, X: Any) -> list[float]:
        if not self.is_fitted:
            raise RuntimeError("Ensemble not fitted")
        predictions = [m.predict(X) for m in self._models]
        total_weight = sum(self._weights)
        normalized = [w / total_weight for w in self._weights]
        n = len(predictions[0])
        ensemble_pred = []
        for i in range(n):
            weighted_sum = sum(p[i] * w for p, w in zip(predictions, normalized))
            ensemble_pred.append(weighted_sum)
        return ensemble_pred

    def _optimize_weights(self, X: Any, y: Any) -> None:
        """Simple performance-based weight optimization."""
        predictions = [m.predict(X) for m in self._models]
        errors = []
        for preds in predictions:
            mae = sum(abs(a - p) for a, p in zip(y, preds)) / len(y)
            errors.append(mae)
        if all(e == 0 for e in errors):
            self._weights = [1.0] * len(self._models)
        else:
            inv_errors = [1.0 / (e + 1e-8) for e in errors]
            total = sum(inv_errors)
            self._weights = [ie / total for ie in inv_errors]
        logger.info("Optimized weights: %s", [round(w, 3) for w in self._weights])
