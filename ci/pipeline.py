"""CI/CD pipeline configuration and workflow management."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class PipelineStage(Enum):
    LINT = "lint"
    TYPE_CHECK = "type_check"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    BUILD = "build"
    DEPLOY = "deploy"


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    stage: PipelineStage
    status: StageStatus
    duration_seconds: float = 0.0
    output: str = ""
    error: Optional[str] = None
    artifacts: list[str] = field(default_factory=list)


@dataclass
class PipelineConfig:
    stages: list[PipelineStage] = field(default_factory=lambda: list(PipelineStage))
    fail_fast: bool = True
    parallel_stages: bool = False
    env_vars: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 3600
    working_dir: Path = field(default_factory=Path.cwd)


class CIPipeline:
    """Orchestrates CI/CD pipeline execution with stage management."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.results: list[StageResult] = []
        self._stage_handlers: dict[PipelineStage, Any] = {
            PipelineStage.LINT: self._run_lint,
            PipelineStage.TYPE_CHECK: self._run_type_check,
            PipelineStage.UNIT_TEST: self._run_unit_test,
            PipelineStage.INTEGRATION_TEST: self._run_integration_test,
            PipelineStage.BUILD: self._run_build,
            PipelineStage.DEPLOY: self._run_deploy,
        }

    def run(self) -> list[StageResult]:
        for stage in self.config.stages:
            handler = self._stage_handlers.get(stage)
            if handler is None:
                self.results.append(
                    StageResult(stage=stage, status=StageStatus.SKIPPED)
                )
                continue
            result = handler()
            self.results.append(result)
            if result.status == StageStatus.FAILED and self.config.fail_fast:
                remaining = [
                    s for s in self.config.stages
                    if s not in [r.stage for r in self.results]
                ]
                for skip_stage in remaining:
                    self.results.append(
                        StageResult(stage=skip_stage, status=StageStatus.SKIPPED)
                    )
                break
        return self.results

    def _execute_command(self, cmd: list[str]) -> tuple[int, str, str]:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=self.config.working_dir,
                env={**dict(subprocess.os.environ), **self.config.env_vars},
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except FileNotFoundError:
            return -1, "", f"Command not found: {cmd[0]}"

    def _run_lint(self) -> StageResult:
        import time
        start = time.monotonic()
        code, out, err = self._execute_command(
            [sys.executable, "-m", "ruff", "check", "."]
        )
        elapsed = time.monotonic() - start
        return StageResult(
            stage=PipelineStage.LINT,
            status=StageStatus.PASSED if code == 0 else StageStatus.FAILED,
            duration_seconds=elapsed,
            output=out,
            error=err if code != 0 else None,
        )

    def _run_type_check(self) -> StageResult:
        import time
        start = time.monotonic()
        code, out, err = self._execute_command(
            [sys.executable, "-m", "mypy", "--strict", "."]
        )
        elapsed = time.monotonic() - start
        return StageResult(
            stage=PipelineStage.TYPE_CHECK,
            status=StageStatus.PASSED if code == 0 else StageStatus.FAILED,
            duration_seconds=elapsed,
            output=out,
            error=err if code != 0 else None,
        )

    def _run_unit_test(self) -> StageResult:
        import time
        start = time.monotonic()
        code, out, err = self._execute_command(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
        )
        elapsed = time.monotonic() - start
        return StageResult(
            stage=PipelineStage.UNIT_TEST,
            status=StageStatus.PASSED if code == 0 else StageStatus.FAILED,
            duration_seconds=elapsed,
            output=out,
            error=err if code != 0 else None,
        )

    def _run_integration_test(self) -> StageResult:
        import time
        start = time.monotonic()
        code, out, err = self._execute_command(
            [sys.executable, "-m", "pytest", "tests/integration/", "-v", "--tb=short"]
        )
        elapsed = time.monotonic() - start
        return StageResult(
            stage=PipelineStage.INTEGRATION_TEST,
            status=StageStatus.PASSED if code == 0 else StageStatus.FAILED,
            duration_seconds=elapsed,
            output=out,
            error=err if code != 0 else None,
        )

    def _run_build(self) -> StageResult:
        import time
        start = time.monotonic()
        code, out, err = self._execute_command(
            [sys.executable, "-m", "build", "--wheel"]
        )
        elapsed = time.monotonic() - start
        artifacts = []
        if code == 0:
            dist = self.config.working_dir / "dist"
            if dist.exists():
                artifacts = [str(p) for p in dist.glob("*.whl")]
        return StageResult(
            stage=PipelineStage.BUILD,
            status=StageStatus.PASSED if code == 0 else StageStatus.FAILED,
            duration_seconds=elapsed,
            output=out,
            error=err if code != 0 else None,
            artifacts=artifacts,
        )

    def _run_deploy(self) -> StageResult:
        return StageResult(
            stage=PipelineStage.DEPLOY,
            status=StageStatus.SKIPPED,
            output="Deploy stage requires manual trigger",
        )

    def generate_report(self) -> dict[str, Any]:
        total_duration = sum(r.duration_seconds for r in self.results)
        passed = sum(1 for r in self.results if r.status == StageStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == StageStatus.FAILED)
        return {
            "total_stages": len(self.results),
            "passed": passed,
            "failed": failed,
            "skipped": len(self.results) - passed - failed,
            "total_duration_seconds": round(total_duration, 2),
            "success": failed == 0,
            "stages": [
                {
                    "name": r.stage.value,
                    "status": r.status.value,
                    "duration": round(r.duration_seconds, 2),
                    "artifacts": r.artifacts,
                }
                for r in self.results
            ],
        }
