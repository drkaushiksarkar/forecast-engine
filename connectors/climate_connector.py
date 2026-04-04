"""Climate data connectors for ERA5 and NOAA GSOD."""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

class ERA5Connector:
    """Fetches ERA5 reanalysis climate data."""

    def __init__(self, cds_api_key: str = "") -> None:
        self._api_key = cds_api_key
        self._request_count = 0

    def get_monthly(self, variable: str, lat: float, lon: float, year_start: int, year_end: int) -> list[dict[str, Any]]:
        self._request_count += 1
        logger.info("ERA5 query: %s at (%.2f, %.2f) %d-%d", variable, lat, lon, year_start, year_end)
        return []

    def get_daily(self, variable: str, bbox: tuple[float, float, float, float], date_start: str, date_end: str) -> list[dict[str, Any]]:
        self._request_count += 1
        return []

class NOAAConnector:
    """Fetches NOAA GSOD station data."""

    def __init__(self) -> None:
        self._request_count = 0

    def get_stations(self, country: str = "", lat: float = 0.0, lon: float = 0.0, radius_km: float = 100.0) -> list[dict[str, Any]]:
        self._request_count += 1
        return []

    def get_station_data(self, station_id: str, year: int) -> list[dict[str, Any]]:
        self._request_count += 1
        return []
