"""Health intelligence utility library.

Provides cross-cutting concerns: retry logic, validation, caching,
structured logging, and metrics collection.
"""
from utils.retry import retry, RetryBudget
from utils.validation import DatasetValidator, FieldValidator, ValidationReport
from utils.caching import LRUCache, TieredCache, cache_key
from utils.logging_config import configure_logging, get_logger, new_correlation_id
from utils.metrics import registry as metrics_registry, timed

__all__ = [
    "retry", "RetryBudget",
    "DatasetValidator", "FieldValidator", "ValidationReport",
    "LRUCache", "TieredCache", "cache_key",
    "configure_logging", "get_logger", "new_correlation_id",
    "metrics_registry", "timed",
]
