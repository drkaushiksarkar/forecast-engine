-- Health Intelligence Platform Schema
-- Initial migration

CREATE SCHEMA IF NOT EXISTS health;

CREATE TABLE health.countries (
    iso3 CHAR(3) PRIMARY KEY,
    iso2 CHAR(2) NOT NULL,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(50),
    sub_region VARCHAR(100),
    income_group VARCHAR(50),
    population BIGINT,
    area_km2 DOUBLE PRECISION,
    centroid_lat DOUBLE PRECISION,
    centroid_lon DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE health.indicators (
    indicator_id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    unit VARCHAR(100),
    aggregation VARCHAR(50) DEFAULT 'mean',
    description TEXT,
    source VARCHAR(255),
    frequency VARCHAR(20) DEFAULT 'annual',
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE health.observations (
    observation_id BIGSERIAL PRIMARY KEY,
    iso3 CHAR(3) NOT NULL REFERENCES health.countries(iso3),
    indicator_id INTEGER NOT NULL REFERENCES health.indicators(indicator_id),
    year INTEGER NOT NULL,
    month SMALLINT,
    value DOUBLE PRECISION NOT NULL,
    quality_flag CHAR(1) DEFAULT 'A',
    source VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(iso3, indicator_id, year, month)
);

CREATE TABLE health.forecasts (
    forecast_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iso3 CHAR(3) NOT NULL REFERENCES health.countries(iso3),
    indicator_id INTEGER NOT NULL REFERENCES health.indicators(indicator_id),
    model_id VARCHAR(100) NOT NULL,
    horizon INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE health.forecast_points (
    point_id BIGSERIAL PRIMARY KEY,
    forecast_id UUID NOT NULL REFERENCES health.forecasts(forecast_id),
    target_date DATE NOT NULL,
    predicted DOUBLE PRECISION NOT NULL,
    lower_ci DOUBLE PRECISION,
    upper_ci DOUBLE PRECISION,
    confidence DOUBLE PRECISION DEFAULT 0.95
);

CREATE TABLE health.alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    iso3 CHAR(3) REFERENCES health.countries(iso3),
    indicator_id INTEGER REFERENCES health.indicators(indicator_id),
    value DOUBLE PRECISION,
    threshold DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    resolution TEXT
);

-- Indexes for query performance
CREATE INDEX idx_observations_iso3_indicator ON health.observations(iso3, indicator_id);
CREATE INDEX idx_observations_year ON health.observations(year);
CREATE INDEX idx_forecasts_iso3 ON health.forecasts(iso3);
CREATE INDEX idx_alerts_severity ON health.alerts(severity) WHERE resolved_at IS NULL;
CREATE INDEX idx_alerts_active ON health.alerts(created_at) WHERE resolved_at IS NULL;

-- Audit trigger
CREATE OR REPLACE FUNCTION health.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER countries_updated
    BEFORE UPDATE ON health.countries
    FOR EACH ROW EXECUTE FUNCTION health.update_timestamp();
