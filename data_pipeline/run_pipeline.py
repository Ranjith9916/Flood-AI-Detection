"""
data_pipeline/run_pipeline.py
Production CLI runner for the Flood AI Integrated Ingestion Pipeline.
Supports running individual sources, all sources, batch backfills, and continuous scheduler mode.
"""

import argparse
import logging
import sys
from datetime import datetime, timezone, timedelta

from data_pipeline.processors.weather_processor import WeatherProcessor, DEFAULT_STATIONS
from data_pipeline.processors.satellite_processor import SatelliteProcessor
from data_pipeline.processors.radar_processor import RadarProcessor
from data_pipeline.processors.nwp_processor import NwpProcessor
from data_pipeline.processors.rainfall_accumulator import RainfallAccumulator
from data_pipeline.schedulers.pipeline_scheduler import PipelineScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline_cli")


def run_weather(days: int = 1, station_code: str = None):
    print("--------------------------------------------------")
    print(" Running Weather Ingestion Pipeline")
    print("--------------------------------------------------")
    proc = WeatherProcessor()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    stations = DEFAULT_STATIONS
    if station_code:
        stations = [s for s in DEFAULT_STATIONS if s["code"] == station_code]
        if not stations:
            stations = [{"code": station_code, "name": f"Station {station_code}", "lat": 12.9716, "lon": 77.5946}]

    res = proc.process_stations(stations=stations, start_date=start_date, end_date=end_date)
    print(f"Status: {res['status']}")
    print(f"Stations Processed: {res['stations_processed']}")
    print(f"Records Received: {res['records_received']}")
    print(f"Records Inserted: {res['records_inserted']}")
    print(f"Pipeline Run ID: {res['pipeline_run_id']}")


def run_satellite(days: int = 1):
    print("--------------------------------------------------")
    print(" Running Satellite Precipitation Ingestion")
    print("--------------------------------------------------")
    proc = SatelliteProcessor()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    res = proc.process(start_time=start_date, end_time=end_date)
    print(f"Status: {res['status']}")
    print(f"Records Received: {res['records_received']}")
    print(f"Records Inserted: {res['records_inserted']}")
    print(f"Pipeline Run ID: {res['pipeline_run_id']}")


def run_radar(hours: int = 6):
    print("--------------------------------------------------")
    print(" Running Weather Radar (DWR) Ingestion")
    print("--------------------------------------------------")
    proc = RadarProcessor()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=hours)
    res = proc.process(start_time=start_date, end_time=end_date)
    print(f"Status: {res['status']}")
    print(f"Scans Processed: {res['records_received']}")
    print(f"Records Inserted: {res['records_inserted']}")
    print(f"Pipeline Run ID: {res['pipeline_run_id']}")


def run_nwp(forecast_days: int = 3):
    print("--------------------------------------------------")
    print(" Running NWP Forecast Ingestion")
    print("--------------------------------------------------")
    proc = NwpProcessor()
    res = proc.process_forecasts(forecast_days=forecast_days)
    print(f"Status: {res['status']}")
    print(f"Points Processed: {res['points_processed']}")
    print(f"Forecast Horizons Stored: {res['records_inserted']}")
    print(f"Pipeline Run ID: {res['pipeline_run_id']}")


def run_accumulation():
    print("--------------------------------------------------")
    print(" Running Rainfall Accumulation & Alert Engine")
    print("--------------------------------------------------")
    acc = RainfallAccumulator()
    res = acc.process_all_stations(auto_generate_alerts=True)
    print(f"Processed {len(res)} stations:")
    for st in res:
        print(f"  Station: {st['station_code']:<15} 24h Rain: {st['rainfall_24h_mm']:>6.1f} mm  Category: {st['category']}")


def main():
    parser = argparse.ArgumentParser(description="Flood AI Data Ingestion Pipeline CLI")
    parser.add_argument(
        "--source",
        choices=["all", "weather", "satellite", "radar", "nwp", "accumulate"],
        default="all",
        help="Data source pipeline to execute",
    )
    parser.add_argument("--station", type=str, default=None, help="Filter to specific station code")
    parser.add_argument("--days", type=int, default=1, help="Number of past days to ingest (default: 1)")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in background scheduler mode")

    args = parser.parse_args()

    print("==================================================")
    print(" FLOOD AI INTEGRATED DATA PIPELINE")
    print("==================================================")

    if args.daemon:
        print("Starting continuous background scheduler...")
        scheduler = PipelineScheduler()
        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.stop()
            print("Scheduler stopped.")
        return

    if args.source in ["all", "weather"]:
        run_weather(days=args.days, station_code=args.station)

    if args.source in ["all", "satellite"]:
        run_satellite(days=args.days)

    if args.source in ["all", "radar"]:
        run_radar(hours=min(args.days * 24, 24))

    if args.source in ["all", "nwp"]:
        run_nwp(forecast_days=3)

    if args.source in ["all", "accumulate"]:
        run_accumulation()

    print("==================================================")
    print(" Pipeline execution finished successfully.")
    print("==================================================")


if __name__ == "__main__":
    main()