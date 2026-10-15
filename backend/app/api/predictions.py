"""
backend/app/api/predictions.py
Prediction result endpoints.
Returns real ML model outputs from the database.
If no models have been trained, returns a clear status message.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.flood import FloodPrediction
from backend.app.models.inundation import InundationPrediction
from backend.app.schemas.flood import FloodPredictionListResponse
from backend.app.schemas.inundation import InundationListResponse

router = APIRouter(prefix="/predictions", tags=["Predictions"])

_NOT_TRAINED_MSG = (
    "No trained model available. "
    "Run the ML training pipeline to generate predictions."
)


@router.get("/flood", response_model=FloodPredictionListResponse)
def get_flood_predictions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Return flood probability predictions from the database.
    Results are from the ML inference pipeline only — never fabricated.
    """
    query = db.query(FloodPrediction).order_by(
        FloodPrediction.prediction_time.desc()
    )
    if start:
        query = query.filter(FloodPrediction.prediction_time >= start)
    if end:
        query = query.filter(FloodPrediction.prediction_time <= end)
    if risk_level:
        query = query.filter(
            FloodPrediction.risk_level == risk_level.upper()
        )

    records = query.offset(offset).limit(limit).all()

    return FloodPredictionListResponse(count=len(records), data=records)


@router.get("/inundation", response_model=InundationListResponse)
def get_inundation_predictions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    inference_status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Return inundation prediction results from the database.
    Check inference_status field to understand model availability.
    """
    query = db.query(InundationPrediction).order_by(
        InundationPrediction.prediction_time.desc()
    )
    if start:
        query = query.filter(InundationPrediction.prediction_time >= start)
    if end:
        query = query.filter(InundationPrediction.prediction_time <= end)
    if inference_status:
        query = query.filter(
            InundationPrediction.inference_status == inference_status.upper()
        )

    records = query.offset(offset).limit(limit).all()
    return InundationListResponse(count=len(records), data=records)


@router.get("/heavy-rain")
def get_heavy_rain_predictions():
    """
    Heavy rainfall classification predictions.
    Model training pipeline must be completed before results appear here.
    """
    return {
        "status": "unavailable",
        "message": _NOT_TRAINED_MSG,
        "model": "heavy_rain_classifier",
        "data": [],
    }


@router.get("/rainfall")
def get_rainfall_forecasts():
    """
    Rainfall forecast predictions.
    Model training pipeline must be completed before results appear here.
    """
    return {
        "status": "unavailable",
        "message": _NOT_TRAINED_MSG,
        "model": "rainfall_forecast",
        "data": [],
    }
