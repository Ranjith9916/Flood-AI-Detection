"""
ml/preprocessing/clean_weather.py
Cleans and preprocesses meteorological time-series.
Handles missing values, physical bound clipping, and cyclical temporal encodings.
"""

import math
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd


def encode_cyclical_time(dt: datetime) -> dict[str, float]:
    """Encodes diurnal (hour) and seasonal (day-of-year) cycles into sin/cos components."""
    hour = dt.hour + dt.minute / 60.0
    doy = dt.timetuple().tm_yday

    hour_sin = math.sin(2.0 * math.pi * hour / 24.0)
    hour_cos = math.cos(2.0 * math.pi * hour / 24.0)

    doy_sin = math.sin(2.0 * math.pi * doy / 365.25)
    doy_cos = math.cos(2.0 * math.pi * doy / 365.25)

    return {
        "hour_sin": round(hour_sin, 4),
        "hour_cos": round(hour_cos, 4),
        "doy_sin": round(doy_sin, 4),
        "doy_cos": round(doy_cos, 4),
    }


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans weather/rainfall dataframe:
    - Sorts chronologically
    - Interpolates small gaps (<3 hours)
    - Clips negative precipitation
    - Imputes remaining missing values with median
    """
    df = df.copy()
    if "observation_time" in df.columns:
        df["observation_time"] = pd.to_datetime(df["observation_time"], utc=True)
        df = df.sort_values("observation_time")

    if "rainfall_mm" in df.columns:
        df["rainfall_mm"] = df["rainfall_mm"].clip(lower=0.0)

    # Numeric columns interpolation
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].interpolate(method="linear", limit=3)
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())

    return df
