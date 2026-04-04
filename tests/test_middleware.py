"""Tests for middleware components."""
import pytest
from middleware.auth import AuthContext, Role, APIKeyValidator, RateLimiter, ROLE_PERMISSIONS
from middleware.request_tracking import RequestTracker


class TestAuthContext:
    def test_admin_permissions(self):
        ctx = AuthContext("user1", Role.ADMIN, ROLE_PERMISSIONS[Role.ADMIN])
        assert ctx.has_permission("read") is True
        assert ctx.has_permission("admin") is True
        assert ctx.has_permission("delete") is True

    def test_viewer_permissions(self):
        ctx = AuthContext("user2", Role.VIEWER, ROLE_PERMISSIONS[Role.VIEWER])
        assert ctx.has_permission("read") is True
        assert ctx.has_permission("write") is False

    def test_require_permission_raises(self):
        ctx = AuthContext("user2", Role.VIEWER, ROLE_PERMISSIONS[Role.VIEWER])
        with pytest.raises(PermissionError):
            ctx.require_permission("write")

    def test_not_expired(self):
        ctx = AuthContext("user1", Role.ADMIN, set())
        assert ctx.is_expired is False


class TestAPIKeyValidator:
    def test_generate_and_validate(self):
        validator = APIKeyValidator("test-secret")
        key = validator.generate_key("client1")
        assert validator.validate_key(key) == "client1"

    def test_invalid_key(self):
        validator = APIKeyValidator("test-secret")
        assert validator.validate_key("invalid.key") is None

    def test_malformed_key(self):
        validator = APIKeyValidator("test-secret")
        assert validator.validate_key("no-dot-here") is None


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter(requests_per_minute=60)
        assert limiter.allow("client1") is True

    def test_blocks_excess(self):
        limiter = RateLimiter(requests_per_minute=1)
        limiter.allow("client1")
        assert limiter.allow("client1") is False


class TestRequestTracker:
    def test_start_end(self):
        tracker = RequestTracker()
        ctx = tracker.start("/api/v1/indicators", "GET", "client1")
        assert tracker.active_count == 1
        record = tracker.end(ctx.request_id, 200)
        assert record["status"] == 200
        assert tracker.active_count == 0

    def test_stats(self):
        tracker = RequestTracker()
        ctx = tracker.start("/api/v1/data", "POST")
        tracker.end(ctx.request_id, 200)
        stats = tracker.get_stats()
        assert stats["total"] == 1
