"""
backend/tests/test_validators.py
Unit tests for data pipeline domain validators.
"""

from datetime import datetime, timezone
import pytest

from data_pipeline.validators.weather_validator import WeatherValidator
from data_pipeline.validators.rainfall_validator import RainfallValidator
from data_pipeline.validators.satellite_validator import SatelliteValidator
from data_pipeline.validators.radar_validator import RadarValidator
from data_pipeline.validators.nwp_validator import NwpValidator


def test_weather_validator_valid():
    validator = WeatherValidator()
    rec = {
        "station_code": "STN_001",
        "observation_time": datetime.now(timezone.utc),
        "temperature_c": 25.5,
        "humidity_percent": 75.0,
        "pressure_hpa": 1013.2,
        "wind_speed_ms": 5.4,
        "wind_direction_deg": 180.0,
        "rainfall_mm": 12.0,
    }
    res = validator.validate(rec)
    assert res.is_valid is True
    assert res.quality_flag == "OK"


def test_weather_validator_out_of_range():
    validator = WeatherValidator()
    rec = {
        "station_code": "STN_001",
        "observation_time": datetime.now(timezone.utc),
        "temperature_c": 95.0,  # Invalid temp
    }
    res = validator.validate(rec)
    assert res.is_valid is False
    assert len(res.errors) >= 1


def test_rainfall_validator_negative_rain():
    validator = RainfallValidator()
    rec = {
        "observation_time": datetime.now(timezone.utc),
        "source": "STATION",
        "rainfall_mm": -5.0,
    }
    res = validator.validate(rec)
    assert res.is_valid is False
    assert any("Negative rainfall" in e.message for e in res.errors)


def test_satellite_validator_bounding_box():
    validator = SatelliteValidator()
    rec = {
        "observation_time": datetime.now(timezone.utc),
        "satellite_name": "GPM",
        "product_name": "IMERG",
        "min_lat": 20.0,
        "max_lat": 10.0,  # min > max
    }
    res = validator.validate(rec)
    assert res.is_valid is False


def test_radar_validator_reflectivity():
    validator = RadarValidator()
    rec = {
        "observation_time": datetime.now(timezone.utc),
        "radar_name": "BLR_DWR",
        "product_name": "CAPPI",
        "mean_reflectivity_dbz": 120.0,  # Physically absurd
    }
    res = validator.validate(rec)
    assert res.is_valid is False


def test_nwp_validator_lead_time():
    validator = NwpValidator()
    fc_time = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
    vl_time = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)
    rec = {
        "model_name": "ECMWF",
        "forecast_time": fc_time,
        "valid_time": vl_time,
        "lead_time_hours": 6,
        "rainfall_mm": 5.0,
    }
    res = validator.validate(rec)
    assert res.is_valid is True
