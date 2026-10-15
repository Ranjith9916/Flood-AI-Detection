"""backend/app/schemas/system.py - Pydantic schemas for system health and status."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ComponentHealth(BaseModel):
    name: str
    status: str          # "healthy", "degraded", "unavailable", "unknown"
    message: Optional[str] = None
    latency_ms: Optional[float] = None

class SystemStatus(BaseModel):
    status: str          # "healthy", "degraded", "unhealthy"
    environment: str
    version: str
    timestamp: datetime
    components: list[ComponentHealth]
    data_sources: Optional[list[ComponentHealth]] = None
    ml_models: Optional[list[ComponentHealth]] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
