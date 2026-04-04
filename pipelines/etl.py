"""ETL pipeline framework with stage composition and error recovery."""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StageResult:
    name: str
    status: StageStatus
    records_in: int = 0
    records_out: int = 0
    elapsed_seconds: float = 0.0
    error: str | None = None

@dataclass
class PipelineResult:
    pipeline_id: str
    stages: list[StageResult] = field(default_factory=list)
    total_elapsed: float = 0.0

    @property
    def success(self) -> bool:
        return all(s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED) for s in self.stages)

class Stage:
    """Single ETL stage with transform function and validation."""

    def __init__(self, name: str, transform: Callable, validator: Callable | None = None) -> None:
        self.name = name
        self._transform = transform
        self._validator = validator

    def execute(self, data: Any) -> tuple[Any, StageResult]:
        start = time.monotonic()
        try:
            records_in = len(data) if hasattr(data, "__len__") else 0
            result = self._transform(data)
            records_out = len(result) if hasattr(result, "__len__") else 0
            if self._validator and not self._validator(result):
                return result, StageResult(self.name, StageStatus.FAILED, records_in, records_out,
                                           time.monotonic() - start, "Validation failed")
            return result, StageResult(self.name, StageStatus.COMPLETED, records_in, records_out,
                                       time.monotonic() - start)
        except Exception as e:
            logger.error("Stage %s failed: %s", self.name, e)
            return data, StageResult(self.name, StageStatus.FAILED, error=str(e),
                                     elapsed_seconds=time.monotonic() - start)

class Pipeline:
    """Composable ETL pipeline with ordered stages."""

    def __init__(self, pipeline_id: str) -> None:
        self.pipeline_id = pipeline_id
        self._stages: list[Stage] = []

    def add_stage(self, name: str, transform: Callable, validator: Callable | None = None) -> Pipeline:
        self._stages.append(Stage(name, transform, validator))
        return self

    def execute(self, data: Any) -> PipelineResult:
        start = time.monotonic()
        result = PipelineResult(self.pipeline_id)
        current_data = data
        for stage in self._stages:
            current_data, stage_result = stage.execute(current_data)
            result.stages.append(stage_result)
            if stage_result.status == StageStatus.FAILED:
                logger.error("Pipeline %s halted at stage %s", self.pipeline_id, stage.name)
                break
        result.total_elapsed = time.monotonic() - start
        return result
