"""
Train All Machine Learning Models Script.
Trains:
1. Heavy Rain Classifier (XGBClassifier)
2. Flood Probability & Risk Classifier (XGBClassifier)
3. Quantitative Rainfall Forecaster (XGBRegressor)
4. Inundation Depth Predictor (GradientBoostingRegressor)
Registers trained artifacts and evaluation metrics into PostgreSQL model_registry.
"""
import sys
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.training.heavy_rain.train_classifier import train_heavy_rain_model
from ml.training.flood.train_xgboost import train_flood_model
from ml.training.rainfall.train_xgboost import train_rainfall_forecast_model
from ml.training.inundation.train_segmentation import train_inundation_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TrainAllModels")

def main():
    logger.info("================================================================================")
    logger.info("  FLOOD-AI: Training and Registering All 4 AI/ML Models in Model Registry        ")
    logger.info("================================================================================")
    
    # 1. Heavy Rain Classifier
    logger.info("\n--- [1/4] Training Heavy Rainfall Classifier (XGBoost) ---")
    m1 = train_heavy_rain_model()
    logger.info(f"Model 1 trained: {m1.get('model_name')} v{m1.get('version')} (ROC-AUC: {m1.get('metrics', {}).get('roc_auc', 0):.4f})")
    
    # 2. Flood Probability Classifier
    logger.info("\n--- [2/4] Training Flood Probability & Risk Level Classifier (XGBoost) ---")
    m2 = train_flood_model()
    logger.info(f"Model 2 trained: {m2.get('model_name')} v{m2.get('version')} (ROC-AUC: {m2.get('metrics', {}).get('roc_auc', 0):.4f})")
    
    # 3. Quantitative Rainfall Forecaster
    logger.info("\n--- [3/4] Training Continuous Rainfall Forecaster (XGBoost Regressor) ---")
    m3 = train_rainfall_forecast_model()
    logger.info(f"Model 3 trained: {m3.get('model_name')} v{m3.get('version')} (R2: {m3.get('metrics', {}).get('r2_score', 0):.4f}, RMSE: {m3.get('metrics', {}).get('rmse', 0):.2f} mm)")
    
    # 4. Inundation Depth Predictor
    logger.info("\n--- [4/4] Training Inundation Depth Predictor (Gradient Boosting) ---")
    m4 = train_inundation_model()
    logger.info(f"Model 4 trained: {m4.get('model_name')} v{m4.get('version')} (R2: {m4.get('metrics', {}).get('r2_score', 0):.4f}, IoU: {m4.get('metrics', {}).get('iou', 0):.4f})")
    
    logger.info("\n================================================================================")
    logger.info("  All 4 Models Successfully Trained and Registered in PostgreSQL Registry!     ")
    logger.info("================================================================================")

if __name__ == "__main__":
    main()
