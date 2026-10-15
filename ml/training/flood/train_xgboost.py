"""
ml/training/flood/train_xgboost.py
Trains and registers Flood Probability & Risk Prediction Models (XGBoost).
Predicts calibrated probability of localized flood inundation events from hydro-meteorological features.
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
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from backend.app.core.database import SessionLocal
from backend.app.models.pipeline import ModelMetric, ModelRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("train_flood_xgboost")

FLOOD_FEATURE_COLS = [
    "rainfall_1h_mm", "rainfall_3h_mm", "rainfall_6h_mm", "rainfall_12h_mm", "rainfall_24h_mm",
    "rainfall_48h_mm", "rainfall_72h_mm", "api_3day",
    "radar_reflectivity_dbz", "satellite_precip_mm", "nwp_rain_24h_mm",
    "elevation_m", "slope_deg", "flow_accumulation", "twi", "hand_m",
    "curve_number", "impervious_pct", "direct_runoff_24h_mm", "direct_runoff_forecast_mm",
    "dist_to_stream_m", "drainage_density", "hydro_risk_index",
]
TARGET_COL = "target_flood_occurred"


def train_flood_model(data_path: str = "ml/data/features/flood_training_dataset.csv", output_dir: str = "ml/models/flood"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info("Loading training features from %s...", data_path)
    df = pd.read_csv(data_path)

    X = df[FLOOD_FEATURE_COLS]
    y = df[TARGET_COL]

    neg_count = int((y == 0).sum())
    pos_count = int((y == 1).sum())
    scale_weight = float(neg_count / max(pos_count, 1))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y if pos_count > 1 else None
    )

    logger.info("Training Flood Risk XGBoost Classifier (Positive Events: %d / %d)...", pos_count, len(y))
    model = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=min(scale_weight, 15.0),
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=42,
    )

    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    auc = float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else 0.5
    brier = float(brier_score_loss(y_test, y_prob))

    logger.info("Flood Model Test Metrics: Accuracy=%.3f, Precision=%.3f, Recall=%.3f, F1=%.3f, AUC=%.3f, Brier=%.4f",
                acc, prec, rec, f1, auc, brier)

    # Save model artifact
    model_filename = "xgb_flood_risk_v1.joblib"
    model_file_path = out_path / model_filename
    joblib.dump(
        {
            "model": model,
            "feature_names": FLOOD_FEATURE_COLS,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        },
        model_file_path,
    )

    # Register in PostgreSQL
    session = SessionLocal()
    model_id = uuid.uuid4()
    try:
        session.query(ModelRegistry).filter(ModelRegistry.model_name == "flood_probability_classifier").update({"is_active": False})

        reg = ModelRegistry(
            id=model_id,
            model_name="flood_probability_classifier",
            model_version="1.0.0",
            model_type="XGBClassifier",
            training_dataset_version="v1.0",
            feature_version="v1.0",
            target_variable="flood_event_occurrence",
            training_date=datetime.now(timezone.utc),
            file_path=str(model_file_path),
            is_active=True,
            is_development=False,
            metadata_json=json.dumps({
                "features": FLOOD_FEATURE_COLS,
                "n_samples": len(df),
                "scale_pos_weight": scale_weight,
            }),
        )
        session.add(reg)

        for m_name, m_val in [
            ("roc_auc", auc),
            ("f1_score", f1),
            ("precision", prec),
            ("recall", rec),
            ("accuracy", acc),
            ("brier_score", brier),
        ]:
            session.add(ModelMetric(
                id=uuid.uuid4(),
                model_id=model_id,
                metric_name=m_name,
                metric_value=m_val,
                dataset_split="test",
                evaluation_date=datetime.now(timezone.utc),
            ))

        session.commit()
        logger.info("Flood probability model registered in DB with ID %s", model_id)
    except Exception as e:
        session.rollback()
        logger.error("Database registration failed: %s", e)
    finally:
        session.close()

    return {
        "model_id": str(model_id),
        "model_file": str(model_file_path),
        "metrics": {"auc": auc, "f1": f1, "accuracy": acc},
    }


if __name__ == "__main__":
    train_flood_model()
