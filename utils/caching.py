"""Multi-tier caching for analytical queries and model inference.

Supports in-memory LRU, disk-based persistence, and TTL expiration.
Thread-safe for concurrent access in multi-worker environments.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache with TTL expiration."""

    def __init__(self, maxsize: int = 1024, ttl: float = 3600.0) -> None:
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key in self._cache:
                value, ts = self._cache[key]
                if time.time() - ts < self._ttl:
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return value
                else:
                    del self._cache[key]
            self._misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)
            self._cache[key] = (value, time.time())

    def invalidate(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict[str, int]:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
            "size": len(self._cache),
        }


class DiskCache:
    """Persistent disk-based cache with atomic writes."""

    def __init__(self, cache_dir: str = "/tmp/cache", ttl: float = 86400.0) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ttl = ttl

    def _key_path(self, key: str) -> Path:
        hashed = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._dir / f"{hashed}.pkl"

    def get(self, key: str) -> Any | None:
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            with open(path, "rb") as f:
                ts, value = pickle.load(f)
            if time.time() - ts < self._ttl:
                return value
            path.unlink(missing_ok=True)
        except (pickle.UnpicklingError, EOFError, ValueError):
            path.unlink(missing_ok=True)
        return None

    def put(self, key: str, value: Any) -> None:
        path = self._key_path(key)
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "wb") as f:
            pickle.dump((time.time(), value), f)
        tmp_path.rename(path)

    def evict_expired(self) -> int:
        count = 0
        for path in self._dir.glob("*.pkl"):
            try:
                with open(path, "rb") as f:
                    ts, _ = pickle.load(f)
                if time.time() - ts >= self._ttl:
                    path.unlink()
                    count += 1
            except Exception:
                path.unlink(missing_ok=True)
                count += 1
        return count


class TieredCache:
    """Two-tier cache combining fast in-memory with persistent disk storage."""

    def __init__(
        self, memory_size: int = 512, memory_ttl: float = 600.0,
        disk_dir: str = "/tmp/cache", disk_ttl: float = 86400.0,
    ) -> None:
        self.l1 = LRUCache(maxsize=memory_size, ttl=memory_ttl)
        self.l2 = DiskCache(cache_dir=disk_dir, ttl=disk_ttl)

    def get(self, key: str) -> Any | None:
        value = self.l1.get(key)
        if value is not None:
            return value
        value = self.l2.get(key)
        if value is not None:
            self.l1.put(key, value)
        return value

    def put(self, key: str, value: Any) -> None:
        self.l1.put(key, value)
        self.l2.put(key, value)


def cache_key(*args: Any, **kwargs: Any) -> str:
    raw = json.dumps({"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}})
    return hashlib.sha256(raw.encode()).hexdigest()
