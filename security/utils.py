"""Security utilities: input sanitization, HMAC signing, secret management."""
from __future__ import annotations
import base64, hashlib, hmac, os, re, secrets, time
from dataclasses import dataclass
from typing import Optional

class InputSanitizer:
    SQL_PATTERNS = [re.compile(r"(\b(union|select|insert|update|delete|drop|alter|create)\b.*\b(from|into|table|database)\b)", re.I),
                    re.compile(r"(--|;|/\*|\*/|xp_|sp_)", re.I)]
    XSS_PATTERNS = [re.compile(r"<script[^>]*>", re.I), re.compile(r"javascript:", re.I),
                    re.compile(r"on\w+\s*=", re.I), re.compile(r"<iframe", re.I)]
    PATH_TRAVERSAL = re.compile(r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e/)", re.I)
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        value = value[:max_length].replace("\x00", "")
        for p in cls.XSS_PATTERNS: value = p.sub("", value)
        return value.strip()
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        return any(p.search(value) for p in cls.SQL_PATTERNS)
    @classmethod
    def sanitize_path(cls, path: str) -> str:
        if cls.PATH_TRAVERSAL.search(path): raise ValueError("Path traversal detected")
        return re.sub(r"[^\w\-./]", "_", path.replace("\x00", ""))
    @classmethod
    def sanitize_email(cls, email: str) -> Optional[str]:
        e = email.strip().lower()
        return e if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e) else None

class HMACSigner:
    def __init__(self, secret_key: str, algorithm: str = "sha256") -> None:
        self._key = secret_key.encode("utf-8"); self._algorithm = algorithm
    def sign(self, payload: str, timestamp: Optional[int] = None) -> str:
        ts = timestamp or int(time.time())
        sig = hmac.new(self._key, f"{ts}.{payload}".encode("utf-8"), getattr(hashlib, self._algorithm)).hexdigest()
        return f"t={ts},v1={sig}"
    def verify(self, payload: str, sig_header: str, tolerance: int = 300) -> bool:
        parts = {}
        for p in sig_header.split(","): k, _, v = p.partition("="); parts[k] = v
        if "t" not in parts or "v1" not in parts: return False
        if abs(time.time() - int(parts["t"])) > tolerance: return False
        expected = self.sign(payload, int(parts["t"]))
        ep = {}
        for p in expected.split(","): k, _, v = p.partition("="); ep[k] = v
        return hmac.compare_digest(parts["v1"], ep["v1"])

class SecretManager:
    def __init__(self, prefix: str = "APP") -> None: self._prefix = prefix; self._cache: dict[str, str] = {}
    def get(self, name: str, required: bool = True) -> Optional[str]:
        key = f"{self._prefix}_{name}".upper()
        if key in self._cache: return self._cache[key]
        value = os.environ.get(key)
        if value is None and required: raise EnvironmentError(f"Required secret {key} not found")
        if value: self._cache[key] = value
        return value
    @staticmethod
    def generate_key(length: int = 32) -> str: return secrets.token_urlsafe(length)
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        s = salt or os.urandom(32)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), s, 100000)
        return base64.b64encode(key).decode(), base64.b64encode(s).decode()
    @staticmethod
    def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
        s = base64.b64decode(stored_salt)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), s, 100000)
        return hmac.compare_digest(base64.b64encode(key).decode(), stored_hash)
