"""
backend/app/models/radar.py
SQLAlchemy model for weather radar data metadata.
"""

import uuid

from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.app.core.database import Base


class RadarData(Base):
    """
    Metadata for an ingested radar scan/composite.
    The actual raster/grid data is stored on disk.
    """

    __tablename__ = "radar_data"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    observation_time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    radar_name = Column(String(100))            # e.g. "BLR_RADAR"
    product_name = Column(String(255))          # e.g. "CAPPI_2km", "COMPOSITE"

    file_path = Column(Text)

    # Spatial coverage
    min_lat = Column(Float)
    max_lat = Column(Float)
    min_lon = Column(Float)
    max_lon = Column(Float)

    # Derived statistics over study area
    mean_reflectivity_dbz = Column(Float)
    max_reflectivity_dbz = Column(Float)
    mean_rainfall_rate_mmh = Column(Float)      # mm/hour

    source = Column(String(100))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
