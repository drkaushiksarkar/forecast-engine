"""Health check endpoints for service monitoring."""
from __future__ import annotations
import os
import platform
import time
from typing import Any

_start_time = time.time()

def liveness() -> dict[str, Any]:
    return {"status": "ok", "timestamp": time.time()}

def readiness(checks: dict[str, bool] | None = None) -> dict[str, Any]:
    checks = checks or {}
    all_ready = all(checks.values()) if checks else True
    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "timestamp": time.time(),
    }

def startup_info() -> dict[str, Any]:
    return {
        "service": os.getenv("SERVICE_NAME", "health-intelligence"),
        "version": os.getenv("SERVICE_VERSION", "0.0.0"),
        "environment": os.getenv("APP_ENV", "production"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "uptime_seconds": round(time.time() - _start_time, 2),
        "pid": os.getpid(),
    }

class HealthChecker:
    def __init__(self) -> None:
        self._checks: dict[str, callable] = {}

    def register(self, name: str, check_fn: callable) -> None:
        self._checks[name] = check_fn

    def run_all(self) -> dict[str, Any]:
        results = {}
        for name, fn in self._checks.items():
            try:
                results[name] = fn()
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e)}
        return readiness({k: v.get("healthy", False) if isinstance(v, dict) else bool(v) for k, v in results.items()})
