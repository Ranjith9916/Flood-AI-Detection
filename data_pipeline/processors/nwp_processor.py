"""
data_pipeline/processors/nwp_processor.py
Orchestrates Numerical Weather Prediction (NWP) data pipeline:
Collector -> Validator -> Database Loader -> Quality Report & Run Tracking.
"""

import logging
from typing import Any, Optional

from data_pipeline.collectors.nwp_collector import NwpDataCollector
from data_pipeline.validators.nwp_validator import NwpValidator
from data_pipeline.loaders.db_loader import DatabaseLoader

logger = logging.getLogger(__name__)

# Default forecast target locations (urban / basin points)
DEFAULT_NWP_POINTS = [
    {"name": "Bangalore Urban", "lat": 12.9716, "lon": 77.5946},
    {"name": "Bangalore Rural Catchment", "lat": 13.1500, "lon": 77.6500},
]


class NwpProcessor:
    """
    Ingests multi-horizon NWP forecast cycles.
    """

    def __init__(self, model_name: str = "ECMWF_IFS"):
        self.collector = NwpDataCollector(model_name=model_name)
        self.validator = NwpValidator()
        self.loader = DatabaseLoader()

    def process_forecasts(
        self,
        points: Optional[list[dict[str, Any]]] = None,
        forecast_days: int = 3,
    ) -> dict[str, Any]:
        """
        Fetches and ingests forecast horizons for points in the study domain.
        """
        pipeline_run_id = self.loader.start_pipeline_run(pipeline_name="nwp_ingestion")
        points_to_process = points or DEFAULT_NWP_POINTS

        total_received = 0
        total_valid = 0
        total_rejected = 0
        total_inserted = 0

        try:
            for pt in points_to_process:
                result = self.collector.fetch(
                    latitude=pt["lat"],
                    longitude=pt["lon"],
                    forecast_days=forecast_days,
                )

                if not result.success or not result.records:
                    continue

                total_received += len(result.records)

                # Validate
                valid_recs, rejected_recs, stats = self.validator.validate_batch(result.records)
                total_valid += len(valid_recs)
                total_rejected += len(rejected_recs)

                # Load
                inserted = self.loader.load_nwp_forecasts(valid_recs)
                total_inserted += inserted

            # Complete run
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
                "points_processed": len(points_to_process),
                "records_received": total_received,
                "records_valid": total_valid,
                "records_inserted": total_inserted,
            }
        except Exception as exc:
            logger.error("NWP processor run %s failed: %s", pipeline_run_id, exc)
            self.loader.complete_pipeline_run(
                run_id=pipeline_run_id,
                status="FAILED",
                error_message=str(exc),
            )
            raise
