"""
Download/Ingest Numerical Weather Prediction (NWP) ECMWF/GFS Forecast Horizons.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_pipeline.processors.nwp_processor import NWPProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DownloadNWP")

def main():
    logger.info("Ingesting multi-horizon (1h-72h) NWP forecast grids...")
    proc = NWPProcessor()
    res = proc.process_all_stations(forecast_horizon_hours=72)
    logger.info(f"NWP ingestion completed: {res.get('processed_records', 0)} forecast steps processed.")

if __name__ == "__main__":
    main()
