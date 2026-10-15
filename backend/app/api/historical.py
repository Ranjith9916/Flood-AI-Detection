"""
backend/app/api/historical.py
Historical extreme flood events and executive incident reporting.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.flood import FloodEvent
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/historical", tags=["Historical & Reports"])


@router.get("/events", status_code=status.HTTP_200_OK)
def get_historical_events(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns archive of past major flood disaster events with impact metrics.
    """
    records = db.query(FloodEvent).order_by(FloodEvent.start_time.desc()).limit(limit).all()
    events_data = []
    for r in records:
        events_data.append({
            "id": str(r.id),
            "event_name": r.event_name,
            "event_date": r.start_time.isoformat() if r.start_time else None,
            "max_inundation_depth_m": r.max_depth_m,
            "affected_area_km2": r.affected_area_km2,
            "severity": r.severity,
            "description": r.notes or f"Historical flood event in {r.source or 'Metropolitan area'}.",
        })

    # Fallback to curated catalog if database is freshly initialized
    if not events_data:
        events_data = [
            {
                "id": "EVT-2015-CHENNAI",
                "event_name": "Chennai Historic Flood Catastrophe (Nov-Dec 2015)",
                "event_date": "2015-12-01T00:00:00Z",
                "total_rainfall_mm": 494.0,
                "peak_rainfall_rate_mmh": 68.0,
                "max_inundation_depth_m": 2.80,
                "affected_area_km2": 42.0,
                "loss_estimate_usd": 3000000000,
                "description": "Unprecedented monsoon downpour coupled with Adyar Chembarambakkam reservoir outflow.",
            },
            {
                "id": "EVT-2023-MICHAUNG",
                "event_name": "Cyclone Michaung Cloudburst Inundation (Dec 2023)",
                "event_date": "2023-12-04T00:00:00Z",
                "total_rainfall_mm": 390.0,
                "peak_rainfall_rate_mmh": 52.0,
                "max_inundation_depth_m": 1.95,
                "affected_area_km2": 31.5,
                "loss_estimate_usd": 1200000000,
                "description": "Slow-moving intense cyclonic storm stalled over coast causing extensive urban waterlogging.",
            },
            {
                "id": "EVT-2021-NORTHEAST",
                "event_name": "Northeast Monsoon Flash Flood Spate (Nov 2021)",
                "event_date": "2021-11-07T00:00:00Z",
                "total_rainfall_mm": 215.0,
                "peak_rainfall_rate_mmh": 41.0,
                "max_inundation_depth_m": 1.10,
                "affected_area_km2": 16.2,
                "loss_estimate_usd": 350000000,
                "description": "Trough of low pressure generated overnight localized cloudburst inundation across core metropolitan sectors.",
            },
        ]

    return {
        "status": "success",
        "count": len(events_data),
        "data": events_data,
    }


@router.get("/reports/generate", status_code=status.HTTP_200_OK)
def generate_executive_briefing(
    event_name: str = Query(default="Current Monsoon Event"),
    peak_rainfall_mm: float = Query(default=180.0),
    peak_depth_m: float = Query(default=1.2),
    affected_area_km2: float = Query(default=14.0),
) -> Dict[str, Any]:
    """
    Generates a structured executive disaster assessment briefing report.
    """
    report = ReportService.generate_incident_report(
        event_name=event_name,
        peak_rainfall_mm=peak_rainfall_mm,
        peak_depth_m=peak_depth_m,
        affected_area_km2=affected_area_km2,
    )
    return {
        "status": "success",
        "data": report,
    }
