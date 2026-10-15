"""
Download/Ingest Doppler Weather Radar (DWR) Volume Scans & Reflectivity.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_pipeline.processors.radar_processor import RadarProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DownloadRadar")

def main():
    logger.info("Ingesting Doppler Weather Radar (DWR) sweeps and calculating Marshall-Palmer rain rates...")
    proc = RadarProcessor()
    res = proc.process_current(lookback_hours=3)
    logger.info(f"Radar ingestion completed: {res.get('processed_records', 0)} scans ingested.")

if __name__ == "__main__":
    main()
