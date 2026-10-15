"""
backend/app/models/weather.py
SQLAlchemy models for weather stations and observations.
"""

import uuid

from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey,
    CheckConstraint, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class WeatherStation(Base):
    """
    A physical or virtual weather observation station.
    station_code is the unique identifier used across all subsystems.
    """

    __tablename__ = "weather_stations"

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="chk_station_lat_range",
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="chk_station_lon_range",
        ),
        UniqueConstraint("station_code", name="uq_station_code"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    station_code = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    station_name = Column(String(255))

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    elevation_m = Column(Float)

    source = Column(String(100))                # e.g. "IMD", "OPEN_METEO", "AWS"

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationship
    observations = relationship(
        "WeatherObservation",
        back_populates="station",
    )


class WeatherObservation(Base):
    """
    A single weather observation record from a station.
    All timestamps are stored in UTC.
    """

    __tablename__ = "weather_observations"

    __table_args__ = (
        CheckConstraint(
            "humidity_percent IS NULL OR "
            "(humidity_percent >= 0 AND humidity_percent <= 100)",
            name="chk_obs_humidity_range",
        ),
        CheckConstraint(
            "rainfall_mm IS NULL OR rainfall_mm >= 0",
            name="chk_obs_rainfall_non_negative",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    station_id = Column(
        UUID(as_uuid=True),
        ForeignKey("weather_stations.id"),
        nullable=False,
        index=True,
    )

    observation_time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    temperature_c = Column(Float)
    humidity_percent = Column(Float)
    pressure_hpa = Column(Float)
    wind_speed_ms = Column(Float)
    wind_direction_deg = Column(Float)
    rainfall_mm = Column(Float)

    quality_flag = Column(String(10), default="OK")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationship
    station = relationship(
        "WeatherStation",
        back_populates="observations",
    )
