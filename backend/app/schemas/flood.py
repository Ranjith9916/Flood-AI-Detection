"""backend/app/schemas/flood.py - Pydantic schemas for flood predictions."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class FloodPredictionOut(BaseModel):
    id: UUID
    prediction_time: Optional[datetime] = None
    forecast_valid_time: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    flood_probability: Optional[float] = Field(default=None, ge=0, le=1)
    risk_level: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    feature_version: Optional[str] = None
    data_sources: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class FloodPredictionListResponse(BaseModel):
    status: str = "success"
    count: int
    data: list[FloodPredictionOut]
