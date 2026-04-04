"""Tests for task scheduler."""
import time
import pytest

class TestTaskScheduler:
    def test_basic_execution(self):
        from scheduler.core import TaskScheduler, Priority
        s = TaskScheduler()
        results = []
        s.schedule("t1", lambda: results.append("a"))
        s.schedule("t2", lambda: results.append("b"))
        s.run_all(timeout=5); assert len(results) == 2
    def test_priority_ordering(self):
        from scheduler.core import TaskScheduler, Priority
        s = TaskScheduler(max_concurrent=1); order = []
        s.schedule("low", lambda: order.append("low"), Priority.LOW)
        s.schedule("high", lambda: order.append("high"), Priority.HIGH)
        s.schedule("critical", lambda: order.append("critical"), Priority.CRITICAL)
        s.run_all(timeout=5)
        assert order[0] == "critical"; assert order[-1] == "low"
    def test_dependency_resolution(self):
        from scheduler.core import TaskScheduler, Priority
        s = TaskScheduler(); order = []
        t1 = s.schedule("setup", lambda: order.append("setup"))
        s.schedule("main", lambda: order.append("main"), dependencies=[t1])
        s.run_all(timeout=5)
        assert order == ["setup", "main"]
    def test_retry_on_failure(self):
        from scheduler.core import TaskScheduler
        s = TaskScheduler(); calls = [0]
        def flaky():
            calls[0] += 1
            if calls[0] < 3: raise ValueError("transient")
            return "ok"
        s.schedule("flaky", flaky, max_retries=5)
        tasks = s.run_all(timeout=10)
        completed = [t for t in tasks if t.state.value == "completed"]
        assert len(completed) == 1
    def test_cancel(self):
        from scheduler.core import TaskScheduler
        s = TaskScheduler()
        tid = s.schedule("cancel_me", lambda: None)
        assert s.cancel(tid)
        tasks = s.run_all(timeout=5)
        assert tasks[0].state.value == "cancelled"
    def test_stats(self):
        from scheduler.core import TaskScheduler
        s = TaskScheduler()
        s.schedule("a", lambda: None); s.schedule("b", lambda: None)
        s.run_all(timeout=5)
        stats = s.stats; assert stats.get("completed", 0) == 2
