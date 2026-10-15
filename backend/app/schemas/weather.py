"""
backend/app/schemas/weather.py
Pydantic schemas for weather stations and observations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WeatherStationBase(BaseModel):
    station_code: str
    station_name: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    elevation_m: Optional[float] = None
    source: Optional[str] = None


class WeatherStationCreate(WeatherStationBase):
    pass


class WeatherStationOut(WeatherStationBase):
    id: UUID
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WeatherObservationBase(BaseModel):
    observation_time: datetime
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = Field(default=None, ge=0, le=100)
    pressure_hpa: Optional[float] = None
    wind_speed_ms: Optional[float] = Field(default=None, ge=0)
    wind_direction_deg: Optional[float] = Field(default=None, ge=0, le=360)
    rainfall_mm: Optional[float] = Field(default=None, ge=0)


class WeatherObservationCreate(WeatherObservationBase):
    station_code: str


class WeatherObservationOut(WeatherObservationBase):
    id: UUID
    station_id: UUID
    quality_flag: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WeatherObservationListResponse(BaseModel):
    status: str = "success"
    count: int
    total: Optional[int] = None
    data: list[WeatherObservationOut]
