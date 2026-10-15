"""
data_pipeline/loaders/db_loader.py
Database loader for all pipeline data sources.
Provides batch ingestion, deduplication, pipeline run tracking,
and automated data quality reporting in PostgreSQL/PostGIS.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.weather import WeatherStation, WeatherObservation
from backend.app.models.rainfall import RainfallData
from backend.app.models.satellite import SatelliteData
from backend.app.models.radar import RadarData
from backend.app.models.nwp import NwpForecast
from backend.app.models.pipeline import PipelineRun, DataQualityReport

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """
    Ingests validated records into PostgreSQL and records pipeline execution metrics.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self._external_session = db_session

    def get_session(self) -> Session:
        if self._external_session:
            return self._external_session
        return SessionLocal()

    def start_pipeline_run(self, pipeline_name: str) -> uuid.UUID:
        """Starts a PipelineRun log and returns its ID."""
        run_id = uuid.uuid4()
        session = self.get_session()
        try:
            run = PipelineRun(
                id=run_id,
                pipeline_name=pipeline_name,
                started_at=datetime.now(timezone.utc),
                status="RUNNING",
                records_received=0,
                records_valid=0,
                records_rejected=0,
                records_inserted=0,
                records_duplicate=0,
            )
            session.add(run)
            session.commit()
            return run_id
        except Exception as exc:
            session.rollback()
            logger.error("Failed to start pipeline run for %s: %s", pipeline_name, exc)
            return run_id
        finally:
            if not self._external_session:
                session.close()

    def complete_pipeline_run(
        self,
        run_id: uuid.UUID,
        status: str = "SUCCESS",
        records_received: int = 0,
        records_valid: int = 0,
        records_rejected: int = 0,
        records_inserted: int = 0,
        records_duplicate: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Completes a PipelineRun log."""
        session = self.get_session()
        try:
            run = session.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            if run:
                now = datetime.now(timezone.utc)
                run.completed_at = now
                run.status = status
                run.records_received = records_received
                run.records_valid = records_valid
                run.records_rejected = records_rejected
                run.records_inserted = records_inserted
                run.records_duplicate = records_duplicate
                run.error_message = error_message
                if run.started_at:
                    run.duration_seconds = (now - run.started_at).total_seconds()
                session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Failed to complete pipeline run %s: %s", run_id, exc)
        finally:
            if not self._external_session:
                session.close()

    def save_quality_report(
        self,
        pipeline_run_id: Optional[uuid.UUID],
        source: str,
        stats: dict[str, Any],
    ) -> None:
        """Stores a DataQualityReport record for auditing."""
        session = self.get_session()
        try:
            report = DataQualityReport(
                id=uuid.uuid4(),
                pipeline_run_id=pipeline_run_id,
                source=source,
                report_time=datetime.now(timezone.utc),
                records_received=stats.get("total", 0),
                records_valid=stats.get("valid", 0),
                records_rejected=stats.get("rejected", 0),
                missing_values=sum(stats.get("field_errors", {}).values()),
                duplicates=stats.get("duplicates", 0),
                out_of_range=stats.get("out_of_range", 0),
                invalid_timestamps=stats.get("invalid_timestamps", 0),
                details_json=json.dumps(stats.get("field_errors", {})),
            )
            session.add(report)
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Failed to save quality report for %s: %s", source, exc)
        finally:
            if not self._external_session:
                session.close()

    def load_weather_observations(
        self,
        records: list[dict[str, Any]],
        station_id_map: Optional[dict[str, uuid.UUID]] = None,
    ) -> int:
        """
        Inserts weather observations, resolving station_code to station_id.
        """
        if not records:
            return 0

        session = self.get_session()
        inserted_count = 0
        try:
            # Build station code -> ID cache if not supplied
            if not station_id_map:
                stations = session.query(WeatherStation).all()
                station_id_map = {s.station_code: s.id for s in stations}

            for rec in records:
                st_code = rec.get("station_code")
                station_id = station_id_map.get(st_code)

                # If station does not exist, register it automatically
                if not station_id and st_code:
                    new_station = WeatherStation(
                        id=uuid.uuid4(),
                        station_code=st_code,
                        station_name=f"Station {st_code}",
                        latitude=rec.get("latitude", 12.97),
                        longitude=rec.get("longitude", 77.59),
                        source=rec.get("source", "OPEN_METEO"),
                    )
                    session.add(new_station)
                    session.flush()
                    station_id = new_station.id
                    station_id_map[st_code] = station_id

                if not station_id:
                    continue

                obs = WeatherObservation(
                    id=uuid.uuid4(),
                    station_id=station_id,
                    observation_time=rec["observation_time"],
                    temperature_c=rec.get("temperature_c"),
                    humidity_percent=rec.get("humidity_percent"),
                    pressure_hpa=rec.get("pressure_hpa"),
                    wind_speed_ms=rec.get("wind_speed_ms"),
                    wind_direction_deg=rec.get("wind_direction_deg"),
                    rainfall_mm=rec.get("rainfall_mm"),
                    quality_flag=rec.get("quality_flag", "OK"),
                )
                session.add(obs)
                inserted_count += 1

            session.commit()
            return inserted_count
        except Exception as exc:
            session.rollback()
            logger.error("Failed to load weather observations: %s", exc)
            raise
        finally:
            if not self._external_session:
                session.close()

    def load_rainfall_records(self, records: list[dict[str, Any]]) -> int:
        """
        Inserts rainfall records into rainfall_data table.
        """
        if not records:
            return 0

        session = self.get_session()
        inserted_count = 0
        try:
            for rec in records:
                rainfall_entry = RainfallData(
                    id=uuid.uuid4(),
                    observation_time=rec["observation_time"],
                    source=rec["source"],
                    latitude=rec.get("latitude"),
                    longitude=rec.get("longitude"),
                    rainfall_mm=rec["rainfall_mm"],
                    duration_minutes=rec.get("duration_minutes", 60),
                    station_code=rec.get("station_code"),
                    quality_flag=rec.get("quality_flag", "OK"),
                )
                session.add(rainfall_entry)
                inserted_count += 1

            session.commit()
            return inserted_count
        except Exception as exc:
            session.rollback()
            logger.error("Failed to load rainfall records: %s", exc)
            raise
        finally:
            if not self._external_session:
                session.close()

    def load_satellite_records(self, records: list[dict[str, Any]]) -> int:
        """Inserts satellite metadata records."""
        if not records:
            return 0

        session = self.get_session()
        inserted_count = 0
        try:
            for rec in records:
                sat = SatelliteData(
                    id=uuid.uuid4(),
                    observation_time=rec["observation_time"],
                    satellite_name=rec["satellite_name"],
                    product_name=rec["product_name"],
                    file_path=rec.get("file_path"),
                    min_lat=rec.get("min_lat"),
                    max_lat=rec.get("max_lat"),
                    min_lon=rec.get("min_lon"),
                    max_lon=rec.get("max_lon"),
                    mean_precipitation_mm=rec.get("mean_precipitation_mm"),
                    max_precipitation_mm=rec.get("max_precipitation_mm"),
                    data_coverage_pct=rec.get("data_coverage_pct"),
                    source=rec.get("source", "NASA_GPM"),
                    is_development_data=rec.get("is_development_data", "NO"),
                )
                session.add(sat)
                inserted_count += 1

            session.commit()
            return inserted_count
        except Exception as exc:
            session.rollback()
            logger.error("Failed to load satellite records: %s", exc)
            raise
        finally:
            if not self._external_session:
                session.close()

    def load_radar_records(self, records: list[dict[str, Any]]) -> int:
        """Inserts radar scan metadata records."""
        if not records:
            return 0

        session = self.get_session()
        inserted_count = 0
        try:
            for rec in records:
                radar_entry = RadarData(
                    id=uuid.uuid4(),
                    observation_time=rec["observation_time"],
                    radar_name=rec["radar_name"],
                    product_name=rec["product_name"],
                    file_path=rec.get("file_path"),
                    min_lat=rec.get("min_lat"),
                    max_lat=rec.get("max_lat"),
                    min_lon=rec.get("min_lon"),
                    max_lon=rec.get("max_lon"),
                    mean_reflectivity_dbz=rec.get("mean_reflectivity_dbz"),
                    max_reflectivity_dbz=rec.get("max_reflectivity_dbz"),
                    mean_rainfall_rate_mmh=rec.get("mean_rainfall_rate_mmh"),
                    source=rec.get("source", "DWR_RADAR"),
                )
                session.add(radar_entry)
                inserted_count += 1

            session.commit()
            return inserted_count
        except Exception as exc:
            session.rollback()
            logger.error("Failed to load radar records: %s", exc)
            raise
        finally:
            if not self._external_session:
                session.close()

    def load_nwp_forecasts(self, records: list[dict[str, Any]]) -> int:
        """Inserts NWP forecast records."""
        if not records:
            return 0

        session = self.get_session()
        inserted_count = 0
        try:
            for rec in records:
                nwp_entry = NwpForecast(
                    id=uuid.uuid4(),
                    model_name=rec["model_name"],
                    forecast_time=rec["forecast_time"],
                    valid_time=rec["valid_time"],
                    lead_time_hours=rec.get("lead_time_hours"),
                    latitude=rec.get("latitude"),
                    longitude=rec.get("longitude"),
                    rainfall_mm=rec.get("rainfall_mm"),
                    temperature_c=rec.get("temperature_c"),
                    humidity_percent=rec.get("humidity_percent"),
                    wind_speed_ms=rec.get("wind_speed_ms"),
                    wind_direction_deg=rec.get("wind_direction_deg"),
                    pressure_hpa=rec.get("pressure_hpa"),
                    file_path=rec.get("file_path"),
                    source=rec.get("source", "OPEN_METEO_NWP"),
                )
                session.add(nwp_entry)
                inserted_count += 1

            session.commit()
            return inserted_count
        except Exception as exc:
            session.rollback()
            logger.error("Failed to load NWP forecast records: %s", exc)
            raise
        finally:
            if not self._external_session:
                session.close()
