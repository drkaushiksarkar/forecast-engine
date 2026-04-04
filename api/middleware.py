"""API middleware for request processing."""
from __future__ import annotations
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

class CORSMiddleware:
    """Cross-origin resource sharing middleware."""

    def __init__(self, allowed_origins: list[str] | None = None) -> None:
        self.allowed_origins = allowed_origins or ["*"]

    def process(self, headers: dict[str, str]) -> dict[str, str]:
        origin = headers.get("Origin", "")
        if "*" in self.allowed_origins or origin in self.allowed_origins:
            return {
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
                "Access-Control-Max-Age": "86400",
            }
        return {}

class CompressionMiddleware:
    """Response compression middleware."""

    def __init__(self, min_size: int = 1024) -> None:
        self.min_size = min_size

    def should_compress(self, content_length: int, accept_encoding: str = "") -> bool:
        return content_length >= self.min_size and "gzip" in accept_encoding

class RequestLogger:
    """Structured request logging middleware."""

    def __init__(self) -> None:
        self._count = 0

    def log_request(self, method: str, path: str, status: int, elapsed_ms: float) -> None:
        self._count += 1
        logger.info("%s %s -> %d (%.1fms)", method, path, status, elapsed_ms)

    @property
    def request_count(self) -> int:
        return self._count
