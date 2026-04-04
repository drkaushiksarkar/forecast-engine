"""Tests for retry policies and circuit breaker."""
import time
import pytest

class TestRetryPolicy:
    def test_successful_no_retry(self):
        from resilience.retry_policy import retry, RetryPolicy
        calls = [0]
        @retry(RetryPolicy(max_retries=3))
        def succeed(): calls[0] += 1; return "ok"
        assert succeed() == "ok"; assert calls[0] == 1
    def test_retries_on_failure(self):
        from resilience.retry_policy import retry, RetryPolicy
        calls = [0]
        @retry(RetryPolicy(max_retries=3, base_delay=0.01))
        def flaky():
            calls[0] += 1
            if calls[0] < 3: raise ValueError("fail")
            return "ok"
        assert flaky() == "ok"; assert calls[0] == 3
    def test_exhausts_retries(self):
        from resilience.retry_policy import retry, RetryPolicy
        @retry(RetryPolicy(max_retries=2, base_delay=0.01))
        def always_fail(): raise ValueError("permanent")
        with pytest.raises(ValueError): always_fail()
    def test_delay_calculation(self):
        from resilience.retry_policy import RetryPolicy
        p = RetryPolicy(base_delay=1.0, exponential_base=2.0, max_delay=60.0, jitter=False)
        assert p.get_delay(0) == 1.0; assert p.get_delay(1) == 2.0; assert p.get_delay(2) == 4.0

class TestCircuitBreaker:
    def test_starts_closed(self):
        from resilience.retry_policy import CircuitBreaker, CircuitState
        cb = CircuitBreaker(); assert cb.state == CircuitState.CLOSED; assert cb.can_execute()
    def test_opens_after_failures(self):
        from resilience.retry_policy import CircuitBreaker, CircuitBreakerConfig, CircuitState
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3))
        for _ in range(3): cb.record_failure()
        assert cb.state == CircuitState.OPEN; assert not cb.can_execute()
    def test_half_open_after_timeout(self):
        from resilience.retry_policy import CircuitBreaker, CircuitBreakerConfig, CircuitState
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.05))
        cb.record_failure(); assert cb.state == CircuitState.OPEN
        time.sleep(0.06); assert cb.can_execute(); assert cb.state == CircuitState.HALF_OPEN
    def test_closes_after_success(self):
        from resilience.retry_policy import CircuitBreaker, CircuitBreakerConfig, CircuitState
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01, success_threshold=1))
        cb.record_failure(); time.sleep(0.02); cb.can_execute()
        cb.record_success(); assert cb.state == CircuitState.CLOSED
