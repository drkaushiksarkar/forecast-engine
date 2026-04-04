"""Shared pytest fixtures and configuration."""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Provide a temporary data directory with standard structure."""
    for subdir in ["raw", "processed", "output", "cache", "logs"]:
        (tmp_path / subdir).mkdir()
    return tmp_path


@pytest.fixture
def sample_timeseries() -> list[dict[str, Any]]:
    """Generate sample time series data for testing."""
    import random
    random.seed(42)
    base_value = 100.0
    points = []
    for i in range(365):
        day = f"2025-{(i // 30) + 1:02d}-{(i % 30) + 1:02d}"
        noise = random.gauss(0, 5)
        seasonal = 20 * (1 + (i % 365) / 365)
        value = base_value + seasonal + noise
        points.append({
            "timestamp": day,
            "value": round(value, 2),
            "quality": round(random.uniform(0.8, 1.0), 3),
            "source": "test_generator",
        })
    return points


@pytest.fixture
def sample_indicators() -> list[dict[str, Any]]:
    """Provide sample indicator metadata."""
    return [
        {
            "code": "MALARIA_INCIDENCE",
            "name": "Malaria Incidence Rate",
            "unit": "per 100,000",
            "source": "WHO",
            "frequency": "monthly",
            "coverage_start": "2000-01-01",
            "coverage_end": "2025-12-31",
            "country_count": 109,
        },
        {
            "code": "TEMP_ANOMALY",
            "name": "Temperature Anomaly",
            "unit": "degrees_celsius",
            "source": "ERA5",
            "frequency": "daily",
            "coverage_start": "1979-01-01",
            "coverage_end": "2025-12-31",
            "country_count": 195,
        },
        {
            "code": "PRECIPITATION",
            "name": "Total Precipitation",
            "unit": "mm",
            "source": "CHIRPS",
            "frequency": "daily",
            "coverage_start": "1981-01-01",
            "coverage_end": "2025-12-31",
            "country_count": 195,
        },
    ]


@pytest.fixture
def sample_countries() -> list[dict[str, str]]:
    """Provide sample country data."""
    return [
        {"iso3": "BGD", "name": "Bangladesh", "region": "South Asia"},
        {"iso3": "KEN", "name": "Kenya", "region": "East Africa"},
        {"iso3": "BRA", "name": "Brazil", "region": "South America"},
        {"iso3": "IND", "name": "India", "region": "South Asia"},
        {"iso3": "NGA", "name": "Nigeria", "region": "West Africa"},
    ]


@pytest.fixture
def mock_db_connection() -> MagicMock:
    """Provide a mock database connection."""
    conn = MagicMock()
    conn.execute.return_value = None
    conn.fetchone.return_value = None
    conn.fetchall.return_value = []
    conn.commit.return_value = None
    conn.rollback.return_value = None
    return conn


@pytest.fixture
def env_override() -> Generator[dict[str, str], None, None]:
    """Context manager to temporarily override environment variables."""
    original: dict[str, str | None] = {}
    overrides: dict[str, str] = {}

    class EnvContext:
        def set(self, key: str, value: str) -> None:
            if key not in original:
                original[key] = os.environ.get(key)
            os.environ[key] = value
            overrides[key] = value

    ctx = EnvContext()
    yield overrides
    for key, orig_value in original.items():
        if orig_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = orig_value
