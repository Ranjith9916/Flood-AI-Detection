"""backend/app/schemas/satellite.py - Pydantic schemas for satellite data."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class SatelliteDataOut(BaseModel):
    id: UUID
    observation_time: datetime
    satellite_name: Optional[str] = None
    product_name: Optional[str] = None
    file_path: Optional[str] = None
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lon: Optional[float] = None
    max_lon: Optional[float] = None
    mean_precipitation_mm: Optional[float] = None
    max_precipitation_mm: Optional[float] = None
    data_coverage_pct: Optional[float] = None
    source: Optional[str] = None
    is_development_data: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class SatelliteListResponse(BaseModel):
    status: str = "success"
    count: int
    data: list[SatelliteDataOut]
