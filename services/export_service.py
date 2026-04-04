"""Data export service supporting multiple output formats."""
from __future__ import annotations
import csv
import io
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

class ExportService:
    """Exports analytical results in CSV, JSON, and GeoJSON formats."""

    def to_csv(self, records: list[dict[str, Any]], columns: list[str] | None = None) -> str:
        if not records:
            return ""
        cols = columns or list(records[0].keys())
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
        return output.getvalue()

    def to_json(self, records: list[dict[str, Any]], indent: int = 2) -> str:
        return json.dumps({"data": records, "count": len(records)}, indent=indent, default=str)

    def to_geojson(self, records: list[dict[str, Any]], lat_field: str = "lat", lon_field: str = "lon") -> str:
        features = []
        for r in records:
            lat, lon = r.get(lat_field), r.get(lon_field)
            if lat is not None and lon is not None:
                props = {k: v for k, v in r.items() if k not in (lat_field, lon_field)}
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": props,
                })
        return json.dumps({"type": "FeatureCollection", "features": features}, default=str)

    def to_parquet_schema(self, records: list[dict[str, Any]]) -> dict[str, str]:
        """Infer Parquet schema from records."""
        if not records:
            return {}
        schema = {}
        for key, value in records[0].items():
            if isinstance(value, int):
                schema[key] = "INT64"
            elif isinstance(value, float):
                schema[key] = "DOUBLE"
            elif isinstance(value, bool):
                schema[key] = "BOOLEAN"
            else:
                schema[key] = "UTF8"
        return schema
