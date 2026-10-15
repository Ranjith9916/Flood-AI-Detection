"""
Run End-to-End Prediction & Early Warning Risk Evaluation Script.
Executes the unified RiskEngine across all 4 machine learning inference models.
"""
import sys
import json
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.inference.risk_engine import RiskEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("RunPrediction")

def main():
    logger.info("================================================================================")
    logger.info("  FLOOD-AI: Executing End-to-End Risk Engine & Early Warning Assessment        ")
    logger.info("================================================================================")
    
    engine = RiskEngine()
    
    # Sample multi-horizon hydro-meteorological scenario (Heavy Monsoon Event)
    sample_scenario = {
        "temperature_c": 28.5,
        "relative_humidity_pct": 94.0,
        "wind_speed_ms": 16.5,
        "surface_pressure_hpa": 995.0,
        "rainfall_rate_mmh": 42.0,
        "rainfall_1h_mm": 42.0,
        "rainfall_3h_mm": 88.0,
        "rainfall_6h_mm": 135.0,
        "rainfall_12h_mm": 178.0,
        "rainfall_24h_mm": 235.0,
        "rainfall_48h_mm": 290.0,
        "rainfall_72h_mm": 320.0,
        "satellite_precip_mm": 44.5,
        "radar_reflectivity_dbz": 48.0,
        "nwp_precip_1h_mm": 38.0,
        "nwp_precip_3h_mm": 80.0,
        "nwp_precip_6h_mm": 125.0,
        "nwp_precip_12h_mm": 160.0,
        "nwp_precip_24h_mm": 210.0,
        "elevation_m": 8.5,
        "slope_deg": 1.2,
        "flow_accumulation": 125000.0,
        "twi": 12.8,
        "hand_m": 0.8,
        "curve_number": 88.0,
        "scs_runoff_depth_mm": 195.0,
        "distance_to_stream_m": 120.0,
        "drainage_density_km_km2": 3.8
    }
    
    logger.info("Scenario inputs: 24h Rainfall = 235 mm, Radar Reflectivity = 48 dBZ, TWI = 12.8, HAND = 0.8m")
    
    assessment = engine.evaluate(sample_scenario)
    
    logger.info("\n--- AI/ML RISK ENGINE INFERENCE ASSESSMENT ---")
    print(json.dumps(assessment, indent=2))
    
    logger.info("================================================================================")
    logger.info(f"  Overall Risk Level: {assessment.get('overall_risk_level', 'UNKNOWN').upper()} | Alert Color: {assessment.get('alert_color', 'GREEN')}")
    logger.info(f"  Inundation Depth: {assessment.get('inundation_depth_m', 0.0):.2f} meters | Flood Probability: {assessment.get('flood_probability', 0.0):.1%}")
    logger.info("================================================================================")

if __name__ == "__main__":
    main()
