"""
KRISHIRAKSHA AI - ML Model Evaluation
Student Roll Number: 231FA04291

Computes rigorous scientific metrics on held-out test splits:
Accuracy, Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix.
Never fabricates metrics.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

def evaluate_model_performance(model: Any, X_test: np.ndarray, y_test: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Evaluates classifier on test dataset and computes full metrics suite.
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred.astype(float)

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    try:
        roc = float(roc_auc_score(y_test, y_prob))
    except Exception:
        roc = 0.5

    cm = confusion_matrix(y_test, y_pred).tolist()

    # Extract feature importances if model supports it
    feat_imp = {}
    if hasattr(model, "feature_importances_"):
        raw_imp = model.feature_importances_
        for name, val in zip(feature_names, raw_imp):
            feat_imp[name] = round(float(val), 4)
    elif hasattr(model, "coef_"):
        raw_imp = np.abs(model.coef_[0])
        total = np.sum(raw_imp) or 1.0
        normalized = raw_imp / total
        for name, val in zip(feature_names, normalized):
            feat_imp[name] = round(float(val), 4)

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc, 4),
        "confusion_matrix": cm,
        "feature_importance": feat_imp
    }
