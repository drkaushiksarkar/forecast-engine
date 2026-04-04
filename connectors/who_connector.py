"""WHO Global Health Observatory data connector."""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

WHO_GHO_BASE = "https://ghoapi.azureedge.net/api"

class WHOConnector:
    """Fetches indicator data from WHO GHO API."""

    def __init__(self, base_url: str = WHO_GHO_BASE, timeout: int = 30) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self._request_count = 0

    def get_indicators(self, category: str = "") -> list[dict[str, Any]]:
        self._request_count += 1
        logger.info("Fetching WHO indicators, category=%s", category)
        return []

    def get_data(self, indicator_code: str, iso3: str = "", year_start: int = 2000, year_end: int = 2025) -> list[dict[str, Any]]:
        self._request_count += 1
        logger.info("Fetching WHO data: %s for %s (%d-%d)", indicator_code, iso3 or "all", year_start, year_end)
        return []

    def get_country_metadata(self, iso3: str) -> dict[str, Any]:
        self._request_count += 1
        return {"iso3": iso3, "source": "WHO GHO"}

    @property
    def stats(self) -> dict[str, int]:
        return {"requests": self._request_count}
