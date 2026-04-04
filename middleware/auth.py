"""Authentication and authorization middleware."""
from __future__ import annotations
import hashlib
import hmac
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)

class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_CLIENT = "api_client"

ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"read", "write", "delete", "admin", "export"},
    Role.ANALYST: {"read", "write", "export"},
    Role.VIEWER: {"read"},
    Role.API_CLIENT: {"read", "export"},
}

@dataclass
class AuthContext:
    user_id: str
    role: Role
    permissions: set[str]
    token_hash: str = ""
    expires_at: float = 0.0

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at if self.expires_at > 0 else False

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def require_permission(self, permission: str) -> None:
        if not self.has_permission(permission):
            raise PermissionError(f"User {self.user_id} lacks permission: {permission}")


class APIKeyValidator:
    """Validates API keys using HMAC signatures."""

    def __init__(self, secret: str) -> None:
        self._secret = secret.encode()

    def generate_key(self, client_id: str) -> str:
        sig = hmac.new(self._secret, client_id.encode(), hashlib.sha256).hexdigest()
        return f"{client_id}.{sig[:32]}"

    def validate_key(self, api_key: str) -> str | None:
        parts = api_key.split(".", 1)
        if len(parts) != 2:
            return None
        client_id, sig = parts
        expected = hmac.new(self._secret, client_id.encode(), hashlib.sha256).hexdigest()[:32]
        if hmac.compare_digest(sig, expected):
            return client_id
        return None


class RateLimiter:
    """Token bucket rate limiter per client."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self._rate = requests_per_minute / 60.0
        self._buckets: dict[str, tuple[float, float]] = {}

    def allow(self, client_id: str) -> bool:
        now = time.monotonic()
        tokens, last = self._buckets.get(client_id, (self._rate * 60, now))
        elapsed = now - last
        tokens = min(self._rate * 60, tokens + elapsed * self._rate)
        if tokens >= 1.0:
            self._buckets[client_id] = (tokens - 1.0, now)
            return True
        self._buckets[client_id] = (tokens, now)
        return False


def require_auth(permission: str) -> Callable:
    """Decorator to enforce permission checks."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, auth: AuthContext, **kwargs: Any) -> Any:
            auth.require_permission(permission)
            return func(*args, auth=auth, **kwargs)
        return wrapper
    return decorator
