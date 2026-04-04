"""Data quality assessment and validation framework."""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Sequence


class QualityDimension(Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    dimension: QualityDimension
    severity: Severity
    field_name: str
    description: str
    affected_count: int = 0
    total_count: int = 0
    example_values: list[Any] = field(default_factory=list)

    @property
    def affected_ratio(self) -> float:
        return self.affected_count / self.total_count if self.total_count > 0 else 0.0


@dataclass
class QualityScore:
    dimension: QualityDimension
    score: float
    weight: float = 1.0
    issues: list[QualityIssue] = field(default_factory=list)


@dataclass
class QualityReport:
    dataset_name: str
    record_count: int
    field_count: int
    assessed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    scores: list[QualityScore] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        if not self.scores:
            return 0.0
        total_weight = sum(s.weight for s in self.scores)
        if total_weight == 0:
            return 0.0
        return sum(s.score * s.weight for s in self.scores) / total_weight

    @property
    def all_issues(self) -> list[QualityIssue]:
        return [issue for score in self.scores for issue in score.issues]

    @property
    def critical_issues(self) -> list[QualityIssue]:
        return [i for i in self.all_issues if i.severity == Severity.CRITICAL]


class DataQualityAssessor:
    """Comprehensive data quality assessment engine."""

    def __init__(self, dataset_name: str) -> None:
        self.dataset_name = dataset_name
        self._checks: list[tuple[QualityDimension, str, Any]] = []

    def assess(self, records: Sequence[dict[str, Any]]) -> QualityReport:
        if not records:
            return QualityReport(
                dataset_name=self.dataset_name, record_count=0, field_count=0
            )
        all_fields = set()
        for r in records:
            all_fields.update(r.keys())
        report = QualityReport(
            dataset_name=self.dataset_name,
            record_count=len(records),
            field_count=len(all_fields),
        )
        report.scores.append(self._check_completeness(records, all_fields))
        report.scores.append(self._check_consistency(records, all_fields))
        report.scores.append(self._check_uniqueness(records))
        report.scores.append(self._check_validity(records, all_fields))
        return report

    def _check_completeness(
        self, records: Sequence[dict], fields: set[str]
    ) -> QualityScore:
        issues: list[QualityIssue] = []
        total_cells = len(records) * len(fields)
        missing_cells = 0
        for f in fields:
            missing = sum(
                1 for r in records if f not in r or r[f] is None or r[f] == ""
            )
            if missing > 0:
                missing_cells += missing
                ratio = missing / len(records)
                sev = (
                    Severity.CRITICAL if ratio > 0.5
                    else Severity.ERROR if ratio > 0.2
                    else Severity.WARNING if ratio > 0.05
                    else Severity.INFO
                )
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.COMPLETENESS,
                        severity=sev,
                        field_name=f,
                        description=f"{missing}/{len(records)} records missing value",
                        affected_count=missing,
                        total_count=len(records),
                    )
                )
        score = 1.0 - (missing_cells / total_cells) if total_cells > 0 else 1.0
        return QualityScore(
            dimension=QualityDimension.COMPLETENESS,
            score=max(0.0, score),
            weight=1.5,
            issues=issues,
        )

    def _check_consistency(
        self, records: Sequence[dict], fields: set[str]
    ) -> QualityScore:
        issues: list[QualityIssue] = []
        type_issues = 0
        for f in fields:
            types_seen: set[str] = set()
            for r in records:
                if f in r and r[f] is not None:
                    types_seen.add(type(r[f]).__name__)
            if len(types_seen) > 1:
                type_issues += 1
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.CONSISTENCY,
                        severity=Severity.WARNING,
                        field_name=f,
                        description=f"Mixed types detected: {types_seen}",
                        affected_count=len(types_seen),
                        total_count=len(records),
                    )
                )
        score = 1.0 - (type_issues / len(fields)) if fields else 1.0
        return QualityScore(
            dimension=QualityDimension.CONSISTENCY,
            score=max(0.0, score),
            weight=1.0,
            issues=issues,
        )

    def _check_uniqueness(self, records: Sequence[dict]) -> QualityScore:
        issues: list[QualityIssue] = []
        hashes = []
        for r in records:
            h = hashlib.md5(str(sorted(r.items())).encode()).hexdigest()
            hashes.append(h)
        counts = Counter(hashes)
        duplicates = sum(c - 1 for c in counts.values() if c > 1)
        if duplicates > 0:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.UNIQUENESS,
                    severity=Severity.WARNING if duplicates < len(records) * 0.05
                    else Severity.ERROR,
                    field_name="*",
                    description=f"{duplicates} duplicate records found",
                    affected_count=duplicates,
                    total_count=len(records),
                )
            )
        score = 1.0 - (duplicates / len(records)) if records else 1.0
        return QualityScore(
            dimension=QualityDimension.UNIQUENESS,
            score=max(0.0, score),
            weight=1.0,
            issues=issues,
        )

    def _check_validity(
        self, records: Sequence[dict], fields: set[str]
    ) -> QualityScore:
        issues: list[QualityIssue] = []
        invalid_count = 0
        total_checked = 0
        iso_date = re.compile(r"^\d{4}-\d{2}-\d{2}")
        for f in fields:
            if any(kw in f.lower() for kw in ("date", "time", "created", "updated")):
                for r in records:
                    val = r.get(f)
                    if isinstance(val, str) and val:
                        total_checked += 1
                        if not iso_date.match(val):
                            invalid_count += 1
                if invalid_count > 0:
                    issues.append(
                        QualityIssue(
                            dimension=QualityDimension.VALIDITY,
                            severity=Severity.ERROR,
                            field_name=f,
                            description=f"{invalid_count} invalid date formats",
                            affected_count=invalid_count,
                            total_count=total_checked,
                        )
                    )
            if any(kw in f.lower() for kw in ("lat", "latitude")):
                for r in records:
                    val = r.get(f)
                    if isinstance(val, (int, float)):
                        total_checked += 1
                        if not (-90 <= val <= 90):
                            invalid_count += 1
            if any(kw in f.lower() for kw in ("lon", "longitude", "lng")):
                for r in records:
                    val = r.get(f)
                    if isinstance(val, (int, float)):
                        total_checked += 1
                        if not (-180 <= val <= 180):
                            invalid_count += 1
        score = 1.0 - (invalid_count / total_checked) if total_checked > 0 else 1.0
        return QualityScore(
            dimension=QualityDimension.VALIDITY,
            score=max(0.0, score),
            weight=1.2,
            issues=issues,
        )
