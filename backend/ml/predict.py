"""
KRISHIRAKSHA AI - Heavy Rainfall Risk Inference Service
Student Roll Number: 231FA04291

Checks data freshness, applies feature extraction, and runs inference.
Never predicts on insufficient or invalid data.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from backend.ml.model_registry import model_registry
from backend.ml.features import (
    extract_features_single_observation,
    FEATURE_NAMES,
    FEATURES_VERSION
)

logger = logging.getLogger("krishiraksha.ml_predict")

def predict_heavy_rain_risk(
    rainfall_history: List[float],
    temperature: Optional[float],
    humidity: Optional[float],
    wind_speed: Optional[float],
    month: int = 7,
    data_freshness: str = "FRESH"
) -> Dict[str, Any]:
    """
    Executes heavy rainfall probability prediction with strict sanity and freshness checks.
    """
    # Requirement #37 & #48: If live weather data is missing or stale
    if data_freshness in ["DATA_INSUFFICIENT", "STALE"]:
        return {
            "status": "DATA_INSUFFICIENT",
            "message": "Current prediction unavailable because fresh weather data is unavailable.",
            "heavy_rain_prob": 0.0,
            "predicted_class": 0,
            "confidence": 0.0,
            "model_name": None,
            "model_version": None,
            "features_version": FEATURES_VERSION,
            "features_used": {}
        }

    # Verify input variables
    if temperature is None or humidity is None or wind_speed is None:
        return {
            "status": "DATA_INSUFFICIENT",
            "message": "Meteorological observation fields are incomplete.",
            "heavy_rain_prob": 0.0,
            "predicted_class": 0,
            "confidence": 0.0,
            "model_name": None,
            "model_version": None,
            "features_version": FEATURES_VERSION,
            "features_used": {}
        }

    model = model_registry.load_champion_model()
    metadata = model_registry.get_metadata()

    if model is None or metadata is None:
        return {
            "status": "MODEL_UNAVAILABLE",
            "message": "ML model artifact is not loaded or ready. Run training pipeline first.",
            "heavy_rain_prob": 0.0,
            "predicted_class": 0,
            "confidence": 0.0,
            "model_name": None,
            "model_version": None,
            "features_version": FEATURES_VERSION,
            "features_used": {}
        }

    # Extract feature vector
    feat_df = extract_features_single_observation(
        rainfall_history=rainfall_history,
        temperature=temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        month=month
    )

    try:
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(feat_df)[0]
            prob_heavy = float(probs[1])
            pred_class = int(prob_heavy >= 0.5)
            # Confidence is statistical certainty of the predicted class
            confidence = round(float(np.max(probs)) * 100.0, 1)
        else:
            pred_class = int(model.predict(feat_df)[0])
            prob_heavy = 1.0 if pred_class == 1 else 0.0
            confidence = 80.0

        features_dict = feat_df.to_dict(orient="records")[0]

        return {
            "status": "SUCCESS",
            "heavy_rain_prob": round(prob_heavy, 4),
            "predicted_class": pred_class,
            "confidence": confidence,
            "model_name": metadata.get("model_name"),
            "model_version": metadata.get("version"),
            "features_version": FEATURES_VERSION,
            "prediction_time": datetime.utcnow().isoformat(),
            "features_used": features_dict
        }

    except Exception as ex:
        logger.error(f"Inference execution failed: {ex}")
        return {
            "status": "ERROR",
            "message": f"Inference execution failed: {str(ex)}",
            "heavy_rain_prob": 0.0,
            "predicted_class": 0,
            "confidence": 0.0,
            "model_name": metadata.get("model_name"),
            "model_version": metadata.get("version"),
            "features_version": FEATURES_VERSION,
            "features_used": {}
        }
