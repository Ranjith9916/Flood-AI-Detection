"""
data_pipeline/schedulers/pipeline_scheduler.py
Background pipeline runner and task scheduler.
Periodically triggers weather, radar, satellite, and NWP ingestion cycles
and evaluates rainfall accumulation alerts.
"""

import logging
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Optional

from data_pipeline.processors.weather_processor import WeatherProcessor
from data_pipeline.processors.satellite_processor import SatelliteProcessor
from data_pipeline.processors.radar_processor import RadarProcessor
from data_pipeline.processors.nwp_processor import NwpProcessor
from data_pipeline.processors.rainfall_accumulator import RainfallAccumulator

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """
    Manages automated periodic data ingestion tasks.
    """

    def __init__(
        self,
        weather_interval_s: int = 900,     # 15 minutes
        radar_interval_s: int = 600,       # 10 minutes
        satellite_interval_s: int = 1800,  # 30 minutes
        nwp_interval_s: int = 21600,       # 6 hours
        accumulate_interval_s: int = 900,  # 15 minutes
    ):
        self.weather_interval_s = weather_interval_s
        self.radar_interval_s = radar_interval_s
        self.satellite_interval_s = satellite_interval_s
        self.nwp_interval_s = nwp_interval_s
        self.accumulate_interval_s = accumulate_interval_s

        self.weather_proc = WeatherProcessor()
        self.satellite_proc = SatelliteProcessor()
        self.radar_proc = RadarProcessor()
        self.nwp_proc = NwpProcessor()
        self.accumulator = RainfallAccumulator()

        self._running = False
        self._last_run: dict[str, float] = {}

    def run_all_once(self) -> dict:
        """Runs one full pass of all data pipelines."""
        logger.info("Executing single pass of all ingestion pipelines...")
        results = {}

        try:
            logger.info("--> Running Weather Ingestion...")
            results["weather"] = self.weather_proc.process_stations()
        except Exception as e:
            logger.error("Weather ingestion failed: %s", e)
            results["weather"] = {"status": "FAILED", "error": str(e)}

        try:
            logger.info("--> Running Satellite Ingestion...")
            results["satellite"] = self.satellite_proc.process()
        except Exception as e:
            logger.error("Satellite ingestion failed: %s", e)
            results["satellite"] = {"status": "FAILED", "error": str(e)}

        try:
            logger.info("--> Running Radar Ingestion...")
            results["radar"] = self.radar_proc.process()
        except Exception as e:
            logger.error("Radar ingestion failed: %s", e)
            results["radar"] = {"status": "FAILED", "error": str(e)}

        try:
            logger.info("--> Running NWP Ingestion...")
            results["nwp"] = self.nwp_proc.process_forecasts()
        except Exception as e:
            logger.error("NWP ingestion failed: %s", e)
            results["nwp"] = {"status": "FAILED", "error": str(e)}

        try:
            logger.info("--> Running Accumulation & Alert Engine...")
            acc = self.accumulator.process_all_stations(auto_generate_alerts=True)
            results["accumulation"] = {"status": "SUCCESS", "stations": len(acc)}
        except Exception as e:
            logger.error("Accumulation engine failed: %s", e)
            results["accumulation"] = {"status": "FAILED", "error": str(e)}

        logger.info("Ingestion pass complete.")
        return results

    def start(self):
        """Starts the scheduler loop."""
        self._running = True
        logger.info("Pipeline Scheduler started. Intervals: Weather=%ds, Radar=%ds, Sat=%ds, NWP=%ds",
                    self.weather_interval_s, self.radar_interval_s, self.satellite_interval_s, self.nwp_interval_s)

        # Run immediately on startup
        self.run_all_once()
        now_ts = time.time()
        self._last_run = {
            "weather": now_ts,
            "radar": now_ts,
            "satellite": now_ts,
            "nwp": now_ts,
            "accumulate": now_ts,
        }

        while self._running:
            try:
                now = time.time()

                if now - self._last_run.get("weather", 0) >= self.weather_interval_s:
                    self.weather_proc.process_stations()
                    self._last_run["weather"] = now

                if now - self._last_run.get("radar", 0) >= self.radar_interval_s:
                    self.radar_proc.process()
                    self._last_run["radar"] = now

                if now - self._last_run.get("satellite", 0) >= self.satellite_interval_s:
                    self.satellite_proc.process()
                    self._last_run["satellite"] = now

                if now - self._last_run.get("nwp", 0) >= self.nwp_interval_s:
                    self.nwp_proc.process_forecasts()
                    self._last_run["nwp"] = now

                if now - self._last_run.get("accumulate", 0) >= self.accumulate_interval_s:
                    self.accumulator.process_all_stations(auto_generate_alerts=True)
                    self._last_run["accumulate"] = now

                time.sleep(10)
            except (KeyboardInterrupt, SystemExit):
                self.stop()
                break
            except Exception as e:
                logger.error("Unhandled error in scheduler loop: %s", e)
                time.sleep(10)

    def stop(self):
        """Stops the scheduler loop."""
        logger.info("Stopping Pipeline Scheduler...")
        self._running = False
