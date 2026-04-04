"""Data validation framework for health intelligence pipelines.

Implements schema validation, range checks, completeness audits, and
temporal consistency verification for epidemiological datasets.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Sequence

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    field: str
    severity: Severity
    message: str
    value: Any = None
    rule: str = ""


@dataclass
class ValidationReport:
    results: list[ValidationResult] = field(default_factory=list)
    passed: bool = True

    def add(self, result: ValidationResult) -> None:
        self.results.append(result)
        if result.severity == Severity.ERROR:
            self.passed = False

    @property
    def errors(self) -> list[ValidationResult]:
        return [r for r in self.results if r.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationResult]:
        return [r for r in self.results if r.severity == Severity.WARNING]

    def summary(self) -> dict[str, int]:
        return {
            "total": len(self.results),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "passed": self.passed,
        }


class FieldValidator:
    """Validates individual fields against type and constraint rules."""

    @staticmethod
    def validate_iso3(value: Any) -> ValidationResult | None:
        if not isinstance(value, str) or not re.match(r"^[A-Z]{3}$", value):
            return ValidationResult(
                field="iso3", severity=Severity.ERROR,
                message=f"Invalid ISO3 code: {value}", value=value, rule="iso3_format",
            )
        return None

    @staticmethod
    def validate_year(value: Any, min_year: int = 1900, max_year: int = 2100) -> ValidationResult | None:
        if not isinstance(value, int) or value < min_year or value > max_year:
            return ValidationResult(
                field="year", severity=Severity.ERROR,
                message=f"Year {value} outside range [{min_year}, {max_year}]",
                value=value, rule="year_range",
            )
        return None

    @staticmethod
    def validate_positive(field_name: str, value: Any) -> ValidationResult | None:
        if isinstance(value, (int, float)) and value < 0:
            return ValidationResult(
                field=field_name, severity=Severity.WARNING,
                message=f"Negative value for {field_name}: {value}",
                value=value, rule="positive_check",
            )
        return None

    @staticmethod
    def validate_not_null(field_name: str, value: Any) -> ValidationResult | None:
        if value is None:
            return ValidationResult(
                field=field_name, severity=Severity.ERROR,
                message=f"Null value for required field: {field_name}",
                value=value, rule="not_null",
            )
        return None


class DatasetValidator:
    """Validates entire datasets against quality thresholds."""

    def __init__(self, completeness_threshold: float = 0.95) -> None:
        self.completeness_threshold = completeness_threshold
        self._validators: list[Callable] = []

    def add_rule(self, validator: Callable) -> None:
        self._validators.append(validator)

    def validate_completeness(
        self, records: Sequence[dict[str, Any]], required_fields: Sequence[str],
    ) -> ValidationReport:
        report = ValidationReport()
        total = len(records)
        if total == 0:
            report.add(ValidationResult(
                field="dataset", severity=Severity.ERROR,
                message="Empty dataset", rule="non_empty",
            ))
            return report

        for f in required_fields:
            present = sum(1 for r in records if r.get(f) is not None)
            ratio = present / total
            if ratio < self.completeness_threshold:
                report.add(ValidationResult(
                    field=f, severity=Severity.ERROR,
                    message=f"Completeness {ratio:.2%} below threshold {self.completeness_threshold:.2%}",
                    value=ratio, rule="completeness",
                ))
            else:
                report.add(ValidationResult(
                    field=f, severity=Severity.INFO,
                    message=f"Completeness {ratio:.2%}", value=ratio, rule="completeness",
                ))
        return report

    def validate_temporal_consistency(
        self, records: Sequence[dict[str, Any]], time_field: str = "year",
    ) -> ValidationReport:
        report = ValidationReport()
        years = sorted(set(r.get(time_field) for r in records if r.get(time_field) is not None))
        if len(years) < 2:
            return report

        gaps = []
        for i in range(1, len(years)):
            if years[i] - years[i - 1] > 1:
                gaps.append((years[i - 1], years[i]))

        if gaps:
            report.add(ValidationResult(
                field=time_field, severity=Severity.WARNING,
                message=f"Temporal gaps detected: {gaps}", value=gaps,
                rule="temporal_continuity",
            ))
        return report
