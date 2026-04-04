"""Common data transformation functions for ETL pipelines."""
from __future__ import annotations
import re
from typing import Any

def normalize_iso3(records: list[dict[str, Any]], field: str = "iso3") -> list[dict[str, Any]]:
    for r in records:
        if field in r and isinstance(r[field], str):
            r[field] = r[field].upper().strip()
    return records

def filter_nulls(records: list[dict[str, Any]], required_fields: list[str]) -> list[dict[str, Any]]:
    return [r for r in records if all(r.get(f) is not None for f in required_fields)]

def cast_numeric(records: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    for r in records:
        for f in fields:
            if f in r:
                try:
                    r[f] = float(r[f])
                except (ValueError, TypeError):
                    r[f] = None
    return records

def deduplicate(records: list[dict[str, Any]], key_fields: list[str]) -> list[dict[str, Any]]:
    seen: set[tuple] = set()
    unique = []
    for r in records:
        key = tuple(r.get(f) for f in key_fields)
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

def rename_fields(records: list[dict[str, Any]], mapping: dict[str, str]) -> list[dict[str, Any]]:
    return [{mapping.get(k, k): v for k, v in r.items()} for r in records]

def add_computed_field(records: list[dict[str, Any]], field_name: str, compute_fn: Any) -> list[dict[str, Any]]:
    for r in records:
        r[field_name] = compute_fn(r)
    return records

def clip_values(records: list[dict[str, Any]], field: str, min_val: float | None = None, max_val: float | None = None) -> list[dict[str, Any]]:
    for r in records:
        if field in r and isinstance(r[field], (int, float)):
            if min_val is not None:
                r[field] = max(r[field], min_val)
            if max_val is not None:
                r[field] = min(r[field], max_val)
    return records

def sanitize_strings(records: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    html_re = re.compile(r"<[^>]+>")
    for r in records:
        for f in fields:
            if f in r and isinstance(r[f], str):
                r[f] = html_re.sub("", r[f]).strip()
    return records
