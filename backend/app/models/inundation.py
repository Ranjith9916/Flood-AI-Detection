"""
backend/app/models/inundation.py
SQLAlchemy model for inundation prediction results.
Stores metadata and file references for raster-based inundation outputs.
"""

import uuid

from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.app.core.database import Base


class InundationPrediction(Base):
    """
    Inundation prediction output from the geospatial ML model.
    The raster (GeoTIFF/NetCDF) is stored on disk at file_path.
    Aggregate statistics are stored in the database for quick querying.

    NOTE: This model requires historical inundation labels for training.
    If labels are unavailable, inference_status will indicate 'LABELS_REQUIRED'.
    """

    __tablename__ = "inundation_predictions"

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

    forecast_valid_time = Column(DateTime(timezone=True))

    # Output raster file references
    flood_probability_raster_path = Column(Text)    # GeoTIFF: probability 0-1
    inundation_depth_raster_path = Column(Text)     # GeoTIFF: depth in metres

    # Aggregate statistics
    affected_area_km2 = Column(Float)
    maximum_depth_m = Column(Float)
    mean_depth_m = Column(Float)
    affected_population = Column(Float)             # If population data available

    # Spatial extent of prediction
    min_lat = Column(Float)
    max_lat = Column(Float)
    min_lon = Column(Float)
    max_lon = Column(Float)

    # Confidence
    model_confidence = Column(Float)                # 0-1

    # Status
    inference_status = Column(
        String(50),
        default="COMPLETE",
    )
    # Possible values:
    #   COMPLETE           - prediction generated
    #   LABELS_REQUIRED    - no training labels available
    #   INSUFFICIENT_DATA  - not enough input data
    #   MODEL_NOT_TRAINED  - model file not found
    #   ERROR              - inference failed

    # Traceability
    model_name = Column(String(100))
    model_version = Column(String(100))
    feature_version = Column(String(100))

    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
