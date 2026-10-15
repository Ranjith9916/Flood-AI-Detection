"""
backend/app/models/flood.py
SQLAlchemy models for flood events (historical) and flood predictions (ML output).
"""

import uuid

from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.app.core.database import Base


class FloodEvent(Base):
    """
    Historical flood event record.
    Used for ML training labels and post-event analysis.
    """

    __tablename__ = "flood_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    event_name = Column(String(255))
    start_time = Column(DateTime(timezone=True), index=True)
    end_time = Column(DateTime(timezone=True))

    latitude = Column(Float)
    longitude = Column(Float)

    affected_area_km2 = Column(Float)
    max_depth_m = Column(Float)
    severity = Column(String(50))               # LOW, MODERATE, HIGH, SEVERE, EXTREME

    source = Column(String(100))                # Data provider
    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class FloodPrediction(Base):
    """
    ML model output: flood probability for a given location and time.
    Probability must be between 0 and 1 (enforced at application level).
    Never fabricated — only written by the inference pipeline.
    """

    __tablename__ = "flood_predictions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    prediction_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    forecast_valid_time = Column(DateTime(timezone=True))   # What time this predicts

    latitude = Column(Float)
    longitude = Column(Float)

    flood_probability = Column(Float)           # 0.0–1.0, from ML model
    risk_level = Column(String(50))             # LOW/MODERATE/HIGH/VERY_HIGH/EXTREME

    # Traceability
    model_name = Column(String(100))
    model_version = Column(String(100))
    feature_version = Column(String(100))

    # Data sources used for this prediction
    data_sources = Column(Text)                 # JSON array of source names

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
