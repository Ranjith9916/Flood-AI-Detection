"""
backend/tests/test_data_pipeline.py
Integration tests for pipeline collectors and processors.
"""

from datetime import datetime, timezone
import pytest

from data_pipeline.collectors.weather_collector import OpenMeteoWeatherProvider
from data_pipeline.collectors.satellite_collector import SatelliteDataCollector
from data_pipeline.collectors.radar_collector import RadarDataCollector, dbz_to_rainfall_rate
from data_pipeline.collectors.nwp_collector import NwpDataCollector
from data_pipeline.processors.rainfall_accumulator import RainfallAccumulator


def test_weather_provider_fetch():
    provider = OpenMeteoWeatherProvider()
    res = provider.fetch(
        station_code="TEST_BLR",
        latitude=12.9716,
        longitude=77.5946,
    )
    assert res.success is True
    assert len(res.records) > 0
    assert "station_code" in res.records[0]


def test_satellite_collector():
    collector = SatelliteDataCollector()
    res = collector.fetch(
        satellite_name="GPM",
        product_name="IMERG-Final-V07",
    )
    assert res.success is True
    assert len(res.records) > 0
    assert res.records[0]["satellite_name"] == "GPM"


def test_radar_collector_and_zr_conversion():
    rate = dbz_to_rainfall_rate(35.0)  # ~5.6 mm/h
    assert rate > 0

    collector = RadarDataCollector()
    res = collector.fetch(product_name="CAPPI_2KM")
    assert res.success is True
    assert len(res.records) > 0
    assert "mean_reflectivity_dbz" in res.records[0]


def test_nwp_collector():
    collector = NwpDataCollector()
    res = collector.fetch(latitude=12.97, longitude=77.59, forecast_days=2)
    assert res.success is True
    assert len(res.records) > 0
    assert res.records[0]["model_name"] == "ECMWF_IFS"


def test_rainfall_accumulator_classification():
    acc = RainfallAccumulator()
    assert acc._classify_rainfall(250.0) == "EXTREMELY_HEAVY"
    assert acc._classify_rainfall(120.0) == "VERY_HEAVY"
    assert acc._classify_rainfall(70.0) == "HEAVY"
    assert acc._classify_rainfall(20.0) == "MODERATE"
    assert acc._classify_rainfall(5.0) == "LIGHT"
    assert acc._classify_rainfall(0.0) == "NO_RAIN"
