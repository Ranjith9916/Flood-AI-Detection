"""
ml/preprocessing/create_features.py
Multi-Source Hydro-Meteorological Feature Engineering Pipeline.
Integrates:
1. Station weather observations & rolling rainfall accumulations (1h..72h)
2. Antecedent Precipitation Index (API-7, API-14)
3. Satellite precipitation & Radar reflectivity / rain-rates
4. NWP Multi-Horizon Forecasts (1h..72h)
5. Hydro-geomorphic layers (Elevation, Slope, Aspect, TWI, HAND)
6. LULC & SCS-CN Runoff Depth
7. Stream proximity & drainage density

Generates versioned, normalized Parquet and CSV datasets for ML training and real-time inference.
"""

import json
import logging
import math
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.weather import WeatherStation, WeatherObservation
from backend.app.models.rainfall import RainfallData
from geospatial.dem_processor import DEMProcessor
from geospatial.lulc_processor import LULCProcessor
from geospatial.drainage_network import DrainageNetworkAnalyzer
from ml.preprocessing.clean_weather import encode_cyclical_time

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extracts unified feature vectors for point locations and timesteps.
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        db_session: Optional[Session] = None,
    ):
        self.output_dir = Path(output_dir or "ml/data/features")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = db_session or SessionLocal()

        self.dem_proc = DEMProcessor()
        self.lulc_proc = LULCProcessor()
        self.drain_analyzer = DrainageNetworkAnalyzer()

    def compute_api(self, daily_rainfall_list: list[float], k: float = 0.85) -> float:
        """
        Computes Antecedent Precipitation Index (API):
        API = sum_{t=1}^{N} (k^t * P_t)
        where k is the soil moisture depletion factor (~0.85).
        """
        api = 0.0
        for t, rain in enumerate(daily_rainfall_list, start=1):
            api += (k ** t) * rain
        return round(api, 2)

    def extract_point_features(
        self,
        lat: float,
        lon: float,
        obs_time: datetime,
        station_code: str = "BLR_CENTRAL",
        recent_rain_1h: float = 0.0,
        recent_rain_3h: float = 0.0,
        recent_rain_6h: float = 0.0,
        recent_rain_12h: float = 0.0,
        recent_rain_24h: float = 0.0,
        recent_rain_48h: float = 0.0,
        recent_rain_72h: float = 0.0,
        temp_c: float = 24.0,
        humidity: float = 75.0,
        pressure_hpa: float = 1012.0,
        wind_speed_ms: float = 3.5,
        nwp_rain_24h: float = 10.0,
        radar_dbz: float = 20.0,
        satellite_precip_mm: float = 5.0,
    ) -> dict[str, Any]:
        """
        Generates full feature vector combining meteorological, satellite, radar, NWP, and geospatial variables.
        """
        # 1. Temporal cyclical features
        time_feats = encode_cyclical_time(obs_time)

        # 2. Static Geospatial features
        topo = self.dem_proc.sample_point(lat, lon)
        lulc = self.lulc_proc.sample_point(lat, lon)
        drain = self.drain_analyzer.compute_distance_to_stream(lat, lon)

        # 3. Hydro Runoff calculation
        cn = lulc["curve_number_amc2"]
        direct_runoff_24h = self.lulc_proc.calculate_runoff(recent_rain_24h, cn)
        direct_runoff_forecast = self.lulc_proc.calculate_runoff(nwp_rain_24h, cn)

        # 4. Synthesize API (Antecedent Precipitation Index proxy from 24h/48h/72h lags)
        p1 = recent_rain_24h
        p2 = max(0.0, recent_rain_48h - recent_rain_24h)
        p3 = max(0.0, recent_rain_72h - recent_rain_48h)
        api_3day = self.compute_api([p1, p2, p3], k=0.85)

        # 5. Non-linear interaction features
        # Inundation risk index proxy: (Runoff * TWI) / (HAND + 1)
        hand = topo["hand_m"]
        twi = topo["twi"]
        hydro_risk_index = round((direct_runoff_24h * twi) / (hand + 1.0), 3)

        return {
            # Meta
            "station_code": station_code,
            "latitude": lat,
            "longitude": lon,
            "observation_time": obs_time.isoformat(),
            # Temporal
            **time_feats,
            # Weather & Rain
            "rainfall_1h_mm": recent_rain_1h,
            "rainfall_3h_mm": recent_rain_3h,
            "rainfall_6h_mm": recent_rain_6h,
            "rainfall_12h_mm": recent_rain_12h,
            "rainfall_24h_mm": recent_rain_24h,
            "rainfall_48h_mm": recent_rain_48h,
            "rainfall_72h_mm": recent_rain_72h,
            "api_3day": api_3day,
            "temperature_c": temp_c,
            "humidity_percent": humidity,
            "pressure_hpa": pressure_hpa,
            "wind_speed_ms": wind_speed_ms,
            # Radar & Satellite
            "radar_reflectivity_dbz": radar_dbz,
            "satellite_precip_mm": satellite_precip_mm,
            # NWP Forecast
            "nwp_rain_24h_mm": nwp_rain_24h,
            # Topography
            "elevation_m": topo["elevation_m"],
            "slope_deg": topo["slope_deg"],
            "aspect_deg": topo["aspect_deg"],
            "flow_accumulation": topo["flow_accumulation"],
            "twi": twi,
            "hand_m": hand,
            # LULC & Hydrology
            "curve_number": cn,
            "impervious_pct": lulc["impervious_pct"],
            "direct_runoff_24h_mm": direct_runoff_24h,
            "direct_runoff_forecast_mm": direct_runoff_forecast,
            # Drainage Proximity
            "dist_to_stream_m": drain["dist_to_stream_m"],
            "drainage_density": drain["drainage_density_km_km2"],
            # Interaction
            "hydro_risk_index": hydro_risk_index,
        }

    def generate_synthetic_training_dataset(
        self,
        n_samples: int = 1200,
        random_state: int = 42,
    ) -> pd.DataFrame:
        """
        Generates comprehensive historical training dataset with realistic meteorology,
        extreme monsoon events, topographic sampling, and physically derived labels:
        - heavy_rain_label (0/1): rainfall_24h >= 64.5 mm
        - flood_risk_label (0/1): based on rainfall, runoff, TWI, HAND, and stream distance
        - inundation_depth_m: continuous estimated water depth in meters
        """
        np.random.seed(random_state)
        logger.info("Generating %d synthetic historical training samples for ML...", n_samples)

        # Baseline coordinates across South India / Bangalore basin
        st_coords = [
            ("BLR_CENTRAL", 12.9716, 77.5946),
            ("BLR_AIRPORT", 13.1986, 77.7066),
            ("BLR_SOUTH",   12.8900, 77.5800),
            ("BLR_EAST",    12.9698, 77.7500),
            ("BLR_WEST",    12.9600, 77.5200),
        ]

        rows = []
        base_date = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)

        for i in range(n_samples):
            code, lat, lon = st_coords[i % len(st_coords)]
            # Add small spatial jitter
            lat_j = lat + np.random.uniform(-0.04, 0.04)
            lon_j = lon + np.random.uniform(-0.04, 0.04)

            # Sample temporal timestep across monsoon & non-monsoon
            dt = base_date + timedelta(hours=i * 6)
            is_monsoon = dt.month in [6, 7, 8, 9, 10]

            # Realistic rainfall distribution: mix of dry days, light rain, and extreme convective storms
            is_storm = np.random.rand() < (0.25 if is_monsoon else 0.05)
            if is_storm:
                rain_24h = float(np.random.gamma(shape=4.0, scale=25.0)) # 30 - 200 mm
                rain_1h = float(min(rain_24h, np.random.uniform(10.0, 65.0)))
                rain_3h = float(min(rain_24h, rain_1h + np.random.uniform(5.0, 30.0)))
                rain_6h = float(min(rain_24h, rain_3h + np.random.uniform(5.0, 20.0)))
                rain_12h = float(min(rain_24h, rain_6h + np.random.uniform(5.0, 20.0)))
                rain_48h = float(rain_24h + np.random.uniform(5.0, 60.0))
                rain_72h = float(rain_48h + np.random.uniform(0.0, 40.0))
                dbz = float(np.clip(30.0 + (rain_1h * 0.8), 25.0, 65.0))
                nwp_rain = float(rain_24h * np.random.uniform(0.7, 1.3))
                sat_precip = float(rain_24h * np.random.uniform(0.8, 1.2))
                temp = float(np.random.uniform(19.0, 24.0))
                hum = float(np.random.uniform(85.0, 98.0))
                press = float(np.random.uniform(900.0, 915.0))
                wind = float(np.random.uniform(6.0, 18.0))
            else:
                rain_24h = float(np.random.exponential(scale=3.0) if np.random.rand() < 0.3 else 0.0)
                rain_1h = float(min(rain_24h, np.random.exponential(scale=1.0)))
                rain_3h = float(min(rain_24h, rain_1h * 1.5))
                rain_6h = float(min(rain_24h, rain_3h * 1.2))
                rain_12h = float(min(rain_24h, rain_6h * 1.1))
                rain_48h = float(rain_24h + np.random.exponential(scale=2.0))
                rain_72h = float(rain_48h + np.random.exponential(scale=1.5))
                dbz = float(np.clip(10.0 + rain_1h * 2.0, 0.0, 28.0))
                nwp_rain = float(max(0.0, np.random.exponential(scale=4.0)))
                sat_precip = float(rain_24h * np.random.uniform(0.7, 1.1))
                temp = float(np.random.uniform(22.0, 34.0))
                hum = float(np.random.uniform(40.0, 75.0))
                press = float(np.random.uniform(912.0, 925.0))
                wind = float(np.random.uniform(1.5, 6.5))

            feat = self.extract_point_features(
                lat=lat_j,
                lon=lon_j,
                obs_time=dt,
                station_code=code,
                recent_rain_1h=round(rain_1h, 2),
                recent_rain_3h=round(rain_3h, 2),
                recent_rain_6h=round(rain_6h, 2),
                recent_rain_12h=round(rain_12h, 2),
                recent_rain_24h=round(rain_24h, 2),
                recent_rain_48h=round(rain_48h, 2),
                recent_rain_72h=round(rain_72h, 2),
                temp_c=round(temp, 1),
                humidity=round(hum, 1),
                pressure_hpa=round(press, 1),
                wind_speed_ms=round(wind, 1),
                nwp_rain_24h=round(nwp_rain, 2),
                radar_dbz=round(dbz, 1),
                satellite_precip_mm=round(sat_precip, 2),
            )

            # --- Target Variables (Ground Truth Synthesis) ---
            # 1. Heavy rain target (IMD definition: >= 64.5 mm in 24h)
            heavy_rain_target = 1 if rain_24h >= 64.5 else 0

            # 2. Flood event probability & occurrence
            # Physically grounded: driven by direct runoff, low HAND, high TWI, proximity to stream, high imperviousness
            hand_val = feat["hand_m"]
            twi_val = feat["twi"]
            runoff_val = feat["direct_runoff_24h_mm"]
            dist_stream = feat["dist_to_stream_m"]
            imperv = feat["impervious_pct"] / 100.0

            # Physical flood risk logit
            flood_logit = (
                0.045 * runoff_val
                + 0.18 * twi_val
                - 0.35 * hand_val
                - 0.0008 * min(dist_stream, 3000.0)
                + 1.2 * imperv
                - 2.8
            )
            flood_prob = 1.0 / (1.0 + math.exp(-np.clip(flood_logit, -10.0, 10.0)))
            flood_occurred = 1 if flood_prob >= 0.50 else 0

            # 3. Inundation depth in meters
            if flood_occurred:
                # Water depth proportional to runoff excess over HAND depression
                depth = max(0.05, (runoff_val / 80.0) * math.exp(-hand_val / 3.0) + (twi_val / 20.0) * 0.3)
                depth = round(min(depth, 3.5), 2)
            else:
                depth = 0.0

            feat["target_heavy_rain"] = heavy_rain_target
            feat["target_flood_prob"] = round(flood_prob, 3)
            feat["target_flood_occurred"] = flood_occurred
            feat["target_inundation_depth_m"] = depth

            rows.append(feat)

        df = pd.DataFrame(rows)

        # Save to Parquet and CSV
        csv_path = self.output_dir / "flood_training_dataset.csv"
        parquet_path = self.output_dir / "flood_training_dataset.parquet"

        df.to_csv(csv_path, index=False)
        try:
            df.to_parquet(parquet_path, index=False)
        except Exception as e:
            logger.warning("Could not save parquet format (fastparquet/pyarrow): %s", e)

        meta = {
            "num_samples": len(df),
            "num_features": len(df.columns) - 4,
            "feature_names": [c for c in df.columns if not c.startswith("target_")],
            "targets": ["target_heavy_rain", "target_flood_prob", "target_flood_occurred", "target_inundation_depth_m"],
            "class_distribution_heavy_rain": int(df["target_heavy_rain"].sum()),
            "class_distribution_flood": int(df["target_flood_occurred"].sum()),
            "mean_inundation_depth_m": float(df["target_inundation_depth_m"].mean()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(self.output_dir / "dataset_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        logger.info(
            "Dataset successfully created: %d samples, %d heavy rain events, %d flood events saved to %s",
            len(df), meta["class_distribution_heavy_rain"], meta["class_distribution_flood"], self.output_dir,
        )
        return df


def main():
    extractor = FeatureExtractor()
    df = extractor.generate_synthetic_training_dataset(n_samples=1500)
    print("==================================================")
    print(" FEATURE STORE & DATASET GENERATION SUCCESS")
    print("==================================================")
    print(f"Total Rows: {len(df)}")
    print(f"Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"Heavy Rain Cases: {df['target_heavy_rain'].sum()} / {len(df)}")
    print(f"Flood Occurrence Cases: {df['target_flood_occurred'].sum()} / {len(df)}")
    print(f"Max Inundation Depth: {df['target_inundation_depth_m'].max()} m")
    print("==================================================")


if __name__ == "__main__":
    main()
