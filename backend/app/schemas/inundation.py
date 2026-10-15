"""backend/app/schemas/inundation.py - Pydantic schemas for inundation predictions."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class InundationPredictionOut(BaseModel):
    id: UUID
    prediction_time: Optional[datetime] = None
    forecast_valid_time: Optional[datetime] = None
    flood_probability_raster_path: Optional[str] = None
    inundation_depth_raster_path: Optional[str] = None
    affected_area_km2: Optional[float] = None
    maximum_depth_m: Optional[float] = None
    mean_depth_m: Optional[float] = None
    affected_population: Optional[float] = None
    model_confidence: Optional[float] = None
    inference_status: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class InundationListResponse(BaseModel):
    status: str = "success"
    count: int
    data: list[InundationPredictionOut]
