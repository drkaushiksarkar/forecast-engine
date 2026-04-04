"""Seed script to populate development database with sample data."""
from __future__ import annotations
import json
import logging

logger = logging.getLogger(__name__)

SEED_COUNTRIES = [
    ("BGD", "BD", "Bangladesh", "SEAR", "South Asia", "Lower middle income", 170000000),
    ("IND", "IN", "India", "SEAR", "South Asia", "Lower middle income", 1400000000),
    ("KEN", "KE", "Kenya", "AFR", "Eastern Africa", "Lower middle income", 54000000),
    ("NGA", "NG", "Nigeria", "AFR", "Western Africa", "Lower middle income", 220000000),
    ("BRA", "BR", "Brazil", "AMR", "South America", "Upper middle income", 215000000),
    ("ETH", "ET", "Ethiopia", "AFR", "Eastern Africa", "Low income", 120000000),
    ("TZA", "TZ", "Tanzania", "AFR", "Eastern Africa", "Low income", 62000000),
    ("IDN", "ID", "Indonesia", "SEAR", "South-Eastern Asia", "Lower middle income", 275000000),
]

SEED_INDICATORS = [
    ("MALARIA_CASES", "Confirmed malaria cases", "health", "cases", "sum"),
    ("MALARIA_DEATHS", "Malaria deaths", "health", "deaths", "sum"),
    ("MALARIA_INCIDENCE", "Malaria incidence rate", "health", "per 1000", "rate"),
    ("TEMP_MEAN", "Mean temperature", "climate", "celsius", "mean"),
    ("PRECIP_TOTAL", "Total precipitation", "climate", "mm", "sum"),
    ("GDP_PC_PPP", "GDP per capita PPP", "economics", "USD", "mean"),
    ("POPULATION", "Total population", "demographics", "persons", "sum"),
    ("LIFE_EXPECTANCY", "Life expectancy at birth", "health", "years", "mean"),
    ("INFANT_MORTALITY", "Infant mortality rate", "health", "per 1000 live births", "rate"),
    ("UNDER5_MORTALITY", "Under-5 mortality rate", "health", "per 1000 live births", "rate"),
]

def generate_seed_sql() -> str:
    lines = ["-- Auto-generated seed data", "BEGIN;", ""]
    lines.append("INSERT INTO health.countries (iso3, iso2, name, region, sub_region, income_group, population) VALUES")
    for i, (iso3, iso2, name, region, sub, income, pop) in enumerate(SEED_COUNTRIES):
        comma = "," if i < len(SEED_COUNTRIES) - 1 else ";"
        lines.append(f"  ('{iso3}', '{iso2}', '{name}', '{region}', '{sub}', '{income}', {pop}){comma}")
    lines.append("")
    lines.append("INSERT INTO health.indicators (code, name, domain, unit, aggregation) VALUES")
    for i, (code, name, domain, unit, agg) in enumerate(SEED_INDICATORS):
        comma = "," if i < len(SEED_INDICATORS) - 1 else ";"
        lines.append(f"  ('{code}', '{name}', '{domain}', '{unit}', '{agg}'){comma}")
    lines.append("")
    lines.append("COMMIT;")
    return "\n".join(lines)

if __name__ == "__main__":
    print(generate_seed_sql())
