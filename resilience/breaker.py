"""Retry policies with exponential backoff, jitter, and circuit breaker."""
from __future__ import annotations
import functools, logging, random, time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Sequence, Type

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,)
    on_retry: Optional[Callable[[int, Exception], None]] = None

    def get_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        if self.jitter: delay *= random.uniform(0.5, 1.5)
        return delay

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1
    success_threshold: int = 3

class CircuitBreaker:
    def __init__(self, config: Optional[CircuitBreakerConfig] = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState: return self._state

    def can_execute(self) -> bool:
        if self._state == CircuitState.CLOSED: return True
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.config.recovery_timeout:
                self._state = CircuitState.HALF_OPEN; self._half_open_calls = 0; return True
            return False
        if self._state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.config.half_open_max_calls
        return False

    def record_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._state = CircuitState.CLOSED; self._failure_count = 0; self._success_count = 0
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        self._failure_count += 1; self._last_failure_time = time.monotonic()
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN; self._success_count = 0
        elif self._failure_count >= self.config.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning("Circuit breaker opened after %d failures", self._failure_count)

def retry(policy: Optional[RetryPolicy] = None) -> Callable:
    p = policy or RetryPolicy()
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(p.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except p.retryable_exceptions as e:
                    last_exc = e
                    if attempt < p.max_retries:
                        delay = p.get_delay(attempt)
                        logger.warning("Retry %d/%d for %s: %s (delay=%.1fs)",
                            attempt + 1, p.max_retries, func.__name__, e, delay)
                        if p.on_retry: p.on_retry(attempt + 1, e)
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator

def with_circuit_breaker(breaker: CircuitBreaker) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not breaker.can_execute():
                raise RuntimeError(f"Circuit breaker is {breaker.state.value}")
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        return wrapper
    return decorator
