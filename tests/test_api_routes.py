"""Tests for API route definitions."""
import pytest
from api.routes import router


class TestRouter:
    def test_health_check(self):
        result = router.dispatch("GET", "/api/v1/health")
        assert result["status"] == "ok"

    def test_list_indicators(self):
        result = router.dispatch("GET", "/api/v1/indicators", domain="health")
        assert "indicators" in result

    def test_get_country(self):
        result = router.dispatch("GET", "/api/v1/countries/{iso3}", iso3="BGD")
        assert result["iso3"] == "BGD"

    def test_create_forecast(self):
        result = router.dispatch("POST", "/api/v1/forecast", indicator="MALARIA_CASES", entity="BGD")
        assert "forecast_id" in result

    def test_not_found(self):
        result = router.dispatch("GET", "/api/v1/nonexistent")
        assert result["status"] == 404

    def test_list_routes(self):
        routes = router.list_routes()
        assert len(routes) >= 5
        paths = [r["path"] for r in routes]
        assert "/api/v1/health" in paths
