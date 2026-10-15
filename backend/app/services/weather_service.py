from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.weather import (
    WeatherStation,
    WeatherObservation,
)


# ============================================
# FIND WEATHER STATION
# ============================================

def get_station_by_code(
    db: Session,
    station_code: str,
):

    return (
        db.query(WeatherStation)
        .filter(
            WeatherStation.station_code
            == station_code
        )
        .first()
    )


# ============================================
# SAVE WEATHER OBSERVATION
# ============================================

def save_weather_observation(
    db: Session,
    station_code: str,
    observation_time: datetime,
    temperature_c: float | None = None,
    humidity_percent: float | None = None,
    pressure_hpa: float | None = None,
    wind_speed_ms: float | None = None,
    wind_direction_deg: float | None = None,
    rainfall_mm: float | None = None,
):

    station = get_station_by_code(
        db,
        station_code,
    )

    if station is None:

        raise ValueError(
            f"Weather station "
            f"'{station_code}' not found"
        )

    observation = WeatherObservation(

        station_id=station.id,

        observation_time=observation_time,

        temperature_c=temperature_c,

        humidity_percent=humidity_percent,

        pressure_hpa=pressure_hpa,

        wind_speed_ms=wind_speed_ms,

        wind_direction_deg=wind_direction_deg,

        rainfall_mm=rainfall_mm,
    )

    db.add(observation)

    db.commit()

    db.refresh(observation)

    return observation