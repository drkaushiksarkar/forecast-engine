"""Task scheduler with cron-like scheduling, retries, and dependency resolution."""
from __future__ import annotations
import heapq, logging, time, uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

class TaskState(Enum):
    PENDING = "pending"; READY = "ready"; RUNNING = "running"
    COMPLETED = "completed"; FAILED = "failed"; CANCELLED = "cancelled"

class Priority(Enum):
    LOW = 3; NORMAL = 2; HIGH = 1; CRITICAL = 0

@dataclass(order=True)
class ScheduledTask:
    priority: int
    scheduled_at: float
    task_id: str = field(compare=False, default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = field(compare=False, default="")
    func: Optional[Callable] = field(compare=False, default=None)
    args: tuple = field(compare=False, default_factory=tuple)
    kwargs: dict = field(compare=False, default_factory=dict)
    state: TaskState = field(compare=False, default=TaskState.PENDING)
    max_retries: int = field(compare=False, default=3)
    retry_count: int = field(compare=False, default=0)
    retry_delay: float = field(compare=False, default=1.0)
    dependencies: list[str] = field(compare=False, default_factory=list)
    result: Any = field(compare=False, default=None)
    error: Optional[str] = field(compare=False, default=None)
    created_at: str = field(compare=False, default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = field(compare=False, default=None)
    completed_at: Optional[str] = field(compare=False, default=None)

class TaskScheduler:
    def __init__(self, max_concurrent: int = 4) -> None:
        self._queue: list[ScheduledTask] = []
        self._tasks: dict[str, ScheduledTask] = {}
        self._max_concurrent = max_concurrent
        self._running_count = 0
        self._completed: list[ScheduledTask] = []

    def schedule(self, name: str, func: Callable, priority: Priority = Priority.NORMAL,
                 delay_seconds: float = 0, max_retries: int = 3, dependencies: Optional[list[str]] = None,
                 args: tuple = (), kwargs: Optional[dict] = None) -> str:
        task = ScheduledTask(priority=priority.value, scheduled_at=time.monotonic() + delay_seconds,
            name=name, func=func, args=args, kwargs=kwargs or {}, max_retries=max_retries,
            dependencies=dependencies or [])
        self._tasks[task.task_id] = task
        heapq.heappush(self._queue, task)
        logger.info("Scheduled task %s: %s (priority=%s)", task.task_id, name, priority.name)
        return task.task_id

    def _deps_satisfied(self, task: ScheduledTask) -> bool:
        for dep_id in task.dependencies:
            dep = self._tasks.get(dep_id)
            if dep is None or dep.state != TaskState.COMPLETED:
                return False
        return True

    def _get_next(self) -> Optional[ScheduledTask]:
        now = time.monotonic()
        temp = []
        result = None
        while self._queue:
            task = heapq.heappop(self._queue)
            if task.state in (TaskState.COMPLETED, TaskState.CANCELLED, TaskState.FAILED):
                continue
            if task.scheduled_at > now or not self._deps_satisfied(task):
                temp.append(task)
                continue
            result = task
            break
        for t in temp:
            heapq.heappush(self._queue, t)
        return result

    def run_next(self) -> Optional[ScheduledTask]:
        if self._running_count >= self._max_concurrent:
            return None
        task = self._get_next()
        if task is None:
            return None
        task.state = TaskState.RUNNING
        task.started_at = datetime.utcnow().isoformat()
        self._running_count += 1
        try:
            task.result = task.func(*task.args, **task.kwargs)
            task.state = TaskState.COMPLETED
            task.completed_at = datetime.utcnow().isoformat()
            self._completed.append(task)
            logger.info("Task %s completed: %s", task.task_id, task.name)
        except Exception as e:
            task.retry_count += 1
            task.error = str(e)
            if task.retry_count <= task.max_retries:
                task.state = TaskState.PENDING
                task.scheduled_at = time.monotonic() + task.retry_delay * (2 ** task.retry_count)
                heapq.heappush(self._queue, task)
                logger.warning("Task %s failed (retry %d/%d): %s", task.task_id, task.retry_count, task.max_retries, e)
            else:
                task.state = TaskState.FAILED
                logger.error("Task %s permanently failed: %s", task.task_id, e)
        finally:
            self._running_count -= 1
        return task

    def run_all(self, timeout: float = 300) -> list[ScheduledTask]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            pending = [t for t in self._tasks.values() if t.state in (TaskState.PENDING, TaskState.READY)]
            if not pending: break
            task = self.run_next()
            if task is None: time.sleep(0.01)
        return list(self._tasks.values())

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.state in (TaskState.PENDING, TaskState.READY):
            task.state = TaskState.CANCELLED; return True
        return False

    @property
    def stats(self) -> dict[str, int]:
        from collections import Counter
        counts = Counter(t.state.value for t in self._tasks.values())
        return dict(counts)
