"""
ml/training/inundation/train_segmentation.py
Trains and registers Inundation Depth & Extent Models (Gradient Boosting Regressor).
Predicts continuous water depth (meters) across topographic depression zones.
Logs model version and metrics to PostgreSQL model_registry.
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
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from backend.app.core.database import SessionLocal
from backend.app.models.pipeline import ModelMetric, ModelRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("train_inundation_model")

INUNDATION_FEATURES = [
    "rainfall_1h_mm", "rainfall_6h_mm", "rainfall_24h_mm", "rainfall_48h_mm",
    "elevation_m", "slope_deg", "flow_accumulation", "twi", "hand_m",
    "curve_number", "impervious_pct", "direct_runoff_24h_mm",
    "dist_to_stream_m", "drainage_density", "hydro_risk_index",
]
TARGET_COL = "target_inundation_depth_m"


def train_inundation_model(data_path: str = "ml/data/features/flood_training_dataset.csv", output_dir: str = "ml/models/inundation"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info("Loading dataset from %s...", data_path)
    df = pd.read_csv(data_path)

    X = df[INUNDATION_FEATURES]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    logger.info("Training Inundation Depth Gradient Boosting Regressor...")
    model = GradientBoostingRegressor(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.85,
        random_state=42,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0.0, None)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    # Binary extent IoU (Intersection over Union for flooded pixels > 0.05m)
    actual_flooded = (y_test > 0.05)
    pred_flooded = (y_pred > 0.05)
    intersection = np.logical_and(actual_flooded, pred_flooded).sum()
    union = np.logical_or(actual_flooded, pred_flooded).sum()
    iou = float(intersection / max(union, 1))

    logger.info("Inundation Model Test Metrics: RMSE=%.3f m, MAE=%.3f m, R2=%.3f, Extent IoU=%.3f", rmse, mae, r2, iou)

    # Save artifact
    model_filename = "gb_inundation_depth_v1.joblib"
    model_file_path = out_path / model_filename
    joblib.dump(
        {
            "model": model,
            "feature_names": INUNDATION_FEATURES,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        },
        model_file_path,
    )

    # Register in PostgreSQL
    session = SessionLocal()
    model_id = uuid.uuid4()
    try:
        session.query(ModelRegistry).filter(ModelRegistry.model_name == "inundation_depth_predictor").update({"is_active": False})

        reg = ModelRegistry(
            id=model_id,
            model_name="inundation_depth_predictor",
            model_version="1.0.0",
            model_type="GradientBoostingRegressor",
            training_dataset_version="v1.0",
            feature_version="v1.0",
            target_variable="inundation_depth_meters",
            training_date=datetime.now(timezone.utc),
            file_path=str(model_file_path),
            is_active=True,
            is_development=False,
            metadata_json=json.dumps({"features": INUNDATION_FEATURES, "n_samples": len(df)}),
        )
        session.add(reg)

        for m_name, m_val in [("rmse", rmse), ("mae", mae), ("r2_score", r2), ("extent_iou", iou)]:
            session.add(ModelMetric(
                id=uuid.uuid4(),
                model_id=model_id,
                metric_name=m_name,
                metric_value=m_val,
                dataset_split="test",
                evaluation_date=datetime.now(timezone.utc),
            ))

        session.commit()
        logger.info("Inundation model registered in DB with ID %s", model_id)
    except Exception as e:
        session.rollback()
        logger.error("DB registration failed: %s", e)
    finally:
        session.close()

    return {"model_id": str(model_id), "model_file": str(model_file_path), "metrics": {"rmse": rmse, "mae": mae, "iou": iou}}


if __name__ == "__main__":
    train_inundation_model()
