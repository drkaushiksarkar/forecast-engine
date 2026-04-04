"""Retry utilities with exponential backoff and jitter.

Provides configurable retry logic for transient failures in data pipelines,
API calls, and distributed training checkpoints.
"""
import functools
import logging
import random
import time
from typing import Any, Callable, Sequence, Type

logger = logging.getLogger(__name__)

DEFAULT_RETRY_EXCEPTIONS: tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Sequence[Type[Exception]] = DEFAULT_RETRY_EXCEPTIONS,
) -> Callable:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts before raising.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay cap in seconds.
        exponential_base: Multiplier for exponential backoff.
        jitter: Whether to add random jitter to prevent thundering herd.
        retry_on: Exception types that trigger a retry.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(retry_on) as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        logger.error(
                            "Function %s failed after %d attempts: %s",
                            func.__name__, max_attempts, exc,
                        )
                        raise
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay,
                    )
                    if jitter:
                        delay *= 0.5 + random.random()
                    logger.warning(
                        "Attempt %d/%d for %s failed (%s), retrying in %.1fs",
                        attempt, max_attempts, func.__name__, exc, delay,
                    )
                    time.sleep(delay)
            raise last_exception  # type: ignore[misc]
        return wrapper
    return decorator


class RetryBudget:
    """Token-bucket rate limiter for retry attempts across a service."""

    def __init__(self, max_retries_per_second: float = 10.0) -> None:
        self._max_rate = max_retries_per_second
        self._tokens = max_retries_per_second
        self._last_refill = time.monotonic()

    def acquire(self) -> bool:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._max_rate, self._tokens + elapsed * self._max_rate)
        self._last_refill = now
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False
