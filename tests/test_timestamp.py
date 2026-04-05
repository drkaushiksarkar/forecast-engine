from datetime import datetime, timezone, timedelta
from utils.timestamp import parse_timestamp


def test_positive_offset_converts_to_utc():
    result = parse_timestamp("2024-03-15T10:30:00+05:30")
    expected = datetime(2024, 3, 15, 5, 0, 0, tzinfo=timezone.utc)
    assert result == expected


def test_negative_offset_converts_to_utc():
    result = parse_timestamp("2024-03-15T10:30:00-04:00")
    expected = datetime(2024, 3, 15, 14, 30, 0, tzinfo=timezone.utc)
    assert result == expected


def test_zulu_stays_utc():
    result = parse_timestamp("2024-03-15T10:30:00+00:00")
    expected = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
    assert result == expected


def test_naive_assumed_utc():
    result = parse_timestamp("2024-03-15T10:30:00")
    expected = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
    assert result == expected


def test_date_rollover_on_conversion():
    result = parse_timestamp("2024-03-15T02:00:00+05:30")
    expected = datetime(2024, 3, 14, 20, 30, 0, tzinfo=timezone.utc)
    assert result == expected
