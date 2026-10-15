"""
backend/app/models/__init__.py
Export all SQLAlchemy models so that Base.metadata sees them all
when running Alembic migrations.
"""

from backend.app.models.weather import WeatherStation, WeatherObservation
from backend.app.models.rainfall import RainfallData
from backend.app.models.satellite import SatelliteData
from backend.app.models.radar import RadarData
from backend.app.models.nwp import NwpForecast
from backend.app.models.flood import FloodEvent, FloodPrediction
from backend.app.models.inundation import InundationPrediction
from backend.app.models.alert import Alert
from backend.app.models.pipeline import (
    PipelineRun,
    DataQualityReport,
    ModelRegistry,
    ModelMetric,
)

__all__ = [
    "WeatherStation",
    "WeatherObservation",
    "RainfallData",
    "SatelliteData",
    "RadarData",
    "NwpForecast",
    "FloodEvent",
    "FloodPrediction",
    "InundationPrediction",
    "Alert",
    "PipelineRun",
    "DataQualityReport",
    "ModelRegistry",
    "ModelMetric",
]
