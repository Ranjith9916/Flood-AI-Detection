"""
ml/inference/risk_engine.py
Integrated AI Risk Engine.
Executes the full inference pipeline across all active ML models:
1. Gathers current observations, accumulations, and NWP forecasts from database
2. Builds dynamic feature vectors using FeatureExtractor
3. Runs Heavy Rain, Rainfall Forecast, Flood Probability, and Inundation Depth models
4. Saves predictions to flood_predictions and inundation_predictions tables
5. Generates multi-level alerts for emergency warning management
"""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.alert import Alert
from backend.app.models.flood import FloodPrediction
from backend.app.models.inundation import InundationPrediction
from backend.app.models.weather import WeatherStation
from data_pipeline.processors.rainfall_accumulator import RainfallAccumulator
from ml.inference.flood_predictor import FloodPredictor
from ml.inference.heavy_rain_predictor import HeavyRainPredictor
from ml.inference.inundation_predictor import InundationPredictor
from ml.inference.rainfall_predictor import RainfallPredictor
from ml.preprocessing.create_features import FeatureExtractor

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Unified real-time early warning and inundation risk prediction engine.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self._external_session = db_session
        self.extractor = FeatureExtractor()
        self.accumulator = RainfallAccumulator(db_session=db_session)

        self.heavy_rain_model = HeavyRainPredictor()
        self.rainfall_model = RainfallPredictor()
        self.flood_model = FloodPredictor()
        self.inundation_model = InundationPredictor()

    def get_session(self) -> Session:
        if self._external_session:
            return self._external_session
        return SessionLocal()

    def evaluate(self, features: dict[str, Any]) -> dict[str, Any]:
        """
        Runs full inference stack directly on an arbitrary feature dictionary.
        """
        heavy_rain_res = self.heavy_rain_model.predict([features])[0]
        rainfall_res = self.rainfall_model.predict([features])[0]
        flood_res = self.flood_model.predict([features])[0]
        inundation_res = self.inundation_model.predict([features])[0]

        # Determine overall alert color
        risk = flood_res.get("risk_level", "LOW")
        color_map = {
            "LOW": "GREEN",
            "MODERATE": "YELLOW",
            "HIGH": "ORANGE",
            "VERY_HIGH": "RED",
            "EXTREME": "RED"
        }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "heavy_rain_prediction": heavy_rain_res,
            "rainfall_forecast": rainfall_res,
            "flood_risk": flood_res,
            "inundation_prediction": inundation_res,
            "overall_risk_level": risk,
            "alert_color": color_map.get(risk, "GREEN"),
            "flood_probability": flood_res.get("flood_probability", 0.0),
            "inundation_depth_m": inundation_res.get("estimated_depth_m", 0.0),
        }

    def run_station_inference(
        self,
        station_code: str,
        lat: float,
        lon: float,
        as_of_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Runs full inference stack for a single station point.
        """
        if not as_of_time:
            as_of_time = datetime.now(timezone.utc)

        valid_time = as_of_time + timedelta(hours=24)

        # 1. Fetch live accumulations
        acc = self.accumulator.calculate_station_accumulations(station_code, as_of_time)

        # 2. Extract feature vector
        feat_dict = self.extractor.extract_point_features(
            lat=lat,
            lon=lon,
            obs_time=as_of_time,
            station_code=station_code,
            recent_rain_1h=acc.get("1h", 0.0),
            recent_rain_3h=acc.get("3h", 0.0),
            recent_rain_6h=acc.get("6h", 0.0),
            recent_rain_12h=acc.get("12h", 0.0),
            recent_rain_24h=acc.get("24h", 0.0),
            recent_rain_48h=acc.get("48h", 0.0),
            recent_rain_72h=acc.get("72h", 0.0),
        )

        # 3. Predict across all 4 models
        heavy_rain_res = self.heavy_rain_model.predict([feat_dict])[0]
        rainfall_res = self.rainfall_model.predict([feat_dict])[0]
        flood_res = self.flood_model.predict([feat_dict])[0]
        inundation_res = self.inundation_model.predict([feat_dict])[0]

        # 4. Save to Database
        session = self.get_session()
        try:
            # Save Flood Prediction
            flood_pred = FloodPrediction(
                id=uuid.uuid4(),
                prediction_time=as_of_time,
                forecast_valid_time=valid_time,
                latitude=lat,
                longitude=lon,
                flood_probability=flood_res["flood_probability"],
                risk_level=flood_res["risk_level"],
                model_name="flood_probability_classifier",
                model_version="1.0.0",
                feature_version="1.0.0",
                data_sources=json.dumps(["STATION", "GPM_IMERG", "RADAR", "NWP", "DEM_HYDRO"]),
            )
            session.add(flood_pred)

            # Save Inundation Prediction
            inund_pred = InundationPrediction(
                id=uuid.uuid4(),
                prediction_time=as_of_time,
                forecast_valid_time=valid_time,
                affected_area_km2=0.25 if inundation_res["is_inundated"] else 0.0,
                maximum_depth_m=inundation_res["estimated_depth_m"],
                mean_depth_m=round(inundation_res["estimated_depth_m"] * 0.6, 2),
                min_lat=lat - 0.02,
                max_lat=lat + 0.02,
                min_lon=lon - 0.02,
                max_lon=lon + 0.02,
                model_confidence=0.92,
                inference_status="COMPLETE",
                model_name="inundation_depth_predictor",
                model_version="1.0.0",
                feature_version="1.0.0",
                notes=f"Station {station_code}: Forecast 24h rain {rainfall_res['forecast_rainfall_24h_mm']} mm",
            )
            session.add(inund_pred)

            # 5. Generate Alert if high risk or heavy rain expected
            if flood_res["risk_level"] in ["HIGH", "VERY_HIGH", "EXTREME"] or heavy_rain_res["heavy_rain_predicted"]:
                severity = "CRITICAL" if flood_res["risk_level"] in ["VERY_HIGH", "EXTREME"] else "HIGH"
                alert = Alert(
                    id=uuid.uuid4(),
                    alert_type="FLOOD_WARNING" if flood_res["is_flood_expected"] else "HEAVY_RAIN_WARNING",
                    severity=severity,
                    title=f"{flood_res['risk_level']} Risk Alert: {station_code}",
                    description=(
                        f"AI Prediction for {station_code} (Lat {lat:.4f}, Lon {lon:.4f}): "
                        f"Flood Probability: {flood_res['flood_probability']*100:.1f}%, "
                        f"Forecast 24h Rain: {rainfall_res['forecast_rainfall_24h_mm']:.1f} mm, "
                        f"Est. Inundation Depth: {inundation_res['estimated_depth_m']:.2f} m."
                    ),
                    is_active=True,
                    created_at=as_of_time,
                    expires_at=as_of_time + timedelta(hours=24),
                )
                session.add(alert)

            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Failed to save predictions/alerts for %s: %s", station_code, exc)
            raise
        finally:
            if not self._external_session:
                session.close()

        return {
            "station_code": station_code,
            "latitude": lat,
            "longitude": lon,
            "prediction_time": as_of_time.isoformat(),
            "heavy_rain": heavy_rain_res,
            "rainfall_forecast": rainfall_res,
            "flood_risk": flood_res,
            "inundation": inundation_res,
        }

    def run_all_stations(self, as_of_time: Optional[datetime] = None) -> list[dict[str, Any]]:
        """
        Runs predictions for all registered weather observation stations.
        """
        if not as_of_time:
            as_of_time = datetime.now(timezone.utc)

        session = self.get_session()
        stations = []
        try:
            st_records = session.query(WeatherStation).all()
            for s in st_records:
                stations.append({
                    "code": s.station_code,
                    "lat": s.latitude,
                    "lon": s.longitude,
                })
        finally:
            if not self._external_session:
                session.close()

        results = []
        for st in stations:
            res = self.run_station_inference(
                station_code=st["code"],
                lat=st["lat"],
                lon=st["lon"],
                as_of_time=as_of_time,
            )
            results.append(res)

        logger.info("Executed risk inference across %d stations.", len(results))
        return results


def main():
    engine = RiskEngine()
    results = engine.run_all_stations()
    print("==================================================")
    print(" AI/ML RISK ENGINE INFERENCE EXECUTION")
    print("==================================================")
    for r in results:
        print(f"Station: {r['station_code']:<15} Flood Prob: {r['flood_risk']['flood_probability']*100:>5.1f}%  "
              f"Risk: {r['flood_risk']['risk_level']:<10} Rain Fcst: {r['rainfall_forecast']['forecast_rainfall_24h_mm']:>5.1f} mm "
              f"Inundation: {r['inundation']['estimated_depth_m']:>4.2f} m")
    print("==================================================")


if __name__ == "__main__":
    main()
