"""backend/app/schemas/alert.py - Pydantic schemas for alerts."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class AlertOut(BaseModel):
    id: UUID
    alert_time: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    alert_type: Optional[str] = None
    severity: str
    status: str
    title: str
    message: Optional[str] = None
    recommended_action: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    affected_area_km2: Optional[float] = None
    trigger_rainfall_mm: Optional[float] = None
    trigger_flood_probability: Optional[float] = None
    trigger_heavy_rain_probability: Optional[float] = None
    expected_inundation_area_km2: Optional[float] = None
    expected_max_depth_m: Optional[float] = None
    model_confidence: Optional[float] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class AlertAcknowledgeRequest(BaseModel):
    acknowledged_by: Optional[str] = None
    notes: Optional[str] = None

class AlertListResponse(BaseModel):
    status: str = "success"
    count: int
    data: list[AlertOut]
