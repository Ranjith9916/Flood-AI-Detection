"""backend/app/schemas/radar.py - Pydantic schemas for radar data."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class RadarDataOut(BaseModel):
    id: UUID
    observation_time: datetime
    radar_name: Optional[str] = None
    product_name: Optional[str] = None
    file_path: Optional[str] = None
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lon: Optional[float] = None
    max_lon: Optional[float] = None
    mean_reflectivity_dbz: Optional[float] = None
    max_reflectivity_dbz: Optional[float] = None
    mean_rainfall_rate_mmh: Optional[float] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class RadarListResponse(BaseModel):
    status: str = "success"
    count: int
    data: list[RadarDataOut]
