"""
Crop Price Forecasting - ML Training Pipeline
Trains RandomForestRegressor and GradientBoostingRegressor on
AGMARKNET-style historical market price data.
Chronological train/test splitting prevents data leakage.
"""

import os
import json
import logging
import pickle
from datetime import datetime
from typing import Dict, Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from backend.ml.marketplace.features import (
    load_and_split_data,
    build_preprocessor,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_PRICE,
)

logger = logging.getLogger("krishiraksha.marketplace.train")

MARKETPLACE_MODEL_DIR = os.path.join("ml_artifacts", "marketplace")
MODEL_PATH = os.path.join(MARKETPLACE_MODEL_DIR, "price_forecast_model.pkl")
METADATA_PATH = os.path.join(MARKETPLACE_MODEL_DIR, "price_forecast_metadata.json")

CANDIDATE_MODELS = {
    "RandomForest": RandomForestRegressor(
        n_estimators=200, max_depth=12, min_samples_leaf=3, n_jobs=-1, random_state=42
    ),
    "GradientBoosting": GradientBoostingRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.08, subsample=0.8, random_state=42
    ),
}


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2   = r2_score(y_true, y_pred)
    mask = y_true != 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100) if mask.sum() > 0 else 0.0
    return {
        "mae": round(float(mae), 4),
        "rmse": round(rmse, 4),
        "r2_score": round(float(r2), 4),
        "mape_pct": round(mape, 4),
    }


def train_price_forecast_model() -> Dict[str, Any]:
    """
    1. Load and feature-engineer historical market data.
    2. Train candidate regressors with chronological split.
    3. Select champion by lowest RMSE.
    4. Persist champion model + metadata JSON.
    """
    os.makedirs(MARKETPLACE_MODEL_DIR, exist_ok=True)
    logger.info("=== Crop Price Forecast ML Training ===")

    data = load_and_split_data()
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_train"], data["y_test"]
    full_df = data["full_df"]
    logger.info(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}")

    preprocessor = build_preprocessor()
    results: Dict[str, Any] = {}
    champion_name = None
    champion_rmse = float("inf")
    champion_pipeline = None

    for name, estimator in CANDIDATE_MODELS.items():
        logger.info(f"Training {name}...")
        pipeline = Pipeline([("preprocessor", preprocessor), ("regressor", estimator)])
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        metrics = compute_metrics(y_test.values, y_pred)
        results[name] = metrics
        logger.info(f"  {name}: RMSE={metrics['rmse']}, R2={metrics['r2_score']}, MAPE={metrics['mape_pct']}%")
        if metrics["rmse"] < champion_rmse:
            champion_rmse = metrics["rmse"]
            champion_name = name
            champion_pipeline = pipeline

    logger.info(f"Champion: {champion_name} (RMSE={champion_rmse})")

    # Feature importance (RandomForest only)
    feature_importance: Dict[str, float] = {}
    if champion_name == "RandomForest":
        reg = champion_pipeline.named_steps["regressor"]
        pre = champion_pipeline.named_steps["preprocessor"]
        feat_names = (
            NUMERICAL_FEATURES
            + list(pre.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES))
        )
        feature_importance = {
            fn: round(float(imp), 6)
            for fn, imp in sorted(zip(feat_names, reg.feature_importances_), key=lambda x: -x[1])
        }

    supported_crops   = sorted(full_df["crop"].unique().tolist())
    supported_markets = sorted(full_df["market"].unique().tolist())
    price_range = {
        "min":  round(float(full_df[TARGET_PRICE].min()), 2),
        "max":  round(float(full_df[TARGET_PRICE].max()), 2),
        "mean": round(float(full_df[TARGET_PRICE].mean()), 2),
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(champion_pipeline, f)
    logger.info(f"Model saved: {MODEL_PATH}")

    metadata = {
        "version": f"mp-v{datetime.utcnow().strftime('%Y%m%d%H%M')}",
        "trained_at": datetime.utcnow().isoformat(),
        "champion_algorithm": champion_name,
        "champion_metrics": results[champion_name],
        "all_candidate_metrics": results,
        "feature_importance": feature_importance,
        "training_dataset_size": int(len(X_train)),
        "test_dataset_size": int(len(X_test)),
        "training_period": f"{data['train_df']['date'].min()} to {data['train_df']['date'].max()}",
        "test_period": f"{data['test_df']['date'].min()} to {data['test_df']['date'].max()}",
        "data_source": "AGMARKNET / eNAM Synthetic Historical Market Price Dataset",
        "target_variable": "modal_price (Rs/quintal)",
        "price_unit": "Rs/quintal",
        "supported_crops": supported_crops,
        "supported_markets": supported_markets,
        "price_range": price_range,
        "scientific_note": (
            "Prices are ML predictions based on historical patterns. "
            "They are NOT guaranteed market outcomes and should be used for "
            "decision support only. Actual prices depend on many real-world factors."
        ),
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info(f"Metadata saved: {METADATA_PATH}")

    # Optional MLflow logging
    try:
        import mlflow
        from backend.app.config import settings
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("KrishiRaksha_CropPriceForecast")
        with mlflow.start_run(run_name=f"{champion_name}_CropPrice_{datetime.utcnow().strftime('%Y%m%d')}"):
            mlflow.log_param("algorithm", champion_name)
            mlflow.log_param("train_size", len(X_train))
            mlflow.log_param("test_size", len(X_test))
            for k, v in results[champion_name].items():
                mlflow.log_metric(k, v)
            mlflow.log_artifact(MODEL_PATH)
            mlflow.log_artifact(METADATA_PATH)
        logger.info("MLflow run logged.")
    except Exception as e:
        logger.warning(f"MLflow logging skipped: {e}")

    return {
        "status": "SUCCESS",
        "champion": champion_name,
        "metrics": results[champion_name],
        "all_metrics": results,
        "version": metadata["version"],
        "training_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(train_price_forecast_model(), indent=2))
