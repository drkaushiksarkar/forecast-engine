"""Tests for data source connectors."""
import pytest
from connectors.who_connector import WHOConnector
from connectors.worldbank_connector import WorldBankConnector
from connectors.climate_connector import ERA5Connector, NOAAConnector


class TestWHOConnector:
    def test_init(self):
        conn = WHOConnector()
        assert conn.base_url.startswith("https://")

    def test_stats(self):
        conn = WHOConnector()
        conn.get_indicators()
        assert conn.stats["requests"] == 1

    def test_get_data(self):
        conn = WHOConnector()
        data = conn.get_data("MALARIA_EST_CASES", "BGD")
        assert isinstance(data, list)


class TestWorldBankConnector:
    def test_init(self):
        conn = WorldBankConnector()
        assert conn.base_url.startswith("https://")

    def test_get_indicator(self):
        conn = WorldBankConnector()
        data = conn.get_indicator("NY.GDP.PCAP.PP.CD", "BGD")
        assert isinstance(data, list)

    def test_stats(self):
        conn = WorldBankConnector()
        conn.search_indicators("gdp")
        assert conn.stats["requests"] == 1


class TestERA5Connector:
    def test_init(self):
        conn = ERA5Connector()
        assert conn._request_count == 0

    def test_get_monthly(self):
        conn = ERA5Connector()
        data = conn.get_monthly("2m_temperature", 23.7, 90.4, 2020, 2024)
        assert isinstance(data, list)
        assert conn._request_count == 1


class TestNOAAConnector:
    def test_get_stations(self):
        conn = NOAAConnector()
        stations = conn.get_stations(country="BD")
        assert isinstance(stations, list)
