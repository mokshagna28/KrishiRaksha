"""
Crop Price Forecasting - Inference & Prediction Engine
Loads the trained champion ML pipeline and provides:
- Current price context from historical data
- 7/14/30-day ML price forecasts
- Selling window recommendations
- Market intelligence summaries
"""

import os
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

from backend.ml.marketplace.features import (
    create_time_series_features,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_PRICE,
)

logger = logging.getLogger("krishiraksha.marketplace.predict")

MARKETPLACE_MODEL_DIR = os.path.join("ml_artifacts", "marketplace")
MODEL_PATH     = os.path.join(MARKETPLACE_MODEL_DIR, "price_forecast_model.pkl")
METADATA_PATH  = os.path.join(MARKETPLACE_MODEL_DIR, "price_forecast_metadata.json")
DATA_PATH      = os.path.join("data", "marketplace", "crop_price_history.csv")

RECOMMENDATION_LABELS = {
    "SELL_NOW":     "Favorable to Sell Now",
    "WAIT":         "Wait — Higher Price Expected",
    "MONITOR":      "Monitor — Price Uncertain",
    "CAUTION":      "Caution — Price May Decline",
}


class MarketplacePricePredictor:
    def __init__(self):
        self._model = None
        self._metadata: Optional[Dict] = None
        self._history_df: Optional[pd.DataFrame] = None

    def _load(self):
        """Lazy-load model, metadata, and historical dataset."""
        if self._model is None:
            if not os.path.exists(MODEL_PATH):
                return False
            with open(MODEL_PATH, "rb") as f:
                self._model = pickle.load(f)
            with open(METADATA_PATH, "r") as f:
                self._metadata = json.load(f)
            if os.path.exists(DATA_PATH):
                raw = pd.read_csv(DATA_PATH)
                self._history_df = create_time_series_features(raw)
                self._history_df["date"] = pd.to_datetime(self._history_df["date"])
        return self._model is not None

    def is_ready(self) -> bool:
        return self._load()

    def get_metadata(self) -> Optional[Dict]:
        self._load()
        return self._metadata

    def get_supported_options(self) -> Dict[str, List[str]]:
        if not self._load():
            return {}
        meta = self._metadata or {}
        return {
            "crops": meta.get("supported_crops", []),
            "markets": meta.get("supported_markets", []),
        }

    def _get_crop_market_history(self, crop: str, market: str, days: int = 30) -> pd.DataFrame:
        """Return recent price history for a crop-market pair."""
        if self._history_df is None:
            return pd.DataFrame()
        df = self._history_df[
            (self._history_df["crop"] == crop) & (self._history_df["market"] == market)
        ].sort_values("date")
        return df.tail(days)

    def _build_forecast_row(self, crop: str, market: str, state: str,
                             base_row: pd.Series, offset_days: int) -> pd.DataFrame:
        """
        Build a synthetic feature row for a future date by
        simulating lag values from the base_row.
        """
        future_date = pd.Timestamp.now() + timedelta(days=offset_days)
        row = {
            "crop": crop,
            "market": market,
            "state": state,
            "date": future_date,
            "modal_price": base_row.get("modal_price", 0),
            "arrivals_quintal": base_row.get("arrivals_quintal", base_row.get("arrivals", 100)),
            "price_lag_1": base_row.get("modal_price", 0),
            "price_lag_3": base_row.get("price_roll_mean_7", base_row.get("modal_price", 0)),
            "price_lag_7": base_row.get("price_roll_mean_7", base_row.get("modal_price", 0)),
            "price_roll_mean_7": base_row.get("price_roll_mean_7", base_row.get("modal_price", 0)),
            "price_roll_std_7": base_row.get("price_roll_std_7", 50.0),
            "month": future_date.month,
            "dayofweek": future_date.dayofweek,
        }
        return pd.DataFrame([row])

    def predict_price_forecast(
        self, crop: str, market: str, state: str,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate ML price forecasts for the next forecast_days.
        Returns current price context + daily forecast array + selling recommendation.
        """
        if not self._load():
            return {"error": True, "message": "Marketplace ML model not trained yet. Run /api/market/train first."}

        hist = self._get_crop_market_history(crop, market, days=60)
        if hist.empty:
            return {"error": True, "message": f"No historical data for {crop} in {market}. Check supported crops/markets."}

        latest_row = hist.iloc[-1]
        current_price = float(latest_row["modal_price"])

        # Recent stats
        recent_7d  = hist.tail(7)["modal_price"].tolist()
        recent_30d = hist.tail(30)["modal_price"].tolist()
        avg_7d     = round(float(np.mean(recent_7d)), 2)
        avg_30d    = round(float(np.mean(recent_30d)), 2)
        price_trend_7d = round(float(hist.tail(7)["modal_price"].pct_change().mean() * 100), 2)

        # Forecast checkpoints: 7, 14, 30 days
        checkpoints = [7, 14, 30]
        forecasts = []
        for days_ahead in checkpoints:
            if days_ahead > forecast_days:
                continue
            row_df = self._build_forecast_row(crop, market, state, latest_row, days_ahead)
            X = row_df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
            try:
                pred_price = float(self._model.predict(X)[0])
                pred_price = max(pred_price, 0)  # floor at 0
            except Exception as e:
                logger.warning(f"Prediction error for {crop}/{market} +{days_ahead}d: {e}")
                pred_price = current_price
            pct_change = round(((pred_price - current_price) / current_price) * 100, 2) if current_price > 0 else 0.0
            forecasts.append({
                "days_ahead": days_ahead,
                "forecast_date": (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d"),
                "predicted_price": round(pred_price, 2),
                "price_change_pct": pct_change,
                "price_change_rs": round(pred_price - current_price, 2),
                "is_ml_prediction": True,
            })

        # Determine best forecast window
        best_forecast = max(forecasts, key=lambda x: x["predicted_price"]) if forecasts else None
        best_price    = best_forecast["predicted_price"] if best_forecast else current_price
        best_pct      = best_forecast["price_change_pct"] if best_forecast else 0.0

        # Recommendation logic
        if best_pct >= 5:
            recommendation = "WAIT"
        elif best_pct <= -5:
            recommendation = "SELL_NOW"
        elif abs(price_trend_7d) > 3:
            recommendation = "MONITOR"
        else:
            recommendation = "SELL_NOW"

        # Historical price context
        hist_price_series = []
        for _, row in hist.tail(30).iterrows():
            hist_price_series.append({
                "date": str(row["date"])[:10],
                "price": round(float(row["modal_price"]), 2),
                "is_observed": True,
            })

        meta = self._metadata or {}
        return {
            "error": False,
            "crop": crop,
            "market": market,
            "state": state,
            "current_price": round(current_price, 2),
            "price_unit": meta.get("price_unit", "Rs/quintal"),
            "current_price_context": {
                "avg_7d": avg_7d,
                "avg_30d": avg_30d,
                "trend_7d_pct": price_trend_7d,
                "vs_avg_30d_pct": round(((current_price - avg_30d) / avg_30d) * 100, 2) if avg_30d > 0 else 0.0,
            },
            "forecasts": forecasts,
            "best_selling_window": best_forecast,
            "recommendation": recommendation,
            "recommendation_label": RECOMMENDATION_LABELS.get(recommendation, recommendation),
            "historical_price_series": hist_price_series,
            "model_version": meta.get("version", "unknown"),
            "model_algorithm": meta.get("champion_algorithm", "unknown"),
            "scientific_disclaimer": meta.get("scientific_note", ""),
            "prediction_generated_at": datetime.utcnow().isoformat(),
        }

    def get_market_overview(self, crops: Optional[List[str]] = None) -> Dict[str, Any]:
        """Return price overview for multiple crops across top markets."""
        if not self._load():
            return {"error": True, "message": "Model not trained"}
        meta = self._metadata or {}
        all_crops = crops or meta.get("supported_crops", [])[:5]
        top_markets = meta.get("supported_markets", [])[:3]

        overview = []
        for crop in all_crops:
            for market in top_markets:
                hist = self._get_crop_market_history(crop, market, days=7)
                if hist.empty:
                    continue
                latest = hist.iloc[-1]
                trend = round(float(hist["modal_price"].pct_change().mean() * 100), 2)
                overview.append({
                    "crop": crop,
                    "market": market,
                    "latest_price": round(float(latest["modal_price"]), 2),
                    "price_unit": "Rs/quintal",
                    "trend_7d_pct": trend,
                    "trend_direction": "UP" if trend > 0.5 else "DOWN" if trend < -0.5 else "STABLE",
                })

        return {
            "market_overview": overview,
            "last_updated": datetime.utcnow().isoformat(),
            "data_source": meta.get("data_source", "AGMARKNET / eNAM"),
        }


# Global singleton
marketplace_predictor = MarketplacePricePredictor()
