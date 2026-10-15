"""backend/app/api/radar.py - Radar data endpoints."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.radar import RadarData
from backend.app.schemas.radar import RadarListResponse

router = APIRouter(prefix="/radar", tags=["Radar"])


@router.get("/", response_model=RadarListResponse)
def get_radar_data(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    radar_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List ingested radar scan metadata."""
    query = db.query(RadarData).order_by(RadarData.observation_time.desc())
    if start:
        query = query.filter(RadarData.observation_time >= start)
    if end:
        query = query.filter(RadarData.observation_time <= end)
    if radar_name:
        query = query.filter(RadarData.radar_name == radar_name)

    records = query.offset(offset).limit(limit).all()
    return RadarListResponse(count=len(records), data=records)
