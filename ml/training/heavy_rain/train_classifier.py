"""
ml/training/heavy_rain/train_classifier.py
Trains and registers Heavy Rainfall Classification Models (XGBoost / LightGBM).
Predicts whether accumulated rainfall will exceed IMD heavy rain threshold (>=64.5 mm).
Logs metrics to PostgreSQL model_registry and model_metrics.
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
from sklearn.model_selection import StratifiedKFold, train_test_split
from xgboost import XGBClassifier

from backend.app.core.database import SessionLocal
from backend.app.models.pipeline import ModelMetric, ModelRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("train_heavy_rain")

FEATURE_COLS = [
    "hour_sin", "hour_cos", "doy_sin", "doy_cos",
    "rainfall_1h_mm", "rainfall_3h_mm", "rainfall_6h_mm", "rainfall_12h_mm", "rainfall_24h_mm",
    "rainfall_48h_mm", "rainfall_72h_mm", "api_3day",
    "temperature_c", "humidity_percent", "pressure_hpa", "wind_speed_ms",
    "radar_reflectivity_dbz", "satellite_precip_mm", "nwp_rain_24h_mm",
    "elevation_m", "slope_deg", "twi", "curve_number", "impervious_pct",
    "direct_runoff_24h_mm", "dist_to_stream_m",
]
TARGET_COL = "target_heavy_rain"


def train_model(data_path: str = "ml/data/features/flood_training_dataset.csv", output_dir: str = "ml/models/heavy_rain"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info("Loading training data from %s...", data_path)
    df = pd.read_csv(data_path)

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    # Handle class imbalance scale_pos_weight
    neg_count = (y == 0).sum()
    pos_count = (y == 1).sum()
    scale_weight = float(neg_count / max(pos_count, 1))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    logger.info("Training XGBoost Heavy Rainfall Classifier (Pos/Neg: %d/%d)...", pos_count, neg_count)
    model = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.06,
        scale_pos_weight=scale_weight,
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

    logger.info("Evaluation on Test Split: Accuracy=%.3f, Precision=%.3f, Recall=%.3f, F1=%.3f, AUC=%.3f, Brier=%.4f",
                acc, prec, rec, f1, auc, brier)

    # Save model artifact
    model_filename = "xgb_heavy_rain_v1.joblib"
    model_file_path = out_path / model_filename
    joblib.dump(
        {
            "model": model,
            "feature_names": FEATURE_COLS,
            "threshold": 64.5,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        },
        model_file_path,
    )

    # Register model in PostgreSQL
    session = SessionLocal()
    model_id = uuid.uuid4()
    try:
        # Mark previous models of this type as inactive
        session.query(ModelRegistry).filter(ModelRegistry.model_name == "heavy_rain_classifier").update({"is_active": False})

        reg = ModelRegistry(
            id=model_id,
            model_name="heavy_rain_classifier",
            model_version="1.0.0",
            model_type="XGBClassifier",
            training_dataset_version="v1.0",
            feature_version="v1.0",
            target_variable="heavy_rain_threshold_64.5mm",
            training_date=datetime.now(timezone.utc),
            file_path=str(model_file_path),
            is_active=True,
            is_development=False,
            metadata_json=json.dumps({
                "features": FEATURE_COLS,
                "n_samples": len(df),
                "scale_pos_weight": scale_weight,
            }),
        )
        session.add(reg)

        # Store metrics
        metrics = [
            ("roc_auc", auc),
            ("f1_score", f1),
            ("precision", prec),
            ("recall", rec),
            ("accuracy", acc),
            ("brier_score", brier),
        ]
        for m_name, m_val in metrics:
            session.add(ModelMetric(
                id=uuid.uuid4(),
                model_id=model_id,
                metric_name=m_name,
                metric_value=m_val,
                dataset_split="test",
                evaluation_date=datetime.now(timezone.utc),
            ))

        session.commit()
        logger.info("Heavy Rainfall model registered successfully in database with ID %s", model_id)
    except Exception as e:
        session.rollback()
        logger.error("Failed to register model in database: %s", e)
    finally:
        session.close()

    return {
        "model_id": str(model_id),
        "model_file": str(model_file_path),
        "metrics": {"auc": auc, "f1": f1, "accuracy": acc, "precision": prec, "recall": rec},
    }


if __name__ == "__main__":
    train_model()
