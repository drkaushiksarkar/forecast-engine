"""Tests for caching utilities."""
import time
import pytest
from utils.caching import LRUCache, DiskCache, TieredCache, cache_key


class TestLRUCache:
    def test_basic_put_get(self):
        cache = LRUCache(maxsize=10)
        cache.put("k1", "v1")
        assert cache.get("k1") == "v1"

    def test_miss_returns_none(self):
        cache = LRUCache(maxsize=10)
        assert cache.get("missing") is None

    def test_eviction_on_maxsize(self):
        cache = LRUCache(maxsize=2)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        cache.put("k3", "v3")
        assert cache.get("k1") is None
        assert cache.get("k2") == "v2"
        assert cache.get("k3") == "v3"

    def test_ttl_expiration(self):
        cache = LRUCache(maxsize=10, ttl=0.05)
        cache.put("k1", "v1")
        time.sleep(0.06)
        assert cache.get("k1") is None

    def test_lru_ordering(self):
        cache = LRUCache(maxsize=2)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        cache.get("k1")
        cache.put("k3", "v3")
        assert cache.get("k1") == "v1"
        assert cache.get("k2") is None

    def test_invalidate(self):
        cache = LRUCache(maxsize=10)
        cache.put("k1", "v1")
        assert cache.invalidate("k1") is True
        assert cache.get("k1") is None
        assert cache.invalidate("k1") is False

    def test_clear(self):
        cache = LRUCache(maxsize=10)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_stats(self):
        cache = LRUCache(maxsize=10)
        cache.put("k1", "v1")
        cache.get("k1")
        cache.get("missing")
        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1


class TestDiskCache:
    def test_basic_put_get(self, tmp_path):
        cache = DiskCache(cache_dir=str(tmp_path), ttl=3600)
        cache.put("k1", {"data": [1, 2, 3]})
        assert cache.get("k1") == {"data": [1, 2, 3]}

    def test_miss_returns_none(self, tmp_path):
        cache = DiskCache(cache_dir=str(tmp_path))
        assert cache.get("missing") is None

    def test_ttl_expiration(self, tmp_path):
        cache = DiskCache(cache_dir=str(tmp_path), ttl=0.05)
        cache.put("k1", "v1")
        time.sleep(0.06)
        assert cache.get("k1") is None

    def test_evict_expired(self, tmp_path):
        cache = DiskCache(cache_dir=str(tmp_path), ttl=0.01)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        time.sleep(0.02)
        count = cache.evict_expired()
        assert count == 2


class TestCacheKey:
    def test_deterministic(self):
        k1 = cache_key("query", iso3="BGD", year=2024)
        k2 = cache_key("query", iso3="BGD", year=2024)
        assert k1 == k2

    def test_different_args(self):
        k1 = cache_key("a", x=1)
        k2 = cache_key("b", x=2)
        assert k1 != k2
