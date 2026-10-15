"""
ml/inference/heavy_rain_predictor.py
Inference engine for Heavy Rainfall Prediction.
Loads the active model from model_registry and produces calibrated probabilities and binary alerts.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd

from backend.app.core.database import SessionLocal
from backend.app.models.pipeline import ModelRegistry

logger = logging.getLogger(__name__)


class HeavyRainPredictor:
    """
    Inference wrapper for Heavy Rainfall Classifier.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_data = None
        self.feature_names = []
        self._load_model(model_path)

    def _load_model(self, model_path: Optional[str] = None):
        if model_path and Path(model_path).exists():
            self.model_data = joblib.load(model_path)
        else:
            # Load active model from DB
            session = SessionLocal()
            try:
                reg = (
                    session.query(ModelRegistry)
                    .filter(
                        ModelRegistry.model_name == "heavy_rain_classifier",
                        ModelRegistry.is_active.is_(True),
                    )
                    .order_by(ModelRegistry.created_at.desc())
                    .first()
                )
                if reg and Path(reg.file_path).exists():
                    self.model_data = joblib.load(reg.file_path)
                    logger.info("Loaded active Heavy Rain model from %s (v%s)", reg.file_path, reg.model_version)
                else:
                    default_path = Path("ml/models/heavy_rain/xgb_heavy_rain_v1.joblib")
                    if default_path.exists():
                        self.model_data = joblib.load(default_path)
            finally:
                session.close()

        if self.model_data:
            self.feature_names = self.model_data.get("feature_names", [])

    @property
    def is_ready(self) -> bool:
        return self.model_data is not None

    def predict(self, feature_dicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Runs batch prediction over a list of feature dictionaries.
        """
        if not self.is_ready:
            raise RuntimeError("HeavyRainPredictor model is not loaded. Train a model first.")

        df = pd.DataFrame(feature_dicts)
        # Ensure all required features are present
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0.0

        X = df[self.feature_names]
        model = self.model_data["model"]

        probabilities = model.predict_proba(X)[:, 1]
        predictions = model.predict(X)

        results = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            prob_val = float(prob)
            results.append({
                "heavy_rain_predicted": bool(pred == 1),
                "probability": round(prob_val, 4),
                "threshold_mm": 64.5,
                "confidence": "HIGH" if prob_val > 0.75 or prob_val < 0.25 else "MODERATE",
            })
        return results
