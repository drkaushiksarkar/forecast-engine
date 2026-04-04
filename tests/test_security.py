"""Tests for security utilities."""
import time
import pytest

class TestInputSanitizer:
    def test_removes_xss(self):
        from security.utils import InputSanitizer
        r = InputSanitizer.sanitize_string('<script>alert("xss")</script>hello')
        assert "<script" not in r; assert "hello" in r
    def test_detects_sql_injection(self):
        from security.utils import InputSanitizer
        assert InputSanitizer.check_sql_injection("1; DROP TABLE users--")
        assert not InputSanitizer.check_sql_injection("normal query")
    def test_path_traversal(self):
        from security.utils import InputSanitizer
        with pytest.raises(ValueError): InputSanitizer.sanitize_path("../../etc/passwd")
    def test_email(self):
        from security.utils import InputSanitizer
        assert InputSanitizer.sanitize_email("user@example.com") == "user@example.com"
        assert InputSanitizer.sanitize_email("not-an-email") is None

class TestHMACSigner:
    def test_sign_verify(self):
        from security.utils import HMACSigner
        s = HMACSigner("secret"); sig = s.sign('{"amount": 100}')
        assert s.verify('{"amount": 100}', sig)
    def test_reject_tampered(self):
        from security.utils import HMACSigner
        s = HMACSigner("secret"); sig = s.sign('{"amount": 100}')
        assert not s.verify('{"amount": 999}', sig)
    def test_reject_expired(self):
        from security.utils import HMACSigner
        s = HMACSigner("secret"); sig = s.sign("payload", timestamp=int(time.time()) - 600)
        assert not s.verify("payload", sig, tolerance=300)

class TestSecretManager:
    def test_get_from_env(self, monkeypatch):
        from security.utils import SecretManager
        monkeypatch.setenv("APP_DB_PASS", "secret123")
        assert SecretManager("APP").get("DB_PASS") == "secret123"
    def test_required_missing(self):
        from security.utils import SecretManager
        with pytest.raises(EnvironmentError): SecretManager("TEST").get("NOPE")
    def test_password_hash(self):
        from security.utils import SecretManager
        h, s = SecretManager.hash_password("mypass")
        assert SecretManager.verify_password("mypass", h, s)
        assert not SecretManager.verify_password("wrong", h, s)
