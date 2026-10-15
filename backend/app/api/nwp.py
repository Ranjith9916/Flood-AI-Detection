"""backend/app/api/nwp.py - NWP forecast endpoints."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.nwp import NwpForecast
from backend.app.schemas.nwp import NwpListResponse

router = APIRouter(prefix="/nwp", tags=["NWP"])


@router.get("/", response_model=NwpListResponse)
def get_nwp_forecasts(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    model_name: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """List NWP forecast records. Filter by model_name and valid_time range."""
    query = db.query(NwpForecast).order_by(NwpForecast.valid_time.desc())
    if model_name:
        query = query.filter(NwpForecast.model_name == model_name)
    if start:
        query = query.filter(NwpForecast.valid_time >= start)
    if end:
        query = query.filter(NwpForecast.valid_time <= end)

    records = query.offset(offset).limit(limit).all()
    return NwpListResponse(count=len(records), data=records)
