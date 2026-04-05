"""Type stubs and protocol definitions for forecast-engine."""
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union
from dataclasses import dataclass

T = TypeVar("T")
ModelOutput = Dict[str, Union[float, List[float], Dict[str, float]]]


class DataLoader(Protocol):
    def load(self, path: str) -> List[Dict[str, Any]]: ...
    def save(self, data: List[Dict[str, Any]], path: str) -> None: ...
    def validate(self, data: List[Dict[str, Any]]) -> bool: ...


class ModelInterface(Protocol):
    def predict(self, inputs: Any) -> ModelOutput: ...
    def evaluate(self, inputs: Any, targets: Any) -> Dict[str, float]: ...
    def save_checkpoint(self, path: str) -> None: ...
    def load_checkpoint(self, path: str) -> None: ...


@dataclass
class PredictionResult:
    prediction: float
    confidence: float
    model_version: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "prediction": self.prediction,
            "confidence": self.confidence,
            "model_version": self.model_version,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class BatchResult:
    results: List[PredictionResult]
    processing_time_ms: float
    batch_size: int

    @property
    def mean_confidence(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.confidence for r in self.results) / len(self.results)
