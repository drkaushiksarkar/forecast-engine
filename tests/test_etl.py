"""Tests for ETL pipeline framework."""
import pytest
from pipelines.etl import Pipeline, StageStatus
from pipelines.transforms import normalize_iso3, filter_nulls, deduplicate, cast_numeric, clip_values


class TestPipeline:
    def test_simple_pipeline(self):
        pipeline = Pipeline("test-001")
        pipeline.add_stage("double", lambda data: [x * 2 for x in data])
        pipeline.add_stage("filter", lambda data: [x for x in data if x > 5])
        result = pipeline.execute([1, 2, 3, 4, 5])
        assert result.success is True
        assert len(result.stages) == 2

    def test_failed_stage_halts(self):
        pipeline = Pipeline("test-002")
        pipeline.add_stage("fail", lambda data: 1 / 0)
        pipeline.add_stage("never", lambda data: data)
        result = pipeline.execute([1])
        assert result.success is False
        assert len(result.stages) == 1
        assert result.stages[0].status == StageStatus.FAILED

    def test_validation_failure(self):
        pipeline = Pipeline("test-003")
        pipeline.add_stage("transform", lambda d: d, validator=lambda d: len(d) > 10)
        result = pipeline.execute([1, 2, 3])
        assert result.success is False


class TestTransforms:
    def test_normalize_iso3(self):
        data = [{"iso3": "bgd"}, {"iso3": " IND "}]
        result = normalize_iso3(data)
        assert result[0]["iso3"] == "BGD"
        assert result[1]["iso3"] == "IND"

    def test_filter_nulls(self):
        data = [{"a": 1, "b": 2}, {"a": None, "b": 3}, {"a": 4, "b": None}]
        result = filter_nulls(data, ["a", "b"])
        assert len(result) == 1

    def test_deduplicate(self):
        data = [{"iso3": "BGD", "year": 2024}, {"iso3": "BGD", "year": 2024}, {"iso3": "IND", "year": 2024}]
        result = deduplicate(data, ["iso3", "year"])
        assert len(result) == 2

    def test_cast_numeric(self):
        data = [{"value": "123.4"}, {"value": "abc"}]
        result = cast_numeric(data, ["value"])
        assert result[0]["value"] == 123.4
        assert result[1]["value"] is None

    def test_clip_values(self):
        data = [{"v": -5}, {"v": 50}, {"v": 150}]
        result = clip_values(data, "v", min_val=0, max_val=100)
        assert result[0]["v"] == 0
        assert result[1]["v"] == 50
        assert result[2]["v"] == 100
