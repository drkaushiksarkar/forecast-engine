"""Tests for data validation framework."""
import pytest
from utils.validation import (
    FieldValidator, DatasetValidator, ValidationReport, Severity,
)


class TestFieldValidator:
    def test_valid_iso3(self):
        assert FieldValidator.validate_iso3("USA") is None
        assert FieldValidator.validate_iso3("BGD") is None

    def test_invalid_iso3_lowercase(self):
        result = FieldValidator.validate_iso3("usa")
        assert result is not None
        assert result.severity == Severity.ERROR

    def test_invalid_iso3_length(self):
        result = FieldValidator.validate_iso3("US")
        assert result is not None
        assert result.severity == Severity.ERROR

    def test_invalid_iso3_numeric(self):
        result = FieldValidator.validate_iso3(123)
        assert result is not None

    def test_valid_year(self):
        assert FieldValidator.validate_year(2024) is None
        assert FieldValidator.validate_year(1900) is None
        assert FieldValidator.validate_year(2100) is None

    def test_invalid_year_out_of_range(self):
        result = FieldValidator.validate_year(1800)
        assert result is not None
        assert result.severity == Severity.ERROR

    def test_invalid_year_type(self):
        result = FieldValidator.validate_year("2024")
        assert result is not None

    def test_positive_check_negative(self):
        result = FieldValidator.validate_positive("cases", -5)
        assert result is not None
        assert result.severity == Severity.WARNING

    def test_positive_check_valid(self):
        assert FieldValidator.validate_positive("cases", 100) is None

    def test_not_null_fails(self):
        result = FieldValidator.validate_not_null("iso3", None)
        assert result is not None
        assert result.severity == Severity.ERROR

    def test_not_null_passes(self):
        assert FieldValidator.validate_not_null("iso3", "BGD") is None


class TestDatasetValidator:
    def setup_method(self):
        self.validator = DatasetValidator(completeness_threshold=0.95)

    def test_complete_dataset(self):
        records = [{"iso3": "BGD", "year": 2024, "value": 100}] * 100
        report = self.validator.validate_completeness(records, ["iso3", "year", "value"])
        assert report.passed is True

    def test_incomplete_dataset(self):
        records = [{"iso3": "BGD", "year": 2024}] * 100
        records[0]["value"] = 50
        report = self.validator.validate_completeness(records, ["iso3", "year", "value"])
        assert report.passed is False
        assert len(report.errors) > 0

    def test_empty_dataset(self):
        report = self.validator.validate_completeness([], ["iso3"])
        assert report.passed is False

    def test_temporal_consistency_no_gaps(self):
        records = [{"year": y} for y in range(2015, 2025)]
        report = self.validator.validate_temporal_consistency(records)
        assert len(report.warnings) == 0

    def test_temporal_consistency_with_gap(self):
        records = [{"year": 2015}, {"year": 2016}, {"year": 2020}]
        report = self.validator.validate_temporal_consistency(records)
        assert len(report.warnings) > 0

    def test_report_summary(self):
        report = ValidationReport()
        assert report.summary()["total"] == 0
        assert report.passed is True
