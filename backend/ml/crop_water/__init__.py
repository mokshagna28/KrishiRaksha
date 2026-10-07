"""
Crop Water Requirement & Excess-Water Recovery ML Module.
Provides ML-based predictions for crop water needs, status classification,
and stress level assessment using trained models from FAO-56 & ICAR data.
"""

from backend.ml.crop_water.predict import crop_water_predictor

__all__ = ["crop_water_predictor"]
