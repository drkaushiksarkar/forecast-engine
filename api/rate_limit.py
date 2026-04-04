"""Token bucket rate limiter with sliding window and per-client tracking."""
from __future__ import annotations
import threading, time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RateLimitConfig:
    requests_per_second: float = 10.0
    burst_size: int = 20
    window_seconds: float = 60.0
    max_clients: int = 10000

@dataclass  
class ClientBucket:
    tokens: float
    last_refill: float
    request_timestamps: list[float] = field(default_factory=list)

class TokenBucketRateLimiter:
    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        self.config = config or RateLimitConfig()
        self._buckets: dict[str, ClientBucket] = {}
        self._lock = threading.Lock()
        self._global_count = 0
        self._denied_count = 0

    def _get_or_create_bucket(self, client_id: str) -> ClientBucket:
        if client_id not in self._buckets:
            if len(self._buckets) >= self.config.max_clients:
                oldest = min(self._buckets, key=lambda k: self._buckets[k].last_refill)
                del self._buckets[oldest]
            self._buckets[client_id] = ClientBucket(tokens=float(self.config.burst_size), last_refill=time.monotonic())
        return self._buckets[client_id]

    def _refill(self, bucket: ClientBucket) -> None:
        now = time.monotonic()
        elapsed = now - bucket.last_refill
        bucket.tokens = min(float(self.config.burst_size), bucket.tokens + elapsed * self.config.requests_per_second)
        bucket.last_refill = now
        cutoff = now - self.config.window_seconds
        bucket.request_timestamps = [t for t in bucket.request_timestamps if t > cutoff]

    def allow(self, client_id: str = "default", cost: float = 1.0) -> bool:
        with self._lock:
            bucket = self._get_or_create_bucket(client_id)
            self._refill(bucket)
            if bucket.tokens >= cost:
                bucket.tokens -= cost
                bucket.request_timestamps.append(time.monotonic())
                self._global_count += 1
                return True
            self._denied_count += 1
            return False

    def remaining(self, client_id: str = "default") -> int:
        with self._lock:
            bucket = self._get_or_create_bucket(client_id)
            self._refill(bucket)
            return int(bucket.tokens)

    def reset(self, client_id: str) -> None:
        with self._lock:
            if client_id in self._buckets:
                del self._buckets[client_id]

    @property
    def stats(self) -> dict:
        with self._lock:
            return {"active_clients": len(self._buckets), "total_allowed": self._global_count, "total_denied": self._denied_count}

class SlidingWindowLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        with self._lock:
            now = time.monotonic()
            cutoff = now - self.window_seconds
            self._windows[key] = [t for t in self._windows[key] if t > cutoff]
            if len(self._windows[key]) < self.max_requests:
                self._windows[key].append(now)
                return True
            return False

    def remaining(self, key: str) -> int:
        with self._lock:
            now = time.monotonic()
            cutoff = now - self.window_seconds
            self._windows[key] = [t for t in self._windows[key] if t > cutoff]
            return max(0, self.max_requests - len(self._windows[key]))
