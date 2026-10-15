"""
Download/Compute Multi-Horizon Rainfall Observations & Accumulations.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_pipeline.processors.rainfall_accumulator import RainfallAccumulator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DownloadRainfall")

def main():
    logger.info("Computing multi-horizon rainfall accumulations (1h..72h) and evaluating IMD warnings...")
    acc = RainfallAccumulator()
    res = acc.accumulate_all_stations()
    logger.info(f"Rainfall accumulation finished: {res.get('accumulations_computed', 0)} multi-horizon records computed.")

if __name__ == "__main__":
    main()
