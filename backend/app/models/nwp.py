"""
backend/app/models/nwp.py
SQLAlchemy model for Numerical Weather Prediction (NWP) forecast data.
"""

import uuid

from sqlalchemy import Column, String, Float, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.app.core.database import Base


class NwpForecast(Base):
    """
    A single NWP forecast point/grid cell value.
    For gridded NWP data, each spatial point is stored as a row.
    For raster-based NWP, store metadata only and reference file_path.
    """

    __tablename__ = "nwp_forecasts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    model_name = Column(
        String(100),
        nullable=False,
    )                                           # e.g. "GFS", "OPEN_METEO_WMO"

    forecast_time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )                                           # Model initialization time

    valid_time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )                                           # Forecast valid time

    lead_time_hours = Column(Integer)           # valid_time - forecast_time in hours

    # Point location (for station-based or point extraction)
    latitude = Column(Float)
    longitude = Column(Float)

    # Forecast variables
    rainfall_mm = Column(Float)                 # Accumulated precipitation (mm)
    temperature_c = Column(Float)
    humidity_percent = Column(Float)
    wind_speed_ms = Column(Float)
    wind_direction_deg = Column(Float)
    pressure_hpa = Column(Float)

    # For gridded/raster NWP
    file_path = Column(Text)

    source = Column(String(100))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
