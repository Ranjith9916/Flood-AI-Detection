"""
data_pipeline/processors/__init__.py
Exports all pipeline processors and accumulation engine.
"""

from data_pipeline.processors.weather_processor import (
    WeatherProcessor,
    DEFAULT_STATIONS,
)
from data_pipeline.processors.satellite_processor import SatelliteProcessor
from data_pipeline.processors.radar_processor import RadarProcessor
from data_pipeline.processors.nwp_processor import NwpProcessor, DEFAULT_NWP_POINTS
from data_pipeline.processors.rainfall_accumulator import (
    RainfallAccumulator,
    RAIN_CATEGORIES,
    ACCUMULATION_WINDOWS,
)

__all__ = [
    "WeatherProcessor",
    "DEFAULT_STATIONS",
    "SatelliteProcessor",
    "RadarProcessor",
    "NwpProcessor",
    "DEFAULT_NWP_POINTS",
    "RainfallAccumulator",
    "RAIN_CATEGORIES",
    "ACCUMULATION_WINDOWS",
]
