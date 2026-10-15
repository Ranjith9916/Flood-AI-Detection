"""
data_pipeline/providers/base.py
Abstract base class for all data source providers.
Every data source (weather, satellite, NWP, radar) implements this interface.
Follows the Strategy pattern — swap providers without changing the pipeline.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProviderResult:
    """
    Standardised result from any provider fetch.
    Always check success before accessing records.
    """
    success: bool
    source: str                             # Provider name e.g. "OPEN_METEO"
    records: list[dict[str, Any]]           # Normalised records ready for DB
    records_fetched: int = 0
    records_valid: int = 0
    records_rejected: int = 0
    error_message: Optional[str] = None
    fetch_start: Optional[datetime] = None
    fetch_end: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_s(self) -> Optional[float]:
        if self.fetch_start and self.fetch_end:
            return (self.fetch_end - self.fetch_start).total_seconds()
        return None


class DataProvider(ABC):
    """
    Abstract base class for a data source provider.
    Subclasses implement fetch() to return a ProviderResult.
    """

    SOURCE_NAME: str = "UNKNOWN"     # Override in every subclass

    def __init__(self, study_area_bbox: Optional[dict] = None):
        """
        Args:
            study_area_bbox: dict with lon_min, lat_min, lon_max, lat_max.
                             None means global / provider-default area.
        """
        self.study_area_bbox = study_area_bbox
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def fetch(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        **kwargs,
    ) -> ProviderResult:
        """
        Fetch data for the given time window.

        Args:
            start: Start of the time window (inclusive).
            end:   End of the time window (inclusive).
            **kwargs: Provider-specific parameters.

        Returns:
            ProviderResult with success flag and records list.
            Records are normalised dicts matching the DB model fields.
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """
        Return True if the provider can be reached (auth, network).
        Used by /system/status to report data source health.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source={self.SOURCE_NAME!r})"


class WeatherProvider(DataProvider):
    """
    Base class for weather observation providers.
    Records must include: station_code, observation_time, temperature_c,
    humidity_percent, pressure_hpa, wind_speed_ms, wind_direction_deg,
    rainfall_mm.
    """
    pass


class RainfallProvider(DataProvider):
    """
    Base class for rainfall data providers.
    Records must include: observation_time, source, rainfall_mm,
    latitude, longitude, duration_minutes.
    """
    pass


class SatelliteProvider(DataProvider):
    """
    Base class for satellite precipitation providers.
    Records are metadata dicts (actual rasters stored on disk).
    Must include: observation_time, satellite_name, product_name,
    file_path, mean_precipitation_mm, max_precipitation_mm.
    """
    pass


class NwpProvider(DataProvider):
    """
    Base class for Numerical Weather Prediction providers.
    Records must include: model_name, forecast_time, valid_time,
    lead_time_hours, latitude, longitude, rainfall_mm.
    """
    pass


class RadarProvider(DataProvider):
    """
    Base class for weather radar providers.
    Records are metadata dicts (actual scans stored on disk).
    Must include: observation_time, radar_name, product_name,
    file_path, mean_rainfall_rate_mmh.
    """
    pass
