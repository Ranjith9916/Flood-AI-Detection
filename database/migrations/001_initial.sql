-- ============================================
-- FLOOD AI SYSTEM - INITIAL DATABASE SCHEMA
-- ============================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================
-- 1. WEATHER STATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS weather_stations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    station_code VARCHAR(100) UNIQUE NOT NULL,
    station_name VARCHAR(255),

    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,

    location GEOGRAPHY(POINT, 4326),

    elevation_m DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_stations_location
ON weather_stations
USING GIST(location);


-- ============================================
-- 2. WEATHER OBSERVATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS weather_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    station_id UUID NOT NULL
        REFERENCES weather_stations(id),

    observation_time TIMESTAMPTZ NOT NULL,

    temperature_c DOUBLE PRECISION,
    humidity_percent DOUBLE PRECISION,
    pressure_hpa DOUBLE PRECISION,

    wind_speed_ms DOUBLE PRECISION,
    wind_direction_deg DOUBLE PRECISION,

    rainfall_mm DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_observations_time
ON weather_observations(observation_time);

CREATE INDEX IF NOT EXISTS idx_weather_observations_station_time
ON weather_observations(station_id, observation_time);


-- ============================================
-- 3. RAINFALL DATA
-- ============================================

CREATE TABLE IF NOT EXISTS rainfall_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    observation_time TIMESTAMPTZ NOT NULL,

    source VARCHAR(50) NOT NULL,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    rainfall_mm DOUBLE PRECISION NOT NULL,

    duration_minutes INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rainfall_time
ON rainfall_data(observation_time);


-- ============================================
-- 4. SATELLITE DATA
-- ============================================

CREATE TABLE IF NOT EXISTS satellite_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    observation_time TIMESTAMPTZ NOT NULL,

    satellite_name VARCHAR(100),
    product_name VARCHAR(255),

    file_path TEXT,

    min_lat DOUBLE PRECISION,
    max_lat DOUBLE PRECISION,
    min_lon DOUBLE PRECISION,
    max_lon DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_satellite_time
ON satellite_data(observation_time);


-- ============================================
-- 5. RADAR DATA
-- ============================================

CREATE TABLE IF NOT EXISTS radar_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    observation_time TIMESTAMPTZ NOT NULL,

    radar_name VARCHAR(100),
    product_name VARCHAR(255),

    file_path TEXT,

    min_lat DOUBLE PRECISION,
    max_lat DOUBLE PRECISION,
    min_lon DOUBLE PRECISION,
    max_lon DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_radar_time
ON radar_data(observation_time);


-- ============================================
-- 6. NWP FORECAST DATA
-- ============================================

CREATE TABLE IF NOT EXISTS nwp_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    model_name VARCHAR(100) NOT NULL,

    forecast_time TIMESTAMPTZ NOT NULL,
    valid_time TIMESTAMPTZ NOT NULL,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    rainfall_mm DOUBLE PRECISION,

    temperature_c DOUBLE PRECISION,
    humidity_percent DOUBLE PRECISION,

    wind_speed_ms DOUBLE PRECISION,
    pressure_hpa DOUBLE PRECISION,

    file_path TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nwp_valid_time
ON nwp_forecasts(valid_time);


-- ============================================
-- 7. FLOOD PREDICTIONS
-- ============================================

CREATE TABLE IF NOT EXISTS flood_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    prediction_time TIMESTAMPTZ DEFAULT NOW(),

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    flood_probability DOUBLE PRECISION
        CHECK (flood_probability >= 0
        AND flood_probability <= 1),

    risk_level VARCHAR(50),

    model_name VARCHAR(100),
    model_version VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_flood_prediction_time
ON flood_predictions(prediction_time);


-- ============================================
-- 8. INUNDATION PREDICTIONS
-- ============================================

CREATE TABLE IF NOT EXISTS inundation_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    prediction_time TIMESTAMPTZ DEFAULT NOW(),

    forecast_time TIMESTAMPTZ,

    file_path TEXT,

    affected_area_km2 DOUBLE PRECISION,

    maximum_depth_m DOUBLE PRECISION,

    model_name VARCHAR(100),
    model_version VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inundation_prediction_time
ON inundation_predictions(prediction_time);


-- ============================================
-- 9. ALERTS
-- ============================================

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    alert_time TIMESTAMPTZ DEFAULT NOW(),

    alert_type VARCHAR(100),

    severity VARCHAR(50),

    title VARCHAR(255),

    message TEXT,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    affected_area_km2 DOUBLE PRECISION,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_time
ON alerts(alert_time);

CREATE INDEX IF NOT EXISTS idx_alerts_active
ON alerts(is_active);


-- ============================================
-- SCHEMA COMPLETE
-- ============================================

SELECT 'Flood AI database schema created successfully'
AS status;