"""
ml/training/rainfall/train_xgboost.py
Trains and registers Rainfall Forecaster Regression Models (XGBoost Regressor).
Predicts future accumulated rainfall depth (mm) from atmospheric & antecedent signals.
Logs model metrics (RMSE, MAE, R2) to PostgreSQL model_registry.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from backend.app.core.database import SessionLocal
from backend.app.models.pipeline import ModelMetric, ModelRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("train_rainfall_xgboost")

RAINFALL_REG_FEATURES = [
    "hour_sin", "hour_cos", "doy_sin", "doy_cos",
    "rainfall_1h_mm", "rainfall_3h_mm", "rainfall_6h_mm", "rainfall_12h_mm",
    "api_3day", "temperature_c", "humidity_percent", "pressure_hpa", "wind_speed_ms",
    "radar_reflectivity_dbz", "satellite_precip_mm", "nwp_rain_24h_mm",
    "elevation_m", "slope_deg",
]
TARGET_COL = "rainfall_24h_mm"


def train_rainfall_regressor(data_path: str = "ml/data/features/flood_training_dataset.csv", output_dir: str = "ml/models/rainfall"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info("Loading training dataset from %s...", data_path)
    df = pd.read_csv(data_path)

    X = df[RAINFALL_REG_FEATURES]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    logger.info("Training XGBoost Rainfall Regressor...")
    model = XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0.0, None)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    logger.info("Rainfall Model Evaluation: RMSE=%.2f mm, MAE=%.2f mm, R2=%.3f", rmse, mae, r2)

    # Save artifact
    model_filename = "xgb_rainfall_regressor_v1.joblib"
    model_file_path = out_path / model_filename
    joblib.dump(
        {
            "model": model,
            "feature_names": RAINFALL_REG_FEATURES,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        },
        model_file_path,
    )

    # Register in DB
    session = SessionLocal()
    model_id = uuid.uuid4()
    try:
        session.query(ModelRegistry).filter(ModelRegistry.model_name == "rainfall_forecast_xgb").update({"is_active": False})

        reg = ModelRegistry(
            id=model_id,
            model_name="rainfall_forecast_xgb",
            model_version="1.0.0",
            model_type="XGBRegressor",
            training_dataset_version="v1.0",
            feature_version="v1.0",
            target_variable="rainfall_24h_accumulation_mm",
            training_date=datetime.now(timezone.utc),
            file_path=str(model_file_path),
            is_active=True,
            is_development=False,
            metadata_json=json.dumps({"features": RAINFALL_REG_FEATURES, "n_samples": len(df)}),
        )
        session.add(reg)

        for m_name, m_val in [("rmse", rmse), ("mae", mae), ("r2_score", r2)]:
            session.add(ModelMetric(
                id=uuid.uuid4(),
                model_id=model_id,
                metric_name=m_name,
                metric_value=m_val,
                dataset_split="test",
                evaluation_date=datetime.now(timezone.utc),
            ))

        session.commit()
        logger.info("Rainfall Forecast model registered in DB with ID %s", model_id)
    except Exception as e:
        session.rollback()
        logger.error("DB registration failed: %s", e)
    finally:
        session.close()

    return {"model_id": str(model_id), "model_file": str(model_file_path), "metrics": {"rmse": rmse, "mae": mae, "r2": r2}}


if __name__ == "__main__":
    train_rainfall_regressor()
