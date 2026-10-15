"""
backend/app/api/alerts.py
Alert management endpoints.
Full lifecycle: list, get active, acknowledge.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.alert import Alert
from backend.app.schemas.alert import AlertListResponse, AlertOut, AlertAcknowledgeRequest

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=AlertListResponse)
def get_alerts(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    active_only: bool = False,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """List all alerts with optional filters."""
    query = db.query(Alert).order_by(Alert.alert_time.desc())
    if active_only:
        query = query.filter(Alert.is_active == True)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if status:
        query = query.filter(Alert.status == status.upper())
    if start:
        query = query.filter(Alert.alert_time >= start)
    if end:
        query = query.filter(Alert.alert_time <= end)

    records = query.offset(offset).limit(limit).all()
    return AlertListResponse(count=len(records), data=records)


@router.get("/active", response_model=AlertListResponse)
def get_active_alerts(
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return only currently active alerts, ordered by severity."""
    severity_order = {
        "EMERGENCY": 0, "SEVERE_WARNING": 1, "WARNING": 2,
        "ADVISORY": 3, "WATCH": 4, "INFO": 5,
    }
    query = db.query(Alert).filter(Alert.is_active == True)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    records = query.all()
    records.sort(key=lambda a: severity_order.get(a.severity, 99))
    return AlertListResponse(count=len(records), data=records)


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: UUID,
    body: AlertAcknowledgeRequest,
    db: Session = Depends(get_db),
):
    """Acknowledge an active alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=404,
            detail=f"Alert {alert_id} not found",
        )
    if alert.status == "ACKNOWLEDGED":
        raise HTTPException(
            status_code=400,
            detail="Alert already acknowledged",
        )

    alert.status = "ACKNOWLEDGED"
    alert.is_active = False
    alert.acknowledged_at = datetime.now(timezone.utc)
    if body.notes:
        alert.notes = body.notes

    db.commit()
    db.refresh(alert)
    return alert


@router.get("/{alert_id}/cap.xml")
def get_alert_cap_xml(
    alert_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Export an alert in international OASIS CAP v1.2 XML format.
    """
    from fastapi.responses import Response
    from backend.app.services.cap_service import CAPService

    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    evac = CAPService.compute_evacuation_zones(13.0827, 80.2707, 0.8)
    xml_content = CAPService.generate_cap_xml(
        alert_id=str(alert.id),
        headline=f"{alert.severity} Risk: {alert.alert_type}",
        description=alert.message or "Immediate emergency flood precaution advised.",
        severity=alert.severity,
        polygon_coords=evac["critical_evacuation_polygon"],
    )
    return Response(content=xml_content, media_type="application/xml")


@router.post("/{alert_id}/dispatch")
async def dispatch_alert_channels(
    alert_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Triggers multi-channel emergency broadcast (WebSockets, CAP Feed, Webhooks) for an alert.
    """
    from backend.app.services.dispatcher import AlertDispatcher

    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    res = await AlertDispatcher.dispatch_emergency_alert(
        alert_id=str(alert.id),
        title=f"{alert.severity} Warning: {alert.alert_type}",
        description=alert.message or "Severe precipitation and inundation risk.",
        severity=alert.severity,
        alert_type=alert.alert_type,
        center_lat=13.0827,
        center_lon=80.2707,
        inundation_depth_m=0.85,
    )
    return {"status": "success", "data": res}

