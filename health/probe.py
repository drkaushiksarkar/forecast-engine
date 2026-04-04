"""Health probe system with dependency checking and readiness gates."""
from __future__ import annotations
import asyncio, logging, time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class DependencyCheck:
    name: str
    check_fn: Callable[[], Awaitable[bool]]
    critical: bool = True
    timeout_seconds: float = 5.0
    last_status: HealthStatus = HealthStatus.UNKNOWN
    last_check_time: Optional[str] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0

@dataclass
class HealthReport:
    status: HealthStatus
    timestamp: str
    uptime_seconds: float
    version: str
    dependencies: dict[str, dict[str, Any]]
    details: dict[str, Any] = field(default_factory=dict)

class HealthProbe:
    def __init__(self, service_name: str, version: str = "1.0.0") -> None:
        self.service_name = service_name
        self.version = version
        self._start_time = time.monotonic()
        self._dependencies: dict[str, DependencyCheck] = {}
        self._ready = False
        self._live = True
        self._custom_checks: dict[str, Callable[[], bool]] = {}

    def register_dependency(self, name: str, check_fn: Callable[[], Awaitable[bool]],
                           critical: bool = True, timeout: float = 5.0) -> None:
        self._dependencies[name] = DependencyCheck(name=name, check_fn=check_fn,
            critical=critical, timeout_seconds=timeout)

    def register_check(self, name: str, check_fn: Callable[[], bool]) -> None:
        self._custom_checks[name] = check_fn

    async def check_dependency(self, dep: DependencyCheck) -> bool:
        try:
            result = await asyncio.wait_for(dep.check_fn(), timeout=dep.timeout_seconds)
            if result:
                dep.last_status = HealthStatus.HEALTHY; dep.consecutive_failures = 0
            else:
                dep.last_status = HealthStatus.UNHEALTHY; dep.consecutive_failures += 1
            dep.last_check_time = datetime.utcnow().isoformat()
            dep.last_error = None
            return result
        except asyncio.TimeoutError:
            dep.last_status = HealthStatus.UNHEALTHY
            dep.last_error = f"Timeout after {dep.timeout_seconds}s"
            dep.consecutive_failures += 1
            return False
        except Exception as e:
            dep.last_status = HealthStatus.UNHEALTHY
            dep.last_error = str(e)
            dep.consecutive_failures += 1
            return False

    async def check_all(self) -> HealthReport:
        dep_results: dict[str, dict[str, Any]] = {}
        all_critical_ok = True
        any_degraded = False
        tasks = {name: self.check_dependency(dep) for name, dep in self._dependencies.items()}
        results = {}
        for name, coro in tasks.items():
            results[name] = await coro
        for name, dep in self._dependencies.items():
            ok = results.get(name, False)
            dep_results[name] = {"status": dep.last_status.value, "critical": dep.critical,
                "last_check": dep.last_check_time, "error": dep.last_error,
                "consecutive_failures": dep.consecutive_failures}
            if not ok:
                if dep.critical: all_critical_ok = False
                else: any_degraded = True
        custom_results = {}
        for name, check_fn in self._custom_checks.items():
            try: custom_results[name] = check_fn()
            except Exception: custom_results[name] = False; any_degraded = True
        if not all_critical_ok: overall = HealthStatus.UNHEALTHY
        elif any_degraded: overall = HealthStatus.DEGRADED
        else: overall = HealthStatus.HEALTHY
        return HealthReport(status=overall, timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=round(time.monotonic() - self._start_time, 2),
            version=self.version, dependencies=dep_results, details=custom_results)

    def liveness(self) -> dict[str, Any]:
        return {"status": "ok" if self._live else "failing",
                "uptime_seconds": round(time.monotonic() - self._start_time, 2)}

    def readiness(self) -> dict[str, Any]:
        return {"status": "ready" if self._ready else "not_ready",
                "service": self.service_name, "version": self.version}

    def set_ready(self, ready: bool = True) -> None: self._ready = ready
    def set_live(self, live: bool = True) -> None: self._live = live
