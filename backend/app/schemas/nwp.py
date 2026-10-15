"""backend/app/schemas/nwp.py - Pydantic schemas for NWP forecast data."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class NwpForecastOut(BaseModel):
    id: UUID
    model_name: str
    forecast_time: datetime
    valid_time: datetime
    lead_time_hours: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rainfall_mm: Optional[float] = None
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    pressure_hpa: Optional[float] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class NwpListResponse(BaseModel):
    status: str = "success"
    count: int
    data: list[NwpForecastOut]
