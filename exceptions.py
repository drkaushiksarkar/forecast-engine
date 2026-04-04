"""Domain-specific exception hierarchy.

Provides structured error types for health intelligence operations
with error codes, context, and retry classification.
"""
from __future__ import annotations

from typing import Any


class BaseError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self, message: str, code: str = "UNKNOWN", context: dict[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.context = context or {}
        self.retryable = retryable

    def to_dict(self) -> dict[str, Any]:
        return {"error": self.code, "message": str(self), "context": self.context, "retryable": self.retryable}


class DataError(BaseError):
    """Errors related to data quality, format, or availability."""
    pass


class ValidationError(DataError):
    """Data validation failure."""

    def __init__(self, field: str, message: str, value: Any = None) -> None:
        super().__init__(
            f"Validation failed for {field}: {message}",
            code="VALIDATION_ERROR",
            context={"field": field, "value": str(value)[:200] if value is not None else None},
        )


class SchemaError(DataError):
    """Schema mismatch or incompatibility."""

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(
            f"Schema mismatch: expected {expected}, got {actual}",
            code="SCHEMA_ERROR",
            context={"expected": expected, "actual": actual},
        )


class SourceUnavailableError(DataError):
    """External data source is unreachable."""

    def __init__(self, source: str, reason: str = "") -> None:
        super().__init__(
            f"Source unavailable: {source}" + (f" ({reason})" if reason else ""),
            code="SOURCE_UNAVAILABLE", retryable=True,
            context={"source": source},
        )


class PipelineError(BaseError):
    """Errors in analytical pipeline execution."""
    pass


class StageError(PipelineError):
    """Failure in a specific pipeline stage."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(
            f"Stage '{stage}' failed: {message}",
            code="STAGE_ERROR", context={"stage": stage},
        )


class CheckpointError(PipelineError):
    """Checkpoint save or restore failure."""

    def __init__(self, operation: str, path: str) -> None:
        super().__init__(
            f"Checkpoint {operation} failed: {path}",
            code="CHECKPOINT_ERROR", retryable=True,
            context={"operation": operation, "path": path},
        )


class ModelError(BaseError):
    """Errors related to ML model operations."""
    pass


class InferenceError(ModelError):
    """Model inference failure."""

    def __init__(self, model_id: str, message: str) -> None:
        super().__init__(
            f"Inference failed for {model_id}: {message}",
            code="INFERENCE_ERROR", retryable=True,
            context={"model_id": model_id},
        )


class TrainingError(ModelError):
    """Model training failure."""

    def __init__(self, phase: str, step: int, message: str) -> None:
        super().__init__(
            f"Training failed at {phase} step {step}: {message}",
            code="TRAINING_ERROR",
            context={"phase": phase, "step": step},
        )
