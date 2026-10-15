"""
backend/app/models/satellite.py
SQLAlchemy model for satellite precipitation data metadata.
Stores references to processed satellite data files (NetCDF/GeoTIFF)
along with spatial coverage and source information.
"""

import uuid

from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.app.core.database import Base


class SatelliteData(Base):
    """
    Metadata record for an ingested satellite precipitation dataset.
    The actual raster data is stored on disk; this table tracks what
    has been ingested, its coverage, and file location.
    """

    __tablename__ = "satellite_data"

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

    satellite_name = Column(String(100))        # e.g. "GPM", "TRMM"
    product_name = Column(String(255))          # e.g. "IMERG-Final-V07"

    file_path = Column(Text)                    # Path to processed file

    # Bounding box of the data
    min_lat = Column(Float)
    max_lat = Column(Float)
    min_lon = Column(Float)
    max_lon = Column(Float)

    # Data quality / availability flags
    mean_precipitation_mm = Column(Float)       # Spatial mean over study area
    max_precipitation_mm = Column(Float)        # Spatial max over study area
    data_coverage_pct = Column(Float)           # % of study area with valid data

    source = Column(String(100))                # Provider code e.g. "NASA_GPM"
    is_development_data = Column(
        String(3), default="NO"
    )                                           # "YES" if synthetic/dev data

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
