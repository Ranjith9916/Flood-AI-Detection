"""
backend/app/api/rainfall.py
Rainfall observation endpoints.
Supports station, satellite, radar, and NWP rainfall sources.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.rainfall import RainfallData
from backend.app.schemas.rainfall import (
    RainfallCreate,
    RainfallListResponse,
)
from backend.app.services.rainfall_service import save_rainfall

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rainfall", tags=["Rainfall"])


@router.get("/", response_model=RainfallListResponse)
def get_rainfall(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    source: Optional[str] = None,
    station_code: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """List rainfall observations with optional source and time filters."""
    query = db.query(RainfallData)
    if source:
        query = query.filter(RainfallData.source == source)
    if station_code:
        query = query.filter(RainfallData.station_code == station_code)
    if start:
        query = query.filter(RainfallData.observation_time >= start)
    if end:
        query = query.filter(RainfallData.observation_time <= end)

    total = query.count()
    records = (
        query.order_by(RainfallData.observation_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return RainfallListResponse(count=len(records), total=total, data=records)


@router.post("/", status_code=201)
def create_rainfall(
    data: RainfallCreate,
    db: Session = Depends(get_db),
):
    """Save a new rainfall observation."""
    try:
        rainfall = save_rainfall(
            db=db,
            observation_time=data.observation_time,
            source=data.source,
            rainfall_mm=data.rainfall_mm,
            latitude=data.latitude,
            longitude=data.longitude,
            duration_minutes=data.duration_minutes,
            station_code=data.station_code,
        )
        logger.info(
            "Saved rainfall: %.1f mm from %s at %s",
            data.rainfall_mm,
            data.source,
            data.observation_time,
        )
        return {
            "status": "success",
            "message": "Rainfall data saved",
            "id": str(rainfall.id),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
