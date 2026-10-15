"""
data_pipeline/processors/weather_processor.py
Orchestrates weather data ingestion pipeline:
Collector -> Validator -> Database Loader -> Rainfall Mirroring -> Accumulation Engine.
Full telemetry with PipelineRun and DataQualityReport tracking.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from data_pipeline.collectors.weather_collector import OpenMeteoWeatherProvider
from data_pipeline.validators.weather_validator import WeatherValidator
from data_pipeline.loaders.db_loader import DatabaseLoader
from data_pipeline.processors.rainfall_accumulator import RainfallAccumulator

logger = logging.getLogger(__name__)

# Default monitoring stations (South India / Bangalore study basin)
DEFAULT_STATIONS = [
    {"code": "BLR_CENTRAL", "name": "Bangalore Central", "lat": 12.9716, "lon": 77.5946},
    {"code": "BLR_AIRPORT", "name": "Kempegowda Airport", "lat": 13.1986, "lon": 77.7066},
    {"code": "BLR_SOUTH",   "name": "Bangalore South",   "lat": 12.8900, "lon": 77.5800},
    {"code": "BLR_EAST",    "name": "Whitefield East",   "lat": 12.9698, "lon": 77.7500},
]


class WeatherProcessor:
    """
    Executes end-to-end weather observation pipeline.
    """

    def __init__(self):
        self.provider = OpenMeteoWeatherProvider()
        self.validator = WeatherValidator()
        self.loader = DatabaseLoader()
        self.accumulator = RainfallAccumulator()

    def process_stations(
        self,
        stations: Optional[list[dict[str, Any]]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Runs the full ingestion cycle across all provided or default stations.
        """
        pipeline_run_id = self.loader.start_pipeline_run(pipeline_name="weather_ingestion")
        stations_to_process = stations or DEFAULT_STATIONS

        total_received = 0
        total_valid = 0
        total_rejected = 0
        total_inserted = 0
        aggregated_stats = {
            "total": 0, "valid": 0, "suspect": 0, "rejected": 0, "field_errors": {}
        }

        try:
            for st in stations_to_process:
                code = st["code"]
                lat = st["lat"]
                lon = st["lon"]

                # 1. Fetch from provider
                result = self.provider.fetch(
                    station_code=code,
                    latitude=lat,
                    longitude=lon,
                    start=start_date,
                    end=end_date,
                )

                if not result.success or not result.records:
                    logger.warning("No records fetched for station %s: %s", code, result.error_message)
                    continue

                total_received += len(result.records)

                # 2. Validate
                valid_recs, rejected_recs, stats = self.validator.validate_batch(result.records)
                total_valid += len(valid_recs)
                total_rejected += len(rejected_recs)

                # Merge stats
                aggregated_stats["total"] += stats["total"]
                aggregated_stats["valid"] += stats["valid"]
                aggregated_stats["suspect"] += stats["suspect"]
                aggregated_stats["rejected"] += stats["rejected"]
                for k, v in stats.get("field_errors", {}).items():
                    aggregated_stats["field_errors"][k] = aggregated_stats["field_errors"].get(k, 0) + v

                # 3. Load weather observations into DB
                inserted = self.loader.load_weather_observations(valid_recs)
                total_inserted += inserted

                # 4. Mirror valid rainfall data into rainfall_data table
                rainfall_recs = [
                    {
                        "observation_time": r["observation_time"],
                        "source": "STATION",
                        "latitude": r.get("latitude"),
                        "longitude": r.get("longitude"),
                        "rainfall_mm": r.get("rainfall_mm") or 0.0,
                        "duration_minutes": 60,
                        "station_code": r.get("station_code"),
                        "quality_flag": r.get("quality_flag", "OK"),
                    }
                    for r in valid_recs
                    if r.get("rainfall_mm") is not None
                ]
                self.loader.load_rainfall_records(rainfall_recs)

            # 5. Trigger multi-horizon accumulation and alerting
            accumulation_results = self.accumulator.process_all_stations()

            # 6. Save data quality report
            self.loader.save_quality_report(
                pipeline_run_id=pipeline_run_id,
                source="weather_observations",
                stats=aggregated_stats,
            )

            # 7. Complete pipeline run
            self.loader.complete_pipeline_run(
                run_id=pipeline_run_id,
                status="SUCCESS",
                records_received=total_received,
                records_valid=total_valid,
                records_rejected=total_rejected,
                records_inserted=total_inserted,
            )

            return {
                "pipeline_run_id": str(pipeline_run_id),
                "status": "SUCCESS",
                "stations_processed": len(stations_to_process),
                "records_received": total_received,
                "records_valid": total_valid,
                "records_rejected": total_rejected,
                "records_inserted": total_inserted,
                "accumulations": accumulation_results,
            }

        except Exception as exc:
            logger.error("Weather pipeline run %s failed: %s", pipeline_run_id, exc)
            self.loader.complete_pipeline_run(
                run_id=pipeline_run_id,
                status="FAILED",
                records_received=total_received,
                records_valid=total_valid,
                records_rejected=total_rejected,
                records_inserted=total_inserted,
                error_message=str(exc),
            )
            raise
