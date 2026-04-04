"""Tests for export service."""
import json
import pytest
from services.export_service import ExportService


class TestExportService:
    def setup_method(self):
        self.service = ExportService()
        self.records = [
            {"iso3": "BGD", "year": 2024, "value": 100.5, "lat": 23.6, "lon": 90.3},
            {"iso3": "IND", "year": 2024, "value": 200.3, "lat": 28.6, "lon": 77.2},
        ]

    def test_to_csv(self):
        csv_out = self.service.to_csv(self.records)
        assert "iso3" in csv_out
        assert "BGD" in csv_out
        lines = csv_out.strip().split("\n")
        assert len(lines) == 3

    def test_to_csv_with_columns(self):
        csv_out = self.service.to_csv(self.records, columns=["iso3", "value"])
        assert "year" not in csv_out.split("\n")[0]

    def test_to_csv_empty(self):
        assert self.service.to_csv([]) == ""

    def test_to_json(self):
        json_out = self.service.to_json(self.records)
        parsed = json.loads(json_out)
        assert parsed["count"] == 2
        assert len(parsed["data"]) == 2

    def test_to_geojson(self):
        geojson = self.service.to_geojson(self.records)
        parsed = json.loads(geojson)
        assert parsed["type"] == "FeatureCollection"
        assert len(parsed["features"]) == 2
        assert parsed["features"][0]["geometry"]["type"] == "Point"

    def test_parquet_schema(self):
        schema = self.service.to_parquet_schema(self.records)
        assert schema["iso3"] == "UTF8"
        assert schema["year"] == "INT64"
        assert schema["value"] == "DOUBLE"
