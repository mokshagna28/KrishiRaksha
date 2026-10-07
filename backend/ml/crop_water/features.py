"""
Crop Water Requirement, Excess-Water Disease, Treatment & Recovery Feature Pipeline
Handles categorical encoding, numerical scaling, and stratified train/test splitting without data leakage.
"""

import os
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

NUMERICAL_FEATURES = [
    "soil_moisture",
    "recent_rainfall",
    "forecast_rainfall",
    "temperature",
    "humidity",
    "wind_speed"
]

CATEGORICAL_FEATURES = [
    "crop",
    "growth_stage",
    "soil_type"
]

TARGET_REGRESSION = "water_requirement_mm"
TARGET_CLASSIFICATION = "water_status"
TARGET_STRESS = "crop_stress_level"
TARGET_DISEASE = "crop_disease_stress"
TARGET_TREATMENT = "recommended_treatment"
TARGET_RECOVERY = "expected_recovery"

def build_preprocessor() -> ColumnTransformer:
    """
    Constructs a ColumnTransformer that standardizes numerical features
    and one-hot encodes categorical crop, growth stage, and soil attributes.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES)
        ],
        remainder="drop"
    )
    return preprocessor

def load_and_split_data(
    data_path: str = "data/crop_water/crop_water_requirement_data.csv",
    test_size: float = 0.20,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Loads empirical crop water dataset and performs stratified train/test split
    for all 5 target variables.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset file not found at {data_path}")

    df = pd.read_csv(data_path)
    
    # Feature matrix X
    X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
    
    # Target vectors
    y_reg = df[TARGET_REGRESSION]
    y_clf = df[TARGET_CLASSIFICATION]
    y_stress = df[TARGET_STRESS]
    y_disease = df[TARGET_DISEASE]
    y_treatment = df[TARGET_TREATMENT]
    y_recovery = df[TARGET_RECOVERY]

    # Stratified split using water_status + disease to maintain balanced distributions
    strat_key = df[TARGET_CLASSIFICATION].astype(str) + "_" + df[TARGET_DISEASE].astype(str)

    train_idx, test_idx = train_test_split(
        df.index,
        test_size=test_size,
        random_state=random_state,
        stratify=strat_key
    )

    return {
        "X_train": X.loc[train_idx],
        "X_test": X.loc[test_idx],
        "y_reg_train": y_reg.loc[train_idx],
        "y_reg_test": y_reg.loc[test_idx],
        "y_clf_train": y_clf.loc[train_idx],
        "y_clf_test": y_clf.loc[test_idx],
        "y_stress_train": y_stress.loc[train_idx],
        "y_stress_test": y_stress.loc[test_idx],
        "y_disease_train": y_disease.loc[train_idx],
        "y_disease_test": y_disease.loc[test_idx],
        "y_treatment_train": y_treatment.loc[train_idx],
        "y_treatment_test": y_treatment.loc[test_idx],
        "y_recovery_train": y_recovery.loc[train_idx],
        "y_recovery_test": y_recovery.loc[test_idx],
        "full_df": df
    }
