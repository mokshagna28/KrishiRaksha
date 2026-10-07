"""
Crop Water Requirement & Excess-Water Recovery Model Training Pipeline.
Trains and benchmarks multiple regression and classification algorithms
across 5 distinct ML tasks:
  1. Water Requirement (mm) [Regression]
  2. Water Status Classification [Classification]
  3. Excess-Water Disease/Stress Identification [Classification]
  4. Treatment/Pesticide Prediction [Classification]
  5. Post-Treatment Recovery Prediction [Classification]

Integrates with MLflow for experiment tracking and saves trained models & metrics metadata.
"""

import os
import json
import logging
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import mlflow

from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

from backend.ml.crop_water.features import (
    build_preprocessor, load_and_split_data,
    NUMERICAL_FEATURES, CATEGORICAL_FEATURES
)
from backend.app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("krishiraksha.crop_water.train")

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

def evaluate_classification_candidates(X_train_proc, y_train, X_test_proc, y_test, task_name: str):
    """Utility to benchmark Logistic Regression, Random Forest, and Gradient Boosting for a classification target."""
    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForestClassifier": RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42),
        "GradientBoostingClassifier": GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    }

    results = {}
    champion_name = None
    champion_model = None
    best_f1 = -float("inf")
    classes = sorted(list(np.unique(y_train)))

    logger.info(f"Benchmarking Classification Algorithms for {task_name}...")

    for name, model in candidates.items():
        with mlflow.start_run(run_name=f"CWR_{task_name}_{name}"):
            model.fit(X_train_proc, y_train)
            preds = model.predict(X_test_proc)

            acc = float(accuracy_score(y_test, preds))
            prec = float(precision_score(y_test, preds, average="weighted", zero_division=0))
            rec = float(recall_score(y_test, preds, average="weighted", zero_division=0))
            f1 = float(f1_score(y_test, preds, average="weighted", zero_division=0))
            cm = confusion_matrix(y_test, preds, labels=classes).tolist()

            results[name] = {
                "algorithm": name,
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "confusion_matrix": cm,
                "classes": classes
            }
            logger.info(f"  [{name}] Accuracy: {acc*100:.2f}%, F1-Score: {f1:.4f}")

            mlflow.log_params({"task": task_name, "algorithm": name})
            mlflow.log_metrics({"accuracy": acc, "precision": prec, "recall": rec, "f1_score": f1})

            if f1 > best_f1:
                best_f1 = f1
                champion_name = name
                champion_model = model

    logger.info(f"🏆 Champion for {task_name}: {champion_name} (F1 = {best_f1:.4f})")
    return champion_name, champion_model, results

def train_and_evaluate_all():
    logger.info("Initializing Crop Water & Recovery ML training pipeline...")
    
    # Configure MLflow
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment("krishiraksha_crop_water_recovery_intelligence")

    # 1. Load Data
    data_dict = load_and_split_data()
    X_train = data_dict["X_train"]
    X_test = data_dict["X_test"]
    full_df = data_dict["full_df"]

    logger.info(f"Loaded dataset: Train samples={len(X_train)}, Test samples={len(X_test)}")

    # 2. Fit Preprocessor
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_feature_names = list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    all_feature_names = NUMERICAL_FEATURES + cat_feature_names

    # ═══════════════════════════════════════════════════════════════════════
    # TASK 1: REGRESSION BENCHMARKING (Water Requirement mm)
    # ═══════════════════════════════════════════════════════════════════════
    y_reg_train = data_dict["y_reg_train"]
    y_reg_test = data_dict["y_reg_test"]

    regression_candidates = {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42),
        "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    }

    reg_results = {}
    champion_reg_name = None
    champion_reg_model = None
    best_r2 = -float("inf")

    logger.info("Benchmarking Regression Algorithms for Water Requirement (mm)...")
    for name, model in regression_candidates.items():
        with mlflow.start_run(run_name=f"CWR_WaterReq_{name}"):
            model.fit(X_train_proc, y_reg_train)
            preds = model.predict(X_test_proc)

            mae = float(mean_absolute_error(y_reg_test, preds))
            rmse = float(np.sqrt(mean_squared_error(y_reg_test, preds)))
            r2 = float(r2_score(y_reg_test, preds))

            reg_results[name] = {
                "algorithm": name,
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2_score": round(r2, 4)
            }
            logger.info(f"  [{name}] MAE: {mae:.3f} mm, RMSE: {rmse:.3f} mm, R²: {r2:.4f}")

            mlflow.log_params({"task": "water_requirement", "algorithm": name})
            mlflow.log_metrics({"mae": mae, "rmse": rmse, "r2_score": r2})

            if r2 > best_r2:
                best_r2 = r2
                champion_reg_name = name
                champion_reg_model = model

    logger.info(f"🏆 Champion Regressor: {champion_reg_name} (R² = {best_r2:.4f})")

    # ═══════════════════════════════════════════════════════════════════════
    # TASK 2: WATER STATUS CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════════════
    champion_clf_name, champion_clf_model, clf_results = evaluate_classification_candidates(
        X_train_proc, data_dict["y_clf_train"], X_test_proc, data_dict["y_clf_test"], "WaterStatus"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # TASK 3: CROP STRESS LEVEL & DISEASE CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════════════
    logger.info("Training Secondary Classifier for Crop Stress Level...")
    stress_model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    stress_model.fit(X_train_proc, data_dict["y_stress_train"])
    stress_preds = stress_model.predict(X_test_proc)
    stress_f1 = float(f1_score(data_dict["y_stress_test"], stress_preds, average="weighted", zero_division=0))

    champion_disease_name, champion_disease_model, disease_results = evaluate_classification_candidates(
        X_train_proc, data_dict["y_disease_train"], X_test_proc, data_dict["y_disease_test"], "CropDiseaseStress"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # TASK 4: RECOMMENDED TREATMENT / PESTICIDE PREDICTION
    # ═══════════════════════════════════════════════════════════════════════
    champion_treatment_name, champion_treatment_model, treatment_results = evaluate_classification_candidates(
        X_train_proc, data_dict["y_treatment_train"], X_test_proc, data_dict["y_treatment_test"], "TreatmentPrediction"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # TASK 5: EXPECTED RECOVERY PREDICTION
    # ═══════════════════════════════════════════════════════════════════════
    champion_recovery_name, champion_recovery_model, recovery_results = evaluate_classification_candidates(
        X_train_proc, data_dict["y_recovery_train"], X_test_proc, data_dict["y_recovery_test"], "RecoveryPrediction"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # FEATURE IMPORTANCE CALCULATION
    # ═══════════════════════════════════════════════════════════════════════
    if hasattr(champion_clf_model, "feature_importances_"):
        raw_importances = champion_clf_model.feature_importances_
    else:
        rf_clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
        rf_clf.fit(X_train_proc, data_dict["y_clf_train"])
        raw_importances = rf_clf.feature_importances_

    feature_importance_agg = {}
    for feat_name, imp in zip(all_feature_names, raw_importances):
        parent_name = feat_name
        for orig in CATEGORICAL_FEATURES:
            if feat_name.startswith(f"cat__{orig}"):
                parent_name = orig
                break
            elif feat_name.startswith(f"num__"):
                parent_name = feat_name.replace("num__", "")
                break
        feature_importance_agg[parent_name] = feature_importance_agg.get(parent_name, 0.0) + float(imp)

    total_imp = sum(feature_importance_agg.values())
    feature_importance_clean = {
        k: round(v / total_imp, 4) for k, v in sorted(feature_importance_agg.items(), key=lambda item: item[1], reverse=True)
    }

    # Extract Treatment Metadata Mapping Table
    treatment_meta_map = {}
    for _, row in full_df.drop_duplicates(subset=["recommended_treatment"]).iterrows():
        cat = str(row["treatment_category"]) if pd.notna(row["treatment_category"]) else "N/A"
        active = str(row["active_ingredient"]) if pd.notna(row["active_ingredient"]) else "N/A"
        app_info = str(row["application_info"]) if pd.notna(row["application_info"]) else "N/A"
        treatment_meta_map[str(row["recommended_treatment"])] = {
            "treatment_category": cat,
            "active_ingredient": active,
            "application_info": app_info
        }

    # ═══════════════════════════════════════════════════════════════════════
    # SAVE MODEL ARTIFACTS & METADATA
    # ═══════════════════════════════════════════════════════════════════════
    metadata = {
        "module": "crop_water_recovery_intelligence",
        "version": "2.0.0",
        "trained_at": datetime.utcnow().isoformat(),
        "training_dataset_size": len(X_train),
        "test_dataset_size": len(X_test),
        "dataset_source": "FAO-56 & ICAR Empirical Benchmark (data/crop_water/crop_water_requirement_data.csv)",
        "regression": {
            "champion_algorithm": champion_reg_name,
            "metrics": reg_results[champion_reg_name],
            "all_candidates": reg_results
        },
        "classification": {
            "champion_algorithm": champion_clf_name,
            "metrics": clf_results[champion_clf_name],
            "all_candidates": clf_results
        },
        "stress_classification": {
            "algorithm": "GradientBoostingClassifier",
            "f1_score": round(stress_f1, 4)
        },
        "disease_classification": {
            "champion_algorithm": champion_disease_name,
            "metrics": disease_results[champion_disease_name],
            "all_candidates": disease_results
        },
        "treatment_classification": {
            "champion_algorithm": champion_treatment_name,
            "metrics": treatment_results[champion_treatment_name],
            "all_candidates": treatment_results
        },
        "recovery_classification": {
            "champion_algorithm": champion_recovery_name,
            "metrics": recovery_results[champion_recovery_name],
            "all_candidates": recovery_results
        },
        "treatment_metadata": treatment_meta_map,
        "feature_importance": feature_importance_clean,
        "supported_crops": sorted(list(full_df["crop"].unique())),
        "supported_stages": sorted(list(full_df["growth_stage"].unique())),
        "supported_soils": sorted(list(full_df["soil_type"].unique())),
    }

    joblib.dump(champion_reg_model, os.path.join(MODELS_DIR, "crop_water_regressor.joblib"))
    joblib.dump(champion_clf_model, os.path.join(MODELS_DIR, "crop_water_classifier.joblib"))
    joblib.dump(stress_model, os.path.join(MODELS_DIR, "crop_stress_classifier.joblib"))
    joblib.dump(champion_disease_model, os.path.join(MODELS_DIR, "crop_disease_classifier.joblib"))
    joblib.dump(champion_treatment_model, os.path.join(MODELS_DIR, "crop_treatment_classifier.joblib"))
    joblib.dump(champion_recovery_model, os.path.join(MODELS_DIR, "crop_recovery_classifier.joblib"))
    joblib.dump(preprocessor, os.path.join(MODELS_DIR, "crop_water_preprocessor.joblib"))

    meta_path = os.path.join(MODELS_DIR, "crop_water_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"All 5 ML model artifacts and metadata saved to {MODELS_DIR}/")
    return metadata

if __name__ == "__main__":
    train_and_evaluate_all()
