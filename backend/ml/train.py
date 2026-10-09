"""
KRISHIRAKSHA AI - Machine Learning Training & MLOps Pipeline

Phase 1 Champion Model: Logistic Regression (Basic / Initial ML Model)
Future Improvements (Phase 2): Random Forest Classifier, Gradient Boosting, XGBoost

Tracks runs, metrics, and parameters in MLflow experiment:
'Rainfall_Flood_Risk_MLOps'
"""

import os
import json
import logging
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import xgboost as xgb
import mlflow
import mlflow.sklearn

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.models.models import ModelVersion
from backend.ml.features import (
    engineer_features_from_historical_df,
    FEATURE_NAMES,
    TARGET_COLUMN,
    FEATURES_VERSION
)
from backend.ml.evaluate import evaluate_model_performance

logger = logging.getLogger("krishiraksha.ml_train")
logging.basicConfig(level=logging.INFO)

def train_and_evaluate_all_models(
    csv_path: str = "data/historical/historical_rainfall_samples.csv",
    artifacts_dir: str = "ml_artifacts"
):
    """
    Executes full ML training pipeline on historical meteorological observations.
    Trains Logistic Regression as the initial Champion Model (bundled with StandardScaler in a sklearn Pipeline),
    and benchmarks candidate models (Random Forest, Gradient Boosting, XGBoost) for academic comparison.
    """
    logger.info(f"Loading historical dataset from {csv_path}...")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Historical dataset not found at {csv_path}")

    raw_df = pd.read_csv(csv_path)
    logger.info(f"Raw observations loaded: {len(raw_df)} rows")

    # Feature Engineering
    engineered_df = engineer_features_from_historical_df(raw_df)
    logger.info(f"Engineered dataset size: {len(engineered_df)} rows with {len(FEATURE_NAMES)} features")

    X = engineered_df[FEATURE_NAMES]
    y = engineered_df[TARGET_COLUMN]

    # Stratified train/test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    logger.info(f"Training split: {len(X_train)} samples, Test split: {len(X_test)} samples")
    logger.info(f"Positive heavy rainfall cases in test set: {sum(y_test)} ({sum(y_test)/len(y_test)*100:.2f}%)")

    # Setup MLflow tracking
    os.makedirs(artifacts_dir, exist_ok=True)
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)

    candidate_models = {
        "LogisticRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=42
            ))
        ]),
        "RandomForest": RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            min_samples_split=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.08,
            max_depth=5,
            scale_pos_weight=max(1.0, (len(y_train) - sum(y_train)) / (sum(y_train) or 1.0)),
            eval_metric="logloss",
            random_state=42
        )
    }

    results = {}

    for name, clf in candidate_models.items():
        logger.info(f"Training candidate algorithm: {name}...")
        run_timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        with mlflow.start_run(run_name=f"{name}_{run_timestamp}"):
            # Fit model
            clf.fit(X_train, y_train)

            # Evaluate
            eval_metrics = evaluate_model_performance(clf, X_test, y_test, FEATURE_NAMES)
            eval_metrics["train_size"] = len(X_train)
            eval_metrics["test_size"] = len(X_test)
            eval_metrics["algorithm"] = name
            results[name] = eval_metrics

            logger.info(f"[{name}] Acc: {eval_metrics['accuracy']:.4f} | Prec: {eval_metrics['precision']:.4f} | Rec: {eval_metrics['recall']:.4f} | F1: {eval_metrics['f1_score']:.4f} | ROC-AUC: {eval_metrics['roc_auc']:.4f}")

            # Log to MLflow
            mlflow.log_params({
                "algorithm": name,
                "features_version": FEATURES_VERSION,
                "target": "heavy_rain_risk_gte_64_5mm",
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            })

            mlflow.log_metrics({
                "accuracy": eval_metrics["accuracy"],
                "precision": eval_metrics["precision"],
                "recall": eval_metrics["recall"],
                "f1_score": eval_metrics["f1_score"],
                "roc_auc": eval_metrics["roc_auc"]
            })

            try:
                mlflow.sklearn.log_model(
                    clf,
                    artifact_path=f"model_{name}",
                    serialization_format="cloudpickle"
                )
            except Exception as log_ex:
                logger.warning(f"Could not log full model artifact to mlflow: {log_ex}")

    # Primary requirement: Logistic Regression is the INITIAL CHAMPION MODEL for Phase 1
    champion_algorithm = "LogisticRegression"
    champion_model_instance = candidate_models[champion_algorithm]
    champion_eval_metrics = results[champion_algorithm]

    # Save champion model directly via joblib
    champion_path = os.path.join(artifacts_dir, "champion_model.joblib")
    metadata_path = os.path.join(artifacts_dir, "model_metadata.json")

    joblib.dump(champion_model_instance, champion_path)
    logger.info(f"Champion model saved: {champion_algorithm} (F1: {champion_eval_metrics['f1_score']:.4f}). Saved to {champion_path}")

    model_version_str = f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
    metadata = {
        "model_name": settings.MODEL_REGISTRY_NAME,
        "version": model_version_str,
        "algorithm": champion_algorithm,
        "model_type": "Logistic Regression (Basic Classification Pipeline with StandardScaler)",
        "champion_status": "Current Initial Champion Model (Phase 1)",
        "features_version": FEATURES_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_dataset_size": len(X_train),
        "test_dataset_size": len(X_test),
        "training_period": "2021-01-01 to 2023-12-31 (3 Years IMD Gridded Reanalysis)",
        "data_source": "IMD Open Data Portal / National Data Centre Pune (Verified Normals)",
        "metrics": champion_eval_metrics,
        "all_candidate_metrics": results,
        "academic_progression": {
            "phase_1": "Logistic Regression (Initial Champion)",
            "phase_2": "Random Forest (Future Improvement Candidate)",
            "phase_3": "Model Comparison & Benchmarking",
            "phase_4": "Selection of Champion Model"
        },
        "target_definition": "heavy_rain_risk (IMD Classification: Daily Rainfall >= 64.5 mm)",
        "distinction_note": "Logistic Regression is used as the initial baseline classification model. It transforms features using StandardScaler and predicts heavy rainfall risk probability. Flood/Waterlogging risk is assessed in the Risk Engine by synthesizing ML risk, official IMD district warnings, and cumulative 7-day soil saturation."
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Persist version to DB if accessible
    try:
        db = SessionLocal()
        db.query(ModelVersion).filter(ModelVersion.is_active == True).update({"is_active": False})

        mv = ModelVersion(
            model_name=settings.MODEL_REGISTRY_NAME,
            version=model_version_str,
            algorithm=champion_algorithm,
            accuracy=champion_eval_metrics["accuracy"],
            precision=champion_eval_metrics["precision"],
            recall=champion_eval_metrics["recall"],
            f1_score=champion_eval_metrics["f1_score"],
            roc_auc=champion_eval_metrics["roc_auc"],
            trained_at=datetime.utcnow(),
            artifact_path=champion_path,
            is_active=True
        )
        db.add(mv)
        db.commit()
        db.close()
        logger.info(f"Registered {settings.MODEL_REGISTRY_NAME} ({model_version_str}) in database registry")
    except Exception as ex:
        logger.warning(f"Could not record model to DB at this moment (DB might not be initialized yet): {ex}")

    return metadata

if __name__ == "__main__":
    train_and_evaluate_all_models()

