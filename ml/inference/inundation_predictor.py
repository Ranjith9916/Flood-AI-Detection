"""
ml/inference/inundation_predictor.py
Inference engine for Inundation Extent and Depth Prediction.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd

from backend.app.core.database import SessionLocal
from backend.app.models.pipeline import ModelRegistry

logger = logging.getLogger(__name__)


class InundationPredictor:
    """
    Inference wrapper for Inundation Depth models.
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
                        ModelRegistry.model_name == "inundation_depth_predictor",
                        ModelRegistry.is_active.is_(True),
                    )
                    .order_by(ModelRegistry.created_at.desc())
                    .first()
                )
                if reg and Path(reg.file_path).exists():
                    self.model_data = joblib.load(reg.file_path)
                    logger.info("Loaded active Inundation model from %s (v%s)", reg.file_path, reg.model_version)
                else:
                    default_path = Path("ml/models/inundation/gb_inundation_depth_v1.joblib")
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
        if not self.is_ready:
            raise RuntimeError("InundationPredictor model is not loaded. Train a model first.")

        df = pd.DataFrame(feature_dicts)
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0.0

        X = df[self.feature_names]
        model = self.model_data["model"]

        raw_depths = model.predict(X)
        depths = np.clip(raw_depths, 0.0, None)

        results = []
        for depth in depths:
            d_val = round(float(depth), 2)
            results.append({
                "estimated_depth_m": d_val,
                "is_inundated": bool(d_val >= 0.05),
                "severity": "CRITICAL" if d_val >= 1.0 else ("MODERATE" if d_val >= 0.3 else ("MINOR" if d_val >= 0.05 else "NONE")),
            })
        return results
