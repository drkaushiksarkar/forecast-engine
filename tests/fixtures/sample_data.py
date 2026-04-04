"""Sample data fixtures for testing."""
from datetime import date

SAMPLE_COUNTRIES = [
    {"iso3": "BGD", "name": "Bangladesh", "region": "SEAR", "population": 170000000},
    {"iso3": "IND", "name": "India", "region": "SEAR", "population": 1400000000},
    {"iso3": "KEN", "name": "Kenya", "region": "AFR", "population": 54000000},
    {"iso3": "NGA", "name": "Nigeria", "region": "AFR", "population": 220000000},
    {"iso3": "BRA", "name": "Brazil", "region": "AMR", "population": 215000000},
]

SAMPLE_INDICATORS = [
    {"iso3": "BGD", "year": 2020, "indicator": "MALARIA_CASES", "value": 15234},
    {"iso3": "BGD", "year": 2021, "indicator": "MALARIA_CASES", "value": 12890},
    {"iso3": "BGD", "year": 2022, "indicator": "MALARIA_CASES", "value": 11456},
    {"iso3": "BGD", "year": 2023, "indicator": "MALARIA_CASES", "value": 10234},
    {"iso3": "BGD", "year": 2024, "indicator": "MALARIA_CASES", "value": 9120},
    {"iso3": "KEN", "year": 2020, "indicator": "MALARIA_CASES", "value": 3500000},
    {"iso3": "KEN", "year": 2021, "indicator": "MALARIA_CASES", "value": 3200000},
    {"iso3": "KEN", "year": 2022, "indicator": "MALARIA_CASES", "value": 3100000},
    {"iso3": "KEN", "year": 2023, "indicator": "MALARIA_CASES", "value": 2900000},
]

SAMPLE_CLIMATE = [
    {"iso3": "BGD", "year": 2024, "month": 1, "temp_mean": 18.5, "precip_mm": 12.0},
    {"iso3": "BGD", "year": 2024, "month": 2, "temp_mean": 22.1, "precip_mm": 25.0},
    {"iso3": "BGD", "year": 2024, "month": 3, "temp_mean": 27.3, "precip_mm": 45.0},
    {"iso3": "BGD", "year": 2024, "month": 4, "temp_mean": 30.1, "precip_mm": 120.0},
    {"iso3": "BGD", "year": 2024, "month": 5, "temp_mean": 30.5, "precip_mm": 280.0},
    {"iso3": "BGD", "year": 2024, "month": 6, "temp_mean": 29.8, "precip_mm": 350.0},
]

SAMPLE_TIMESERIES = [
    {"date": "2024-01-01", "value": 100, "quality": "A"},
    {"date": "2024-02-01", "value": 120, "quality": "A"},
    {"date": "2024-03-01", "value": 150, "quality": "A"},
    {"date": "2024-04-01", "value": 200, "quality": "A"},
    {"date": "2024-05-01", "value": 350, "quality": "A"},
    {"date": "2024-06-01", "value": 500, "quality": "A"},
    {"date": "2024-07-01", "value": 450, "quality": "A"},
    {"date": "2024-08-01", "value": 380, "quality": "A"},
    {"date": "2024-09-01", "value": 250, "quality": "A"},
    {"date": "2024-10-01", "value": 180, "quality": "A"},
    {"date": "2024-11-01", "value": 130, "quality": "A"},
    {"date": "2024-12-01", "value": 110, "quality": "A"},
]
