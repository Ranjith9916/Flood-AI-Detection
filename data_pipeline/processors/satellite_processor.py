"""
data_pipeline/processors/satellite_processor.py
Orchestrates satellite precipitation pipeline:
Collector -> Validator -> Database Loader -> Quality Report & Run Tracking.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from data_pipeline.collectors.satellite_collector import SatelliteDataCollector
from data_pipeline.validators.satellite_validator import SatelliteValidator
from data_pipeline.loaders.db_loader import DatabaseLoader

logger = logging.getLogger(__name__)


class SatelliteProcessor:
    """
    Ingests and processes satellite precipitation tiles / metadata.
    """

    def __init__(self):
        self.collector = SatelliteDataCollector()
        self.validator = SatelliteValidator()
        self.loader = DatabaseLoader()

    def process(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        satellite_name: str = "GPM",
        product_name: str = "IMERG-Final-V07",
    ) -> dict[str, Any]:
        """
        Runs satellite ingestion cycle.
        """
        pipeline_run_id = self.loader.start_pipeline_run(pipeline_name="satellite_ingestion")

        try:
            # 1. Fetch
            result = self.collector.fetch(
                start=start_time,
                end=end_time,
                satellite_name=satellite_name,
                product_name=product_name,
            )

            # 2. Validate
            valid_recs, rejected_recs, stats = self.validator.validate_batch(result.records)

            # 3. Load to DB
            inserted = self.loader.load_satellite_records(valid_recs)

            # 4. Save quality report
            self.loader.save_quality_report(
                pipeline_run_id=pipeline_run_id,
                source=f"satellite_{satellite_name.lower()}",
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
            logger.error("Satellite processor run %s failed: %s", pipeline_run_id, exc)
            self.loader.complete_pipeline_run(
                run_id=pipeline_run_id,
                status="FAILED",
                error_message=str(exc),
            )
            raise
