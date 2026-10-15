"""
backend/app/api/weather.py
Weather station and observation endpoints.
Uses Pydantic schemas for request/response validation.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.weather import WeatherObservation, WeatherStation
from backend.app.schemas.weather import (
    WeatherObservationCreate,
    WeatherObservationListResponse,
    WeatherObservationOut,
    WeatherStationCreate,
    WeatherStationOut,
)
from backend.app.services.weather_service import (
    get_station_by_code,
    save_weather_observation,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/weather", tags=["Weather"])


# ============================================
# WEATHER STATIONS
# ============================================

@router.get("/stations", response_model=dict)
def get_weather_stations(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """List all weather stations."""
    total = db.query(WeatherStation).count()
    stations = (
        db.query(WeatherStation)
        .order_by(WeatherStation.station_code)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "status": "success",
        "count": len(stations),
        "total": total,
        "data": [
            {
                "id": str(s.id),
                "station_code": s.station_code,
                "station_name": s.station_name,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "elevation_m": s.elevation_m,
                "source": s.source,
            }
            for s in stations
        ],
    }


@router.post("/stations", status_code=201)
def create_weather_station(
    data: WeatherStationCreate,
    db: Session = Depends(get_db),
):
    """Register a new weather station."""
    existing = get_station_by_code(db, data.station_code)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Station '{data.station_code}' already exists",
        )
    station = WeatherStation(
        station_code=data.station_code,
        station_name=data.station_name,
        latitude=data.latitude,
        longitude=data.longitude,
        elevation_m=data.elevation_m,
        source=data.source,
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    logger.info("Created weather station: %s", data.station_code)
    return {"status": "success", "id": str(station.id), "station_code": station.station_code}


# ============================================
# WEATHER OBSERVATIONS
# ============================================

@router.get("/observations", response_model=WeatherObservationListResponse)
def get_weather_observations(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    station_code: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """List weather observations with optional station and time filters."""
    query = db.query(WeatherObservation)

    if station_code:
        station = get_station_by_code(db, station_code)
        if station:
            query = query.filter(
                WeatherObservation.station_id == station.id
            )
        else:
            return WeatherObservationListResponse(count=0, data=[])

    if start:
        query = query.filter(WeatherObservation.observation_time >= start)
    if end:
        query = query.filter(WeatherObservation.observation_time <= end)

    total = query.count()
    records = (
        query.order_by(WeatherObservation.observation_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return WeatherObservationListResponse(
        count=len(records),
        total=total,
        data=records,
    )


@router.post("/observations", status_code=201)
def create_weather_observation(
    data: WeatherObservationCreate,
    db: Session = Depends(get_db),
):
    """Save a new weather observation for a registered station."""
    try:
        observation = save_weather_observation(
            db=db,
            station_code=data.station_code,
            observation_time=data.observation_time,
            temperature_c=data.temperature_c,
            humidity_percent=data.humidity_percent,
            pressure_hpa=data.pressure_hpa,
            wind_speed_ms=data.wind_speed_ms,
            wind_direction_deg=data.wind_direction_deg,
            rainfall_mm=data.rainfall_mm,
        )
        logger.info(
            "Saved weather observation for station %s at %s",
            data.station_code,
            data.observation_time,
        )
        return {
            "status": "success",
            "message": "Weather observation saved",
            "id": str(observation.id),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
