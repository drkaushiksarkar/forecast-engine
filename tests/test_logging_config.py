"""Tests for structured logging configuration."""
import json
import logging
import pytest
from utils.logging_config import (
    StructuredFormatter, configure_logging, new_correlation_id, correlation_id,
)


class TestStructuredFormatter:
    def test_json_output(self):
        formatter = StructuredFormatter(service_name="test-svc")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="hello", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "hello"
        assert parsed["service"] == "test-svc"

    def test_correlation_id_included(self):
        formatter = StructuredFormatter()
        correlation_id.set("test-123")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="test", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["correlation_id"] == "test-123"
        correlation_id.set("")

    def test_exception_included(self):
        formatter = StructuredFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="test.py",
                lineno=1, msg="fail", args=(), exc_info=sys.exc_info(),
            )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["exception"]["type"] == "ValueError"


class TestCorrelationId:
    def test_new_correlation_id(self):
        cid = new_correlation_id()
        assert len(cid) == 12
        assert correlation_id.get() == cid

    def test_unique_ids(self):
        id1 = new_correlation_id()
        id2 = new_correlation_id()
        assert id1 != id2


class TestConfigureLogging:
    def test_configure_json(self):
        configure_logging(service_name="test", level="DEBUG", json_output=True)
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) == 1

    def test_configure_plain(self):
        configure_logging(service_name="test", level="INFO", json_output=False)
        root = logging.getLogger()
        assert root.level == logging.INFO
