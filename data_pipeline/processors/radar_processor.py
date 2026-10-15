"""
data_pipeline/processors/radar_processor.py
Orchestrates Doppler Weather Radar (DWR) data pipeline:
Collector -> Validator -> Database Loader -> Quality Report & Run Tracking.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from data_pipeline.collectors.radar_collector import RadarDataCollector
from data_pipeline.validators.radar_validator import RadarValidator
from data_pipeline.loaders.db_loader import DatabaseLoader

logger = logging.getLogger(__name__)


class RadarProcessor:
    """
    Ingests radar reflectivity and derived rainfall rate scans.
    """

    def __init__(self, radar_name: str = "BLR_DWR_RADAR"):
        self.collector = RadarDataCollector(radar_name=radar_name)
        self.validator = RadarValidator()
        self.loader = DatabaseLoader()

    def process(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        product_name: str = "CAPPI_2KM",
    ) -> dict[str, Any]:
        """
        Runs radar ingestion cycle.
        """
        pipeline_run_id = self.loader.start_pipeline_run(pipeline_name="radar_ingestion")

        try:
            # 1. Fetch
            result = self.collector.fetch(
                start=start_time,
                end=end_time,
                product_name=product_name,
            )

            # 2. Validate
            valid_recs, rejected_recs, stats = self.validator.validate_batch(result.records)

            # 3. Load to DB
            inserted = self.loader.load_radar_records(valid_recs)

            # 4. Save quality report
            self.loader.save_quality_report(
                pipeline_run_id=pipeline_run_id,
                source="radar_dwr",
                stats=stats,
            )

            # 5. Complete run
            self.loader.complete_pipeline_run(
                run_id=pipeline_run_id,
                status="SUCCESS",
                records_received=len(result.records),
                records_valid=len(valid_recs),
                records_rejected=len(rejected_recs),
                records_inserted=inserted,
            )

            return {
                "pipeline_run_id": str(pipeline_run_id),
                "status": "SUCCESS",
                "records_received": len(result.records),
                "records_valid": len(valid_recs),
                "records_inserted": inserted,
            }
        except Exception as exc:
            logger.error("Radar processor run %s failed: %s", pipeline_run_id, exc)
            self.loader.complete_pipeline_run(
                run_id=pipeline_run_id,
                status="FAILED",
                error_message=str(exc),
            )
            raise
