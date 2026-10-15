"""
Preprocess All Hydro-Geospatial and Meteorological Data Script.
Executes DEM, LULC, Drainage Network, and Unified Feature Store Generation.
"""
import sys
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from geospatial.dem_processor import DEMProcessor
from geospatial.lulc_processor import LULCProcessor
from geospatial.drainage_network import DrainageNetworkAnalyzer
from ml.preprocessing.create_features import FeatureStoreBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PreprocessAll")

def main():
    logger.info("================================================================================")
    logger.info("  FLOOD-AI: Preprocessing All Geospatial, Hydrological & Meteorological Data   ")
    logger.info("================================================================================")
    
    # 1. DEM Processing
    logger.info("[Step 1/4] Running Hydro-Geomorphic DEM Derivative Processor...")
    dem = DEMProcessor()
    grid = dem.generate_synthetic_elevation_grid(bounds=(12.80, 80.00, 13.25, 80.35), resolution=100)
    dem_metrics = dem.calculate_derivatives(grid)
    logger.info(f"DEM processed successfully: Grid shape {grid.shape}, TWI mean: {dem_metrics['twi'].mean():.2f}")
    
    # 2. LULC & SCS-CN Runoff
    logger.info("[Step 2/4] Running Land-Use/Land-Cover & USDA SCS-CN Direct Runoff Model...")
    lulc = LULCProcessor()
    lulc_grid = lulc.generate_synthetic_lulc_grid(bounds=(12.80, 80.00, 13.25, 80.35), resolution=100)
    cn_grid = lulc.calculate_curve_number(lulc_grid, amc_condition="AMC-II")
    runoff_depth = lulc.calculate_direct_runoff(rainfall_mm=100.0, curve_number=cn_grid)
    logger.info(f"LULC & SCS-CN calculated: Mean Curve Number = {cn_grid.mean():.1f}, Runoff for 100mm = {runoff_depth.mean():.2f} mm")
    
    # 3. Drainage Network & Catchment Channels
    logger.info("[Step 3/4] Extracting Catchment Drainage Network & Distance-to-Stream...")
    drainage = DrainageNetworkAnalyzer()
    streams = drainage.extract_synthetic_stream_network(bounds=(12.80, 80.00, 13.25, 80.35))
    logger.info(f"Drainage network generated: {len(streams)} primary river reaches analyzed.")
    
    # 4. Multi-Source Feature Store
    logger.info("[Step 4/4] Building Multi-Horizon Multi-Source ML Feature Store (Parquet & CSV)...")
    builder = FeatureStoreBuilder()
    df = builder.build_dataset(num_samples=1500)
    csv_path, parquet_path = builder.save(df)
    logger.info(f"Feature store successfully generated: {len(df)} samples, {len(df.columns)} features.")
    logger.info(f"  CSV: {csv_path}")
    logger.info(f"  Parquet: {parquet_path}")
    logger.info("================================================================================")
    logger.info("  All Preprocessing Completed Successfully!                                     ")
    logger.info("================================================================================")

if __name__ == "__main__":
    main()
