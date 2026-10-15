"""
Download/Process Digital Elevation Model (DEM) and Topographic Indices.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from geospatial.dem_processor import DEMProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DownloadDEM")

def main():
    logger.info("Processing Digital Elevation Models (DEM) & Topographic Wetness Index (TWI)...")
    proc = DEMProcessor()
    grid = proc.generate_synthetic_elevation_grid(bounds=(12.80, 80.00, 13.25, 80.35), resolution=100)
    derivs = proc.calculate_derivatives(grid)
    logger.info(f"DEM derivatives successfully computed for grid shape {grid.shape}.")
    logger.info(f"  Elevation Min/Max: {grid.min():.1f}m / {grid.max():.1f}m")
    logger.info(f"  Slope Mean: {derivs['slope'].mean():.2f} deg, TWI Mean: {derivs['twi'].mean():.2f}")

if __name__ == "__main__":
    main()
