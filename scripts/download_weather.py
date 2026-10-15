"""
Download/Ingest Real-time Weather Station Observations.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_pipeline.processors.weather_processor import WeatherProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DownloadWeather")

def main():
    logger.info("Ingesting ground weather station observations...")
    proc = WeatherProcessor()
    res = proc.process_all_stations(lookback_days=2)
    logger.info(f"Ingestion finished: {res.get('processed_records', 0)} records processed across {res.get('stations_count', 0)} stations.")

if __name__ == "__main__":
    main()
