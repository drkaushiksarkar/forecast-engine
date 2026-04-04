"""Tests for domain exception hierarchy."""
import pytest
from exceptions import (
    BaseError, DataError, ValidationError, SchemaError,
    SourceUnavailableError, PipelineError, StageError,
    CheckpointError, InferenceError, TrainingError,
)


class TestBaseError:
    def test_to_dict(self):
        err = BaseError("test", code="TEST_ERR", context={"key": "val"})
        d = err.to_dict()
        assert d["error"] == "TEST_ERR"
        assert d["message"] == "test"
        assert d["context"]["key"] == "val"
        assert d["retryable"] is False

    def test_retryable_flag(self):
        err = BaseError("test", retryable=True)
        assert err.retryable is True


class TestValidationError:
    def test_message_format(self):
        err = ValidationError("iso3", "invalid format", value="XX")
        assert "iso3" in str(err)
        assert "invalid format" in str(err)

    def test_context(self):
        err = ValidationError("year", "out of range", value=1800)
        assert err.context["field"] == "year"


class TestSchemaError:
    def test_message(self):
        err = SchemaError("v2", "v1")
        assert "v2" in str(err)
        assert "v1" in str(err)


class TestSourceUnavailableError:
    def test_retryable(self):
        err = SourceUnavailableError("WHO GHO", "timeout")
        assert err.retryable is True
        assert "WHO GHO" in str(err)


class TestStageError:
    def test_stage_context(self):
        err = StageError("data_fusion", "schema mismatch")
        assert err.context["stage"] == "data_fusion"


class TestCheckpointError:
    def test_retryable(self):
        err = CheckpointError("save", "/mnt/data/checkpoint-001")
        assert err.retryable is True


class TestInferenceError:
    def test_model_context(self):
        err = InferenceError("sage-72b", "OOM")
        assert err.context["model_id"] == "sage-72b"
        assert err.retryable is True


class TestTrainingError:
    def test_phase_step(self):
        err = TrainingError("sft", 5000, "loss diverged")
        assert err.context["phase"] == "sft"
        assert err.context["step"] == 5000
