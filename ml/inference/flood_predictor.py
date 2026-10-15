"""
ml/inference/flood_predictor.py
Inference engine for Flood Probability and Risk Classification.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.pipeline import ModelRegistry

logger = logging.getLogger(__name__)


class FloodPredictor:
    """
    Inference wrapper for Flood Risk models.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_data = None
        self.feature_names = []
        self._load_model(model_path)

    def _load_model(self, model_path: Optional[str] = None):
        if model_path and Path(model_path).exists():
            self.model_data = joblib.load(model_path)
        else:
            session = SessionLocal()
            try:
                reg = (
                    session.query(ModelRegistry)
                    .filter(
                        ModelRegistry.model_name == "flood_probability_classifier",
                        ModelRegistry.is_active.is_(True),
                    )
                    .order_by(ModelRegistry.created_at.desc())
                    .first()
                )
                if reg and Path(reg.file_path).exists():
                    self.model_data = joblib.load(reg.file_path)
                    logger.info("Loaded active Flood model from %s (v%s)", reg.file_path, reg.model_version)
                else:
                    default_path = Path("ml/models/flood/xgb_flood_risk_v1.joblib")
                    if default_path.exists():
                        self.model_data = joblib.load(default_path)
            finally:
                session.close()

        if self.model_data:
            self.feature_names = self.model_data.get("feature_names", [])

    @property
    def is_ready(self) -> bool:
        return self.model_data is not None

    def classify_risk_level(self, probability: float) -> str:
        if probability >= settings.flood_prob_extreme_threshold:
            return "EXTREME"
        elif probability >= settings.flood_prob_very_high_threshold:
            return "VERY_HIGH"
        elif probability >= settings.flood_prob_high_threshold:
            return "HIGH"
        elif probability >= settings.flood_prob_moderate_threshold:
            return "MODERATE"
        return "LOW"

    def predict(self, feature_dicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.is_ready:
            raise RuntimeError("FloodPredictor model is not loaded. Train a model first.")

        df = pd.DataFrame(feature_dicts)
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0.0

        X = df[self.feature_names]
        model = self.model_data["model"]

        probabilities = model.predict_proba(X)[:, 1]

        results = []
        for prob in probabilities:
            prob_val = float(prob)
            risk = self.classify_risk_level(prob_val)
            results.append({
                "flood_probability": round(prob_val, 4),
                "risk_level": risk,
                "is_flood_expected": bool(prob_val >= settings.flood_prob_high_threshold),
            })
        return results
