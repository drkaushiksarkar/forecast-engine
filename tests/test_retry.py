"""Tests for retry utilities."""
import time
import pytest
from utils.retry import retry, RetryBudget


class TestRetryDecorator:
    def test_succeeds_first_attempt(self):
        call_count = 0
        @retry(max_attempts=3, base_delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"
        assert succeed() == "ok"
        assert call_count == 1

    def test_retries_on_transient_error(self):
        attempts = 0
        @retry(max_attempts=3, base_delay=0.01, retry_on=(ValueError,))
        def fail_then_succeed():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("transient")
            return "recovered"
        assert fail_then_succeed() == "recovered"
        assert attempts == 3

    def test_raises_after_max_attempts(self):
        @retry(max_attempts=2, base_delay=0.01, retry_on=(RuntimeError,))
        def always_fail():
            raise RuntimeError("permanent")
        with pytest.raises(RuntimeError, match="permanent"):
            always_fail()

    def test_no_retry_on_unmatched_exception(self):
        @retry(max_attempts=3, base_delay=0.01, retry_on=(ValueError,))
        def raise_type_error():
            raise TypeError("wrong type")
        with pytest.raises(TypeError):
            raise_type_error()

    def test_exponential_backoff_timing(self):
        attempts = []
        @retry(max_attempts=3, base_delay=0.05, jitter=False, retry_on=(OSError,))
        def timed_fail():
            attempts.append(time.monotonic())
            if len(attempts) < 3:
                raise OSError("fail")
            return "ok"
        timed_fail()
        assert len(attempts) == 3
        gap1 = attempts[1] - attempts[0]
        gap2 = attempts[2] - attempts[1]
        assert gap1 >= 0.04
        assert gap2 >= 0.08


class TestRetryBudget:
    def test_acquire_within_budget(self):
        budget = RetryBudget(max_retries_per_second=10.0)
        assert budget.acquire() is True

    def test_budget_exhaustion(self):
        budget = RetryBudget(max_retries_per_second=1.0)
        budget.acquire()
        assert budget.acquire() is False

    def test_budget_refills(self):
        budget = RetryBudget(max_retries_per_second=100.0)
        for _ in range(100):
            budget.acquire()
        time.sleep(0.02)
        assert budget.acquire() is True
