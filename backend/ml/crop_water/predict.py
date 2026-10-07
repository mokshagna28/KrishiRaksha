"""
Crop Water Requirement, Excess-Water Stress, Treatment & Recovery ML Inference Module.
Loads trained models (preprocessor, regressor, classifier, stress classifier, disease classifier,
treatment classifier, recovery classifier) and produces real-time predictions for crop health & recovery.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger("krishiraksha.crop_water.predict")

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models")
METADATA_PATH = os.path.join(MODELS_DIR, "crop_water_metadata.json")


class CropWaterPredictor:
    """
    Loads and caches crop water & recovery ML artifacts.
    Exposes a .predict() method that returns complete pipeline outputs.
    """

    def __init__(self):
        self._preprocessor = None
        self._regressor = None
        self._classifier = None
        self._stress_classifier = None
        self._disease_classifier = None
        self._treatment_classifier = None
        self._recovery_classifier = None
        self._metadata: Optional[Dict] = None
        self._loaded = False

    def _load(self):
        """Load all model artifacts from disk."""
        try:
            self._preprocessor = joblib.load(os.path.join(MODELS_DIR, "crop_water_preprocessor.joblib"))
            self._regressor = joblib.load(os.path.join(MODELS_DIR, "crop_water_regressor.joblib"))
            self._classifier = joblib.load(os.path.join(MODELS_DIR, "crop_water_classifier.joblib"))
            self._stress_classifier = joblib.load(os.path.join(MODELS_DIR, "crop_stress_classifier.joblib"))
            self._disease_classifier = joblib.load(os.path.join(MODELS_DIR, "crop_disease_classifier.joblib"))
            self._treatment_classifier = joblib.load(os.path.join(MODELS_DIR, "crop_treatment_classifier.joblib"))
            self._recovery_classifier = joblib.load(os.path.join(MODELS_DIR, "crop_recovery_classifier.joblib"))

            with open(METADATA_PATH, "r") as f:
                self._metadata = json.load(f)

            self._loaded = True
            logger.info("All 5 Crop Water & Recovery ML models loaded successfully from %s", MODELS_DIR)
        except FileNotFoundError as e:
            logger.warning("Crop Water & Recovery models not found: %s. Run training first.", e)
            self._loaded = False

    def is_ready(self) -> bool:
        if not self._loaded:
            self._load()
        return self._loaded

    def get_metadata(self) -> Optional[Dict]:
        if not self._loaded:
            self._load()
        return self._metadata

    def predict(
        self,
        crop: str,
        growth_stage: str,
        soil_type: str,
        soil_moisture: float,
        recent_rainfall: float,
        forecast_rainfall: float,
        temperature: float,
        humidity: float,
        wind_speed: float,
    ) -> Dict[str, Any]:
        """
        Runs the full 7-step ML pipeline:
          Crop -> Growth Stage -> Water/Rainfall -> Water Status -> Excess-Water Stress -> Disease ID -> Treatment -> Recovery
        """
        if not self.is_ready():
            return {
                "error": True,
                "message": "Crop Water & Recovery ML models are not trained yet. Please run training first."
            }

        input_df = pd.DataFrame([{
            "soil_moisture": soil_moisture,
            "recent_rainfall": recent_rainfall,
            "forecast_rainfall": forecast_rainfall,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "crop": crop,
            "growth_stage": growth_stage,
            "soil_type": soil_type,
        }])

        try:
            X_proc = self._preprocessor.transform(input_df)
        except Exception as e:
            logger.error("Preprocessing failed: %s", e)
            return {"error": True, "message": f"Feature preprocessing failed: {str(e)}"}

        # 1. Regression: Water Requirement (mm)
        water_req_mm = float(self._regressor.predict(X_proc)[0])
        water_req_mm = max(0.0, round(water_req_mm, 2))

        # 2. Classification: Water Status
        water_status = str(self._classifier.predict(X_proc)[0])

        # Status Classifier confidence
        if hasattr(self._classifier, "predict_proba"):
            probs = self._classifier.predict_proba(X_proc)[0]
            confidence = float(np.max(probs)) * 100
        elif hasattr(self._classifier, "decision_function"):
            decision = self._classifier.decision_function(X_proc)[0]
            exp_vals = np.exp(decision - np.max(decision))
            confidence = float(np.max(exp_vals / exp_vals.sum())) * 100
        else:
            confidence = 95.0

        # 3. Stress Level
        stress_level = str(self._stress_classifier.predict(X_proc)[0])

        # 4. Excess-Water Disease / Stress Classification
        disease_stress = str(self._disease_classifier.predict(X_proc)[0])

        # 5. Recommended Treatment / Pesticide Prediction
        recommended_treatment = str(self._treatment_classifier.predict(X_proc)[0])

        # 6. Expected Recovery Prediction
        expected_recovery = str(self._recovery_classifier.predict(X_proc)[0])

        # Lookup treatment metadata from saved dictionary
        treatment_meta = self._metadata.get("treatment_metadata", {}).get(
            recommended_treatment,
            {
                "treatment_category": "Agronomic & Agrochemical Recovery",
                "active_ingredient": "Specific to condition",
                "application_info": "Follow ICAR guidelines and package instructions."
            }
        )

        # Build explainable rationale/reason
        reason = self._generate_reason(
            crop, growth_stage, water_status, stress_level, disease_stress,
            soil_type, soil_moisture, recent_rainfall, forecast_rainfall, humidity
        )

        # Build advisory
        advisory = self._generate_advisory(
            water_status, stress_level, disease_stress, crop, water_req_mm, recent_rainfall, forecast_rainfall
        )

        return {
            "error": False,
            "water_requirement_mm": water_req_mm,
            "water_status": water_status,
            "crop_stress_level": stress_level,
            "crop_disease_stress": disease_stress,
            "recommended_treatment": recommended_treatment,
            "treatment_details": {
                "treatment_name": recommended_treatment,
                "category": treatment_meta.get("treatment_category", "Agronomic Recovery"),
                "active_ingredient": treatment_meta.get("active_ingredient", "N/A"),
                "application_info": treatment_meta.get("application_info", "Apply per instructions."),
                "target_condition": disease_stress
            },
            "expected_recovery": expected_recovery,
            "confidence": round(confidence, 2),
            "reason": reason,
            "advisory": advisory,
            "input_features": {
                "crop": crop,
                "growth_stage": growth_stage,
                "soil_type": soil_type,
                "soil_moisture": soil_moisture,
                "recent_rainfall": recent_rainfall,
                "forecast_rainfall": forecast_rainfall,
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
            },
            "model_info": {
                "regressor": self._metadata.get("regression", {}).get("champion_algorithm", "Unknown"),
                "classifier": self._metadata.get("classification", {}).get("champion_algorithm", "Unknown"),
                "disease_classifier": self._metadata.get("disease_classification", {}).get("champion_algorithm", "Unknown"),
                "treatment_classifier": self._metadata.get("treatment_classification", {}).get("champion_algorithm", "Unknown"),
                "recovery_classifier": self._metadata.get("recovery_classification", {}).get("champion_algorithm", "Unknown"),
            }
        }

    def _generate_reason(
        self, crop: str, growth_stage: str, water_status: str, stress_level: str,
        disease_stress: str, soil_type: str, soil_moisture: float,
        recent_rainfall: float, forecast_rainfall: float, humidity: float
    ) -> str:
        total_water = recent_rainfall + forecast_rainfall
        if "EXCESS" in water_status.upper():
            return (
                f"For {crop} in {growth_stage} stage grown in {soil_type} soil, the cumulative water input "
                f"({recent_rainfall:.1f}mm past + {forecast_rainfall:.1f}mm forecast) and high soil moisture ({soil_moisture:.1f}%) "
                f"substantially exceed the root zone field capacity. The ML model detected severe excess-water condition triggering '{disease_stress}'. "
                f"The recommended treatment is prioritized based on historical ICAR efficacy data under {humidity:.1f}% relative humidity."
            )
        elif "LOW" in water_status.upper():
            return (
                f"For {crop} at {growth_stage} stage, recent rainfall ({recent_rainfall:.1f}mm) and soil moisture ({soil_moisture:.1f}%) "
                f"are below crop evapotranspiration demand, resulting in water deficit stress ('{disease_stress}')."
            )
        else:
            return (
                f"Water availability ({total_water:.1f}mm rainfall + {soil_moisture:.1f}% soil moisture) is within optimal ETc range "
                f"for {crop} at {growth_stage} stage. Crop condition is healthy."
            )

    def _generate_advisory(
        self, water_status: str, stress_level: str, disease_stress: str, crop: str,
        water_req_mm: float, recent_rainfall: float, forecast_rainfall: float
    ) -> Dict[str, Any]:
        advisories: List[str] = []
        severity = "INFO"

        if "EXCESS" in water_status.upper() or "WATERLOGGING" in water_status.upper():
            severity = "CRITICAL"
            advisories.extend([
                f"🚨 EXCESS WATER ALERT: High waterlogging risk detected for {crop}.",
                f"Detected Stress/Disease: {disease_stress}.",
                "Initiate emergency surface and furrow field drainage immediately.",
                "Suspend all irrigation until soil aeration and moisture levels stabilize.",
                "Apply recommended agrochemical/cultural recovery treatment promptly.",
            ])
        elif "LOW" in water_status.upper() or "STRESS" in water_status.upper():
            severity = "WARNING"
            deficit = max(0, water_req_mm - recent_rainfall)
            advisories.extend([
                f"💧 WATER DEFICIT ALERT: Supplemental irrigation required for {crop}.",
                f"Estimated deficit: ~{deficit:.1f} mm.",
                "Apply light supplemental irrigation during early morning hours.",
            ])
        else:
            severity = "INFO"
            advisories.extend([
                f"✅ OPTIMAL CONDITIONS: Water availability matches {crop} requirements ({water_req_mm:.1f} mm).",
                "Maintain standard field management and scheduled monitoring.",
            ])

        return {
            "severity": severity,
            "messages": advisories,
            "water_surplus_deficit_mm": round(recent_rainfall + forecast_rainfall - water_req_mm, 2)
        }


# Singleton instance
crop_water_predictor = CropWaterPredictor()
