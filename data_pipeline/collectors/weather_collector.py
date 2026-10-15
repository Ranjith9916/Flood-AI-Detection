"""
data_pipeline/collectors/weather_collector.py
Open-Meteo weather data provider implementation.
Fetches real hourly weather observations for a station location.
No mock data — all values come directly from Open-Meteo API.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import requests

from data_pipeline.providers.base import ProviderResult, WeatherProvider

logger = logging.getLogger(__name__)

# Open-Meteo variables to fetch
_HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
]


class OpenMeteoWeatherProvider(WeatherProvider):
    """
    Fetches hourly weather observations from the Open-Meteo API.
    Free, no authentication required. Returns global coverage.

    Docs: https://open-meteo.com/en/docs
    """

    SOURCE_NAME = "OPEN_METEO"

    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1",
        timeout_s: int = 30,
        study_area_bbox: Optional[dict] = None,
    ):
        super().__init__(study_area_bbox=study_area_bbox)
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def fetch(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        station_code: str = "DEFAULT",
        latitude: float = 12.97,
        longitude: float = 77.59,
        **kwargs,
    ) -> ProviderResult:
        """
        Fetch hourly weather for a single station location.

        Args:
            station_code: Station identifier for record tagging.
            latitude:     Station latitude.
            longitude:    Station longitude.
            start:        Start date (uses last 24h if not given).
            end:          End date.
        """
        fetch_start = datetime.now(timezone.utc)

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(_HOURLY_VARS),
            "timezone": "UTC",
            "wind_speed_unit": "ms",    # Request m/s directly
        }

        if start:
            params["start_date"] = start.strftime("%Y-%m-%d")
        if end:
            params["end_date"] = end.strftime("%Y-%m-%d")

        try:
            url = f"{self.base_url}/forecast"
            response = requests.get(url, params=params, timeout=self.timeout_s)
            response.raise_for_status()
            raw = response.json()
        except requests.exceptions.Timeout:
            return ProviderResult(
                success=False,
                source=self.SOURCE_NAME,
                records=[],
                error_message=f"Request timed out after {self.timeout_s}s",
                fetch_start=fetch_start,
                fetch_end=datetime.now(timezone.utc),
            )
        except requests.exceptions.RequestException as exc:
            return ProviderResult(
                success=False,
                source=self.SOURCE_NAME,
                records=[],
                error_message=str(exc),
                fetch_start=fetch_start,
                fetch_end=datetime.now(timezone.utc),
            )

        records = _normalise(raw, station_code, latitude, longitude)
        fetch_end = datetime.now(timezone.utc)

        logger.info(
            "OpenMeteo: fetched %d hourly records for station %s (%.4f, %.4f)",
            len(records), station_code, latitude, longitude,
        )

        return ProviderResult(
            success=True,
            source=self.SOURCE_NAME,
            records=records,
            records_fetched=len(records),
            fetch_start=fetch_start,
            fetch_end=fetch_end,
            metadata={
                "station_code": station_code,
                "latitude": latitude,
                "longitude": longitude,
                "api_url": url,
            },
        )

    def is_available(self) -> bool:
        """Ping Open-Meteo with a minimal request."""
        try:
            r = requests.get(
                f"{self.base_url}/forecast",
                params={"latitude": 0, "longitude": 0, "hourly": "temperature_2m"},
                timeout=5,
            )
            return r.status_code == 200
        except Exception:
            return False


# ---- Legacy function API (used by run_pipeline.py) ----

def fetch_weather(
    latitude: float,
    longitude: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Legacy wrapper — prefer OpenMeteoWeatherProvider.fetch() directly."""
    provider = OpenMeteoWeatherProvider()
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    result = provider.fetch(
        start=start,
        end=end,
        latitude=latitude,
        longitude=longitude,
    )
    return result.records


def normalize_weather_data(
    station_code: str,
    latitude: float,
    longitude: float,
    weather_data: dict,
) -> list[dict]:
    """Legacy wrapper around _normalise."""
    return _normalise(weather_data, station_code, latitude, longitude)


def collect_station_weather(
    station_code: str,
    latitude: float,
    longitude: float,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> ProviderResult:
    """
    Fetch weather for a single station. Used by weather_processor.py.
    """
    provider = OpenMeteoWeatherProvider()
    return provider.fetch(
        station_code=station_code,
        latitude=latitude,
        longitude=longitude,
        start=start,
        end=end,
    )


# ---- Normalisation ----

def _normalise(
    raw: dict,
    station_code: str,
    latitude: float,
    longitude: float,
) -> list[dict]:
    """
    Convert Open-Meteo API response into internal record dicts.
    Wind speed is already in m/s (requested via wind_speed_unit=ms).
    All timestamps are UTC.
    """
    hourly = raw.get("hourly", {})
    times = hourly.get("time", [])

    temperatures   = hourly.get("temperature_2m", [])
    humidity       = hourly.get("relative_humidity_2m", [])
    pressure       = hourly.get("surface_pressure", [])
    wind_speed     = hourly.get("wind_speed_10m", [])
    wind_dir       = hourly.get("wind_direction_10m", [])
    precipitation  = hourly.get("precipitation", [])

    records = []
    for i, ts in enumerate(times):
        obs_time = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
        rain = _get(precipitation, i)
        records.append({
            "station_code": station_code,
            "latitude": latitude,
            "longitude": longitude,
            "observation_time": obs_time,
            "temperature_c": _get(temperatures, i),
            "humidity_percent": _get(humidity, i),
            "pressure_hpa": _get(pressure, i),
            "wind_speed_ms": _get(wind_speed, i),
            "wind_direction_deg": _get(wind_dir, i),
            "rainfall_mm": max(rain, 0.0) if rain is not None else None,
            "source": "OPEN_METEO",
        })
    return records


def _get(lst: list, idx: int):
    return lst[idx] if idx < len(lst) else None
