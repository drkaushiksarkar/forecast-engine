"""Tests for rate limiter implementations."""
import threading, time
import pytest

class TestTokenBucketRateLimiter:
    def test_allows_within_burst(self):
        from security.rate_limiter import TokenBucketRateLimiter, RateLimitConfig
        limiter = TokenBucketRateLimiter(RateLimitConfig(burst_size=5, requests_per_second=1.0))
        for _ in range(5): assert limiter.allow("c1")
    def test_denies_after_burst(self):
        from security.rate_limiter import TokenBucketRateLimiter, RateLimitConfig
        limiter = TokenBucketRateLimiter(RateLimitConfig(burst_size=2, requests_per_second=0.1))
        assert limiter.allow("c1"); assert limiter.allow("c1"); assert not limiter.allow("c1")
    def test_refills_over_time(self):
        from security.rate_limiter import TokenBucketRateLimiter, RateLimitConfig
        limiter = TokenBucketRateLimiter(RateLimitConfig(burst_size=1, requests_per_second=100.0))
        assert limiter.allow("c1"); assert not limiter.allow("c1")
        time.sleep(0.02); assert limiter.allow("c1")
    def test_per_client_isolation(self):
        from security.rate_limiter import TokenBucketRateLimiter, RateLimitConfig
        limiter = TokenBucketRateLimiter(RateLimitConfig(burst_size=1, requests_per_second=0.1))
        assert limiter.allow("c1"); assert limiter.allow("c2")
        assert not limiter.allow("c1"); assert not limiter.allow("c2")
    def test_thread_safety(self):
        from security.rate_limiter import TokenBucketRateLimiter, RateLimitConfig
        limiter = TokenBucketRateLimiter(RateLimitConfig(burst_size=100, requests_per_second=1000.0))
        results = []
        def worker():
            for _ in range(50): results.append(limiter.allow("shared"))
        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(results) == 200
    def test_remaining(self):
        from security.rate_limiter import TokenBucketRateLimiter, RateLimitConfig
        limiter = TokenBucketRateLimiter(RateLimitConfig(burst_size=10, requests_per_second=0.1))
        assert limiter.remaining("c1") == 10; limiter.allow("c1"); assert limiter.remaining("c1") == 9
    def test_reset(self):
        from security.rate_limiter import TokenBucketRateLimiter, RateLimitConfig
        limiter = TokenBucketRateLimiter(RateLimitConfig(burst_size=1, requests_per_second=0.1))
        limiter.allow("c1"); assert not limiter.allow("c1"); limiter.reset("c1"); assert limiter.allow("c1")
    def test_stats(self):
        from security.rate_limiter import TokenBucketRateLimiter, RateLimitConfig
        limiter = TokenBucketRateLimiter(RateLimitConfig(burst_size=2, requests_per_second=0.1))
        limiter.allow("c1"); limiter.allow("c1"); limiter.allow("c1")
        s = limiter.stats; assert s["active_clients"] == 1; assert s["total_allowed"] == 2; assert s["total_denied"] == 1
