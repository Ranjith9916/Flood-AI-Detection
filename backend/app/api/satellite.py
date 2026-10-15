"""backend/app/api/satellite.py - Satellite data endpoints."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.satellite import SatelliteData
from backend.app.schemas.satellite import SatelliteListResponse, SatelliteDataOut

router = APIRouter(prefix="/satellite", tags=["Satellite"])


@router.get("/", response_model=SatelliteListResponse)
def get_satellite_data(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List ingested satellite precipitation records.
    Returns metadata only; actual raster data is on disk at file_path.
    """
    query = db.query(SatelliteData).order_by(
        SatelliteData.observation_time.desc()
    )
    if start:
        query = query.filter(SatelliteData.observation_time >= start)
    if end:
        query = query.filter(SatelliteData.observation_time <= end)
    if source:
        query = query.filter(SatelliteData.source == source)

    records = query.offset(offset).limit(limit).all()
    return SatelliteListResponse(count=len(records), data=records)
