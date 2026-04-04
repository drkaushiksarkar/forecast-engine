"""Tests for data schemas."""
import pytest
from schemas.indicator import IndicatorSchema, IndicatorDomain, AggregationMethod, CORE_INDICATORS
from schemas.country import CountrySchema, AdminRegion, REGIONS
from schemas.timeseries import TimeSeries, TimeSeriesPoint, Frequency
from schemas.forecast import ForecastResult, ForecastPoint
from schemas.alert import Alert, AlertRule, AlertSeverity, AlertType
from datetime import date


class TestIndicatorSchema:
    def test_validate_in_range(self):
        schema = IndicatorSchema("TEMP", "Temperature", IndicatorDomain.CLIMATE, "celsius", min_value=-60, max_value=60)
        assert schema.validate_value(25.0) is True
        assert schema.validate_value(-70.0) is False
        assert schema.validate_value(70.0) is False

    def test_to_dict(self):
        schema = CORE_INDICATORS[0]
        d = schema.to_dict()
        assert d["code"] == "MALARIA_CASES"
        assert d["domain"] == "health"

    def test_core_indicators_count(self):
        assert len(CORE_INDICATORS) >= 5


class TestCountrySchema:
    def test_valid_country(self):
        c = CountrySchema("BGD", "BD", "Bangladesh", "SEAR", population=170000000)
        assert c.iso3 == "BGD"

    def test_invalid_iso3(self):
        with pytest.raises(ValueError):
            CountrySchema("XX", "X", "Invalid", "")

    def test_to_dict(self):
        c = CountrySchema("USA", "US", "United States", "AMR")
        d = c.to_dict()
        assert d["region"] == "AMR"


class TestTimeSeries:
    def test_slice(self):
        points = [TimeSeriesPoint(date(2020 + i, 1, 1), float(i * 10)) for i in range(5)]
        ts = TimeSeries("CASES", "BGD", Frequency.ANNUAL, points)
        sliced = ts.slice(date(2021, 1, 1), date(2023, 1, 1))
        assert sliced.length == 3

    def test_outlier_detection(self):
        points = [TimeSeriesPoint(date(2020, 1, i + 1), 10.0) for i in range(20)]
        points.append(TimeSeriesPoint(date(2020, 1, 21), 1000.0))
        ts = TimeSeries("CASES", "BGD", Frequency.DAILY, points)
        outliers = ts.detect_outliers(z_threshold=2.0)
        assert 20 in outliers

    def test_values(self):
        points = [TimeSeriesPoint(date(2020, 1, 1), 10.0), TimeSeriesPoint(date(2021, 1, 1), 20.0)]
        ts = TimeSeries("CASES", "BGD", Frequency.ANNUAL, points)
        assert ts.values() == [10.0, 20.0]


class TestForecastResult:
    def test_mae(self):
        points = [ForecastPoint(date(2025, i, 1), float(i * 10), 0, 0) for i in range(1, 4)]
        result = ForecastResult("model1", "CASES", "BGD", 3, points)
        mae = result.mae([10.0, 20.0, 30.0])
        assert mae == 0.0

    def test_coverage(self):
        points = [ForecastPoint(date(2025, 1, 1), 10.0, 5.0, 15.0)]
        result = ForecastResult("model1", "CASES", "BGD", 1, points)
        assert result.coverage([10.0]) == 1.0
        assert result.coverage([20.0]) == 0.0


class TestAlertRule:
    def test_evaluate_gt(self):
        rule = AlertRule("r1", "CASES", "gt", 100, AlertSeverity.HIGH)
        assert rule.evaluate(150) is True
        assert rule.evaluate(50) is False

    def test_evaluate_disabled(self):
        rule = AlertRule("r1", "CASES", "gt", 100, AlertSeverity.HIGH, enabled=False)
        assert rule.evaluate(150) is False
