"""
data_pipeline/processors/rainfall_accumulator.py
Computes multi-horizon rolling rainfall accumulations (1h, 3h, 6h, 12h, 24h, 48h, 72h).
Evaluates IMD meteorological heavy rainfall thresholds and automatically generates
early warning alerts in the database.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.rainfall import RainfallData
from backend.app.models.alert import Alert

logger = logging.getLogger(__name__)

# Standard meteorological durations in hours
ACCUMULATION_WINDOWS = [1, 3, 6, 12, 24, 48, 72]

# IMD Rainfall Classification Thresholds (24-hour accumulation in mm)
RAIN_CATEGORIES = {
    "EXTREMELY_HEAVY": settings.rainfall_extremely_heavy_threshold_mm,  # 204.5
    "VERY_HEAVY": settings.rainfall_very_heavy_threshold_mm,            # 115.5
    "HEAVY": settings.rainfall_heavy_threshold_mm,                      # 64.5
    "MODERATE": settings.rainfall_moderate_threshold_mm,                # 15.6
    "LIGHT": settings.rainfall_light_threshold_mm,                      # 2.5
}


class RainfallAccumulator:
    """
    Calculates accumulated rainfall for stations and geographic coordinates,
    checks alert criteria, and dispatches early warnings.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self._external_session = db_session

    def get_session(self) -> Session:
        if self._external_session:
            return self._external_session
        return SessionLocal()

    def calculate_station_accumulations(
        self,
        station_code: str,
        as_of_time: Optional[datetime] = None,
    ) -> dict[str, float]:
        """
        Calculates accumulated rainfall over 1h, 3h, 6h, 12h, 24h, 48h, 72h
        for a given station up to `as_of_time`.
        """
        if not as_of_time:
            as_of_time = datetime.now(timezone.utc)
        if as_of_time.tzinfo is None:
            as_of_time = as_of_time.replace(tzinfo=timezone.utc)

        session = self.get_session()
        accumulations = {}

        try:
            for window_h in ACCUMULATION_WINDOWS:
                window_start = as_of_time - timedelta(hours=window_h)
                total_rain = (
                    session.query(func.sum(RainfallData.rainfall_mm))
                    .filter(
                        RainfallData.station_code == station_code,
                        RainfallData.observation_time >= window_start,
                        RainfallData.observation_time <= as_of_time,
                        RainfallData.quality_flag.in_(["OK", "SUSPECT"]),
                    )
                    .scalar()
                )
                accumulations[f"{window_h}h"] = round(float(total_rain or 0.0), 2)

            return accumulations
        finally:
            if not self._external_session:
                session.close()

    def process_all_stations(
        self,
        as_of_time: Optional[datetime] = None,
        auto_generate_alerts: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Computes accumulations for all stations and optionally creates Alert records
        when heavy rain thresholds are crossed.
        """
        if not as_of_time:
            as_of_time = datetime.now(timezone.utc)

        session = self.get_session()
        results = []

        try:
            stations = (
                session.query(RainfallData.station_code)
                .filter(RainfallData.station_code.isnot(None))
                .distinct()
                .all()
            )
            station_codes = [s[0] for s in stations if s[0]]

            for code in station_codes:
                acc = self.calculate_station_accumulations(code, as_of_time)
                rain_24h = acc.get("24h", 0.0)
                category = self._classify_rainfall(rain_24h)

                results.append({
                    "station_code": code,
                    "as_of_time": as_of_time.isoformat(),
                    "accumulations": acc,
                    "rainfall_24h_mm": rain_24h,
                    "category": category,
                })

                if auto_generate_alerts and category in ["HEAVY", "VERY_HEAVY", "EXTREMELY_HEAVY"]:
                    self._create_alert_if_needed(session, code, rain_24h, category, as_of_time)

            session.commit()
            return results
        except Exception as exc:
            session.rollback()
            logger.error("Error in process_all_stations: %s", exc)
            raise
        finally:
            if not self._external_session:
                session.close()

    def _classify_rainfall(self, rain_24h: float) -> str:
        """Classifies 24h rainfall according to IMD standards."""
        if rain_24h >= RAIN_CATEGORIES["EXTREMELY_HEAVY"]:
            return "EXTREMELY_HEAVY"
        elif rain_24h >= RAIN_CATEGORIES["VERY_HEAVY"]:
            return "VERY_HEAVY"
        elif rain_24h >= RAIN_CATEGORIES["HEAVY"]:
            return "HEAVY"
        elif rain_24h >= RAIN_CATEGORIES["MODERATE"]:
            return "MODERATE"
        elif rain_24h >= RAIN_CATEGORIES["LIGHT"]:
            return "LIGHT"
        return "NO_RAIN"

    def _create_alert_if_needed(
        self,
        session: Session,
        station_code: str,
        rain_24h: float,
        category: str,
        as_of_time: datetime,
    ) -> None:
        """
        Creates an Alert if an active alert for this station does not already exist
        in the past 12 hours.
        """
        recent_threshold = as_of_time - timedelta(hours=12)
        existing = (
            session.query(Alert)
            .filter(
                Alert.alert_type == "HEAVY_RAIN",
                Alert.created_at >= recent_threshold,
                Alert.is_active.is_(True),
            )
            .first()
        )

        if not existing:
            severity = "CRITICAL" if category in ["EXTREMELY_HEAVY", "VERY_HEAVY"] else "HIGH"
            alert = Alert(
                id=uuid.uuid4(),
                alert_type="HEAVY_RAIN",
                severity=severity,
                title=f"{category.replace('_', ' ')} Alert: Station {station_code}",
                description=(
                    f"24-hour accumulated rainfall reached {rain_24h:.1f} mm at station {station_code}, "
                    f"exceeding the {category} threshold of {RAIN_CATEGORIES.get(category)} mm."
                ),
                is_active=True,
                created_at=as_of_time,
                expires_at=as_of_time + timedelta(hours=24),
            )
            session.add(alert)
            logger.warning("Created %s heavy rain alert for station %s (%.1f mm)", severity, station_code, rain_24h)
