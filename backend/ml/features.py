"""
KRISHIRAKSHA AI - Machine Learning Feature Engineering

Engineers physically and meteorologically meaningful features for heavy rainfall risk prediction:
- Rolling antecedent rainfall sums (3-day, 7-day)
- Atmospheric moisture indicators (dew point depression, thermo-humidity index)
- Seasonal trigonometric cyclic components
- Momentum & gradient features
"""

import numpy as np
import pandas as pd
from typing import Tuple, List

FEATURE_NAMES = [
    "rainfall_lag1",
    "rainfall_lag2",
    "rainfall_lag3",
    "rainfall_sum_3d",
    "rainfall_sum_7d",
    "temperature",
    "humidity",
    "wind_speed",
    "dew_point_depression",
    "thi_index",
    "month_sin",
    "month_cos",
    "rain_trend_3d"
]

TARGET_COLUMN = "heavy_rain_risk"
FEATURES_VERSION = "v2.1"

def compute_meteorological_indices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes atmospheric and meteorological indices:
    - Dew Point Depression (T - Td): Smaller value indicates near-saturation / convective condensation.
    - Temperature-Humidity Index (THI): Thermodynamic energy index.
    - Cyclical month representations.
    """
    df = df.copy()

    # Dew point approximation (Magnus formula linear approx)
    # Td ~ T - ((100 - RH) / 5)
    df["dew_point_depression"] = (100.0 - df["humidity"]) / 5.0

    # Temperature-Humidity Index (THI)
    df["thi_index"] = (
        0.8 * df["temperature"] +
        (df["humidity"] / 100.0) * (df["temperature"] - 14.4) + 46.4
    )

    # Cyclical month
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"])
        months = dates.dt.month
    else:
        months = 7 # Default to monsoon peak if unprovided

    df["month_sin"] = np.sin(2 * np.pi * months / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * months / 12.0)

    return df

def engineer_features_from_historical_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds lag and rolling accumulation features grouped per station/district.
    Target: heavy_rain_risk = 1 if current day rainfall >= 64.5 mm (IMD Heavy Rain Standard).
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["state", "district", "date"]).reset_index(drop=True)

    # Create target label strictly based on IMD 64.5mm threshold
    df[TARGET_COLUMN] = (df["rainfall"] >= 64.5).astype(int)

    # Compute lags and rolling windows per district
    grouped = df.groupby(["state", "district"])

    df["rainfall_lag1"] = grouped["rainfall"].shift(1)
    df["rainfall_lag2"] = grouped["rainfall"].shift(2)
    df["rainfall_lag3"] = grouped["rainfall"].shift(3)

    # Antecedent rolling sums (soil saturation and hydrological accumulation)
    df["rainfall_sum_3d"] = grouped["rainfall"].transform(lambda x: x.shift(1).rolling(3, min_periods=1).sum())
    df["rainfall_sum_7d"] = grouped["rainfall"].transform(lambda x: x.shift(1).rolling(7, min_periods=1).sum())

    # Gradient/momentum
    df["rain_trend_3d"] = df["rainfall_lag1"] - df["rainfall_lag3"]

    # Fill NaN for initial lag days
    df["rainfall_lag1"] = df["rainfall_lag1"].fillna(0.0)
    df["rainfall_lag2"] = df["rainfall_lag2"].fillna(0.0)
    df["rainfall_lag3"] = df["rainfall_lag3"].fillna(0.0)
    df["rainfall_sum_3d"] = df["rainfall_sum_3d"].fillna(0.0)
    df["rainfall_sum_7d"] = df["rainfall_sum_7d"].fillna(0.0)
    df["rain_trend_3d"] = df["rain_trend_3d"].fillna(0.0)

    # Meteorological thermodynamic features
    df = compute_meteorological_indices(df)

    # Drop any leftover nulls
    df = df.dropna(subset=FEATURE_NAMES + [TARGET_COLUMN]).reset_index(drop=True)

    return df

def extract_features_single_observation(
    rainfall_history: List[float], # recent daily rainfall [yesterday, 2 days ago, 3 days ago, ...]
    temperature: float,
    humidity: float,
    wind_speed: float,
    month: int = 7
) -> pd.DataFrame:
    """
    Extracts feature vector for a real-time live district observation.
    """
    lag1 = float(rainfall_history[0]) if len(rainfall_history) > 0 else 0.0
    lag2 = float(rainfall_history[1]) if len(rainfall_history) > 1 else 0.0
    lag3 = float(rainfall_history[2]) if len(rainfall_history) > 2 else 0.0

    sum_3d = sum(rainfall_history[:3]) if len(rainfall_history) >= 3 else sum(rainfall_history)
    sum_7d = sum(rainfall_history[:7]) if len(rainfall_history) >= 7 else sum(rainfall_history)

    dew_point_dep = (100.0 - humidity) / 5.0
    thi = 0.8 * temperature + (humidity / 100.0) * (temperature - 14.4) + 46.4
    m_sin = np.sin(2 * np.pi * month / 12.0)
    m_cos = np.cos(2 * np.pi * month / 12.0)
    trend = lag1 - lag3

    data = {
        "rainfall_lag1": [lag1],
        "rainfall_lag2": [lag2],
        "rainfall_lag3": [lag3],
        "rainfall_sum_3d": [sum_3d],
        "rainfall_sum_7d": [sum_7d],
        "temperature": [temperature],
        "humidity": [humidity],
        "wind_speed": [wind_speed],
        "dew_point_depression": [dew_point_dep],
        "thi_index": [thi],
        "month_sin": [m_sin],
        "month_cos": [m_cos],
        "rain_trend_3d": [trend]
    }

    return pd.DataFrame(data, columns=FEATURE_NAMES)
