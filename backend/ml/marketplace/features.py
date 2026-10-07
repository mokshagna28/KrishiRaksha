"""
Crop Price Time-Series Feature Engineering & Temporal Train/Test Pipeline.
Constructs lag features, rolling statistics, and seasonal attributes
using chronological time-series splitting to prevent data leakage.
"""

import os
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

NUMERICAL_FEATURES = [
    "price_lag_1",
    "price_lag_3",
    "price_lag_7",
    "price_roll_mean_7",
    "price_roll_std_7",
    "arrivals_quintal",
    "month",
    "dayofweek"
]

CATEGORICAL_FEATURES = [
    "crop",
    "market",
    "state"
]

TARGET_PRICE = "modal_price"

def build_preprocessor() -> ColumnTransformer:
    """Construct ColumnTransformer for numerical scaling and one-hot categorical encoding."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES)
        ],
        remainder="drop"
    )
    return preprocessor

def create_time_series_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate lag features and rolling statistics per crop-market time series."""
    df = df.sort_values(["crop", "market", "date"]).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    df["dayofweek"] = df["date"].dt.dayofweek

    # Group by crop and market to create lag features without cross-market contamination
    grouped = df.groupby(["crop", "market"])

    df["price_lag_1"] = grouped["modal_price"].shift(1)
    df["price_lag_3"] = grouped["modal_price"].shift(3)
    df["price_lag_7"] = grouped["modal_price"].shift(7)
    df["price_roll_mean_7"] = grouped["modal_price"].transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean())
    df["price_roll_std_7"] = grouped["modal_price"].transform(lambda x: x.shift(1).rolling(7, min_periods=1).std().fillna(0))

    # Fill initial boundary NaNs with backward/forward fill within group
    df[NUMERICAL_FEATURES] = df.groupby(["crop", "market"])[NUMERICAL_FEATURES].bfill().ffill()
    df = df.dropna(subset=[TARGET_PRICE] + NUMERICAL_FEATURES).reset_index(drop=True)

    return df

def load_and_split_data(
    data_path: str = "data/marketplace/crop_price_history.csv",
    test_ratio: float = 0.20
) -> Dict[str, Any]:
    """
    Loads historical market price data and performs strict chronological train/test split.
    Prevents future-data leakage into earlier training iterations.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Market dataset file not found at {data_path}")

    raw_df = pd.read_csv(data_path)
    df = create_time_series_features(raw_df)

    # Sort strictly by date for time-based split
    df = df.sort_values("date").reset_index(drop=True)
    split_idx = int(len(df) * (1.0 - test_ratio))

    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    X_train = train_df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
    y_train = train_df[TARGET_PRICE]

    X_test = test_df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
    y_test = test_df[TARGET_PRICE]

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "train_df": train_df,
        "test_df": test_df,
        "full_df": df
    }
