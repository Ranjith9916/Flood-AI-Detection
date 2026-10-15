"""
backend/app/schemas/rainfall.py
Pydantic schemas for rainfall observations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RainfallBase(BaseModel):
    observation_time: datetime
    source: str
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    rainfall_mm: float = Field(..., ge=0)
    duration_minutes: Optional[int] = Field(default=None, ge=1)
    station_code: Optional[str] = None


class RainfallCreate(RainfallBase):
    pass


class RainfallOut(RainfallBase):
    id: UUID
    quality_flag: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RainfallListResponse(BaseModel):
    status: str = "success"
    count: int
    total: Optional[int] = None
    data: list[RainfallOut]


class RainfallAccumulation(BaseModel):
    """Rainfall accumulation summary for a location over multiple periods."""
    latitude: float
    longitude: float
    station_code: Optional[str] = None
    period_end: datetime
    rainfall_1h_mm: Optional[float] = None
    rainfall_3h_mm: Optional[float] = None
    rainfall_6h_mm: Optional[float] = None
    rainfall_12h_mm: Optional[float] = None
    rainfall_24h_mm: Optional[float] = None
    rainfall_48h_mm: Optional[float] = None
    rainfall_72h_mm: Optional[float] = None
