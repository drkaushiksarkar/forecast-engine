"""Country and geographic entity schemas."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class CountrySchema:
    iso3: str
    iso2: str
    name: str
    region: str
    sub_region: str = ""
    income_group: str = ""
    population: int = 0
    area_km2: float = 0.0
    centroid: tuple[float, float] = (0.0, 0.0)
    admin_levels: int = 3
    health_system_tier: str = ""

    def __post_init__(self) -> None:
        if len(self.iso3) != 3 or not self.iso3.isalpha():
            raise ValueError(f"Invalid ISO3: {self.iso3}")
        self.iso3 = self.iso3.upper()

    def to_dict(self) -> dict[str, Any]:
        return {
            "iso3": self.iso3, "iso2": self.iso2, "name": self.name,
            "region": self.region, "sub_region": self.sub_region,
            "income_group": self.income_group, "population": self.population,
        }

@dataclass
class AdminRegion:
    id: str
    name: str
    level: int
    parent_id: str | None = None
    iso3: str = ""
    geometry_type: str = "MultiPolygon"
    centroid: tuple[float, float] = (0.0, 0.0)
    population: int = 0

REGIONS = {
    "AFR": "Sub-Saharan Africa", "SEAR": "South-East Asia",
    "EMR": "Eastern Mediterranean", "WPR": "Western Pacific",
    "AMR": "Americas", "EUR": "Europe",
}
