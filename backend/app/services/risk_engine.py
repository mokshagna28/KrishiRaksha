"""
KRISHIRAKSHA AI - Risk Assessment & Explainability Engine
Student Roll Number: 231FA04291

Synthesizes:
1. Machine Learning Heavy Rain Probability
2. Official IMD District Weather Warning (GREEN, YELLOW, ORANGE, RED)
3. Recent 24h Observed Rainfall
4. Cumulative Antecedent Rainfall (3-day, 7-day soil saturation proxy)
5. 24h & 48h Quantitative Precipitation Forecast (QPF)

Outputs explainable factors based purely on real data inputs.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("krishiraksha.risk_engine")

class RiskEngine:
    """
    Configurable Risk Assessment Engine.
    Levels: LOW, MODERATE, HIGH, VERY_HIGH
    """

    # Configurable thresholds
    THRESHOLD_LOW_MAX = 30.0
    THRESHOLD_MODERATE_MAX = 60.0
    THRESHOLD_HIGH_MAX = 80.0

    @classmethod
    def calculate_risk(
        cls,
        district_name: str,
        state_name: str,
        ml_heavy_rain_prob: float, # 0.0 to 1.0
        ml_confidence: float, # 0 to 100
        official_warning_color: str, # GREEN, YELLOW, ORANGE, RED
        current_rainfall_24h: float, # mm
        forecast_rainfall_24h: float, # mm
        forecast_rainfall_48h: float, # mm
        recent_accumulated_7d: float, # mm
        data_freshness: str = "FRESH"
    ) -> Dict[str, Any]:
        """
        Calculates composite risk score and generates verified explainability reasons.
        """
        reasons: List[str] = []

        # 1. Base ML Probability Contribution (Max 40 points)
        ml_score = ml_heavy_rain_prob * 40.0
        if ml_heavy_rain_prob >= 0.70:
            reasons.append(f"AI Heavy Rain model indicates critical precipitation likelihood ({ml_heavy_rain_prob*100:.1f}%)")
        elif ml_heavy_rain_prob >= 0.40:
            reasons.append(f"AI Heavy Rain model indicates moderate rainfall likelihood ({ml_heavy_rain_prob*100:.1f}%)")

        # 2. Official IMD Warning Weight (Max 25 points)
        warning_color = (official_warning_color or "GREEN").upper()
        warning_score = 0.0
        if warning_color == "RED":
            warning_score = 25.0
            reasons.append("Official IMD District Warning: RED (Take Action for Extreme Weather)")
        elif warning_color == "ORANGE":
            warning_score = 18.0
            reasons.append("Official IMD District Warning: ORANGE (Be Prepared for Heavy to Very Heavy Rain)")
        elif warning_color == "YELLOW":
            warning_score = 8.0
            reasons.append("Official IMD District Warning: YELLOW (Be Updated / Moderate Weather)")
        else:
            warning_score = 0.0

        # 3. Forecast Rainfall Contribution (Max 20 points)
        max_forecast = max(forecast_rainfall_24h, forecast_rainfall_48h)
        forecast_score = 0.0
        if max_forecast >= 115.6:
            forecast_score = 20.0
            reasons.append(f"Severe rainfall forecast: {max_forecast:.1f} mm expected within next 48h")
        elif max_forecast >= 64.5:
            forecast_score = 14.0
            reasons.append(f"Heavy rainfall forecast: {max_forecast:.1f} mm expected within next 24-48h")
        elif max_forecast >= 35.5:
            forecast_score = 8.0
            reasons.append(f"Moderate to heavy rainfall forecast: {max_forecast:.1f} mm expected")
        elif max_forecast > 10.0:
            forecast_score = 3.0

        # 4. Recent Rainfall & Cumulative Soil Saturation (Max 15 points)
        soil_score = 0.0
        if current_rainfall_24h >= 64.5:
            soil_score += 8.0
            reasons.append(f"Heavy daily rainfall observed: {current_rainfall_24h:.1f} mm in past 24 hours")
        elif current_rainfall_24h >= 35.5:
            soil_score += 4.0
            reasons.append(f"Significant daily rainfall observed: {current_rainfall_24h:.1f} mm in past 24 hours")

        if recent_accumulated_7d >= 150.0:
            soil_score += 7.0
            reasons.append(f"High 7-day cumulative rainfall accumulation: {recent_accumulated_7d:.1f} mm causing elevated soil saturation")
        elif recent_accumulated_7d >= 80.0:
            soil_score += 4.0
            reasons.append(f"Elevated 7-day cumulative rainfall: {recent_accumulated_7d:.1f} mm")

        # Total Composite Risk Score (0 - 100)
        composite_score = round(min(100.0, ml_score + warning_score + forecast_score + soil_score), 1)

        # AI-only risk category (separate from official warning)
        if ml_heavy_rain_prob >= 0.75:
            ai_risk = "VERY_HIGH"
        elif ml_heavy_rain_prob >= 0.50:
            ai_risk = "HIGH"
        elif ml_heavy_rain_prob >= 0.25:
            ai_risk = "MODERATE"
        else:
            ai_risk = "LOW"

        # Final Composite Risk Level
        if composite_score >= cls.THRESHOLD_HIGH_MAX or warning_color == "RED":
            final_risk = "VERY_HIGH"
        elif composite_score >= cls.THRESHOLD_MODERATE_MAX or warning_color == "ORANGE":
            final_risk = "HIGH"
        elif composite_score >= cls.THRESHOLD_LOW_MAX or warning_color == "YELLOW":
            final_risk = "MODERATE"
        else:
            final_risk = "LOW"

        if not reasons:
            reasons.append("All meteorological parameters within normal, dry-weather operational thresholds.")

        return {
            "district_name": district_name,
            "state_name": state_name,
            "ai_risk_level": ai_risk,
            "official_warning_level": warning_color,
            "final_risk_level": final_risk,
            "risk_score": composite_score,
            "confidence": ml_confidence,
            "contributing_factors": reasons,
            "data_freshness_status": data_freshness,
            "assessment_time": datetime.utcnow()
        }

risk_engine = RiskEngine()
