"""
Download/Ingest NASA GPM IMERG Satellite Precipitation Data.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_pipeline.processors.satellite_processor import SatelliteProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DownloadSatellite")

def main():
    logger.info("Ingesting NASA GPM IMERG satellite precipitation rasters...")
    proc = SatelliteProcessor()
    res = proc.process_current(lookback_hours=6)
    logger.info(f"Satellite ingestion completed: {res.get('processed_records', 0)} raster frames ingested.")

if __name__ == "__main__":
    main()
