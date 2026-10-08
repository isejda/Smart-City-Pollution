"""Leakage-safe lag, rolling, calendar, and sensor features."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
import pandas as pd


def rolling_minimum_values(window: int, config: dict) -> int:
    """Return the shared training/serving minimum for a rolling statistic."""

    divisor = int(config["features"].get("rolling_minimum_divisor", 3))
    if divisor < 1:
        raise ValueError("rolling_minimum_divisor must be at least 1")
    return max(2, min(window, window // divisor))


def calendar_features(timestamp: pd.Timestamp) -> dict[str, float]:
    hour_angle = 2.0 * math.pi * timestamp.hour / 24.0
    dow_angle = 2.0 * math.pi * timestamp.dayofweek / 7.0
    doy_angle = 2.0 * math.pi * (timestamp.dayofyear - 1) / 365.25
    return {
        "hour_sin": math.sin(hour_angle),
        "hour_cos": math.cos(hour_angle),
        "dow_sin": math.sin(dow_angle),
        "dow_cos": math.cos(dow_angle),
        "doy_sin": math.sin(doy_angle),
        "doy_cos": math.cos(doy_angle),
    }


def build_feature_frame(
    hourly: pd.DataFrame,
    target: str,
    sensor_categories: Sequence[str],
    config: dict,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    lags = [int(value) for value in config["features"]["lags_hours"]]
    windows = [int(value) for value in config["features"]["rolling_windows_hours"]]
    minimum_lags = int(config["features"]["minimum_lag_values"])
    frames: list[pd.DataFrame] = []

    for sensor_id, sensor_frame in hourly.groupby("sensor_id", sort=True):
        sensor_frame = sensor_frame.sort_values("timestamp").set_index("timestamp")
        observed_column = f"{target}__observed"
        series = sensor_frame[target].astype(float)
        if observed_column in sensor_frame.columns:
            # Interpolation is retained as an audited usable-data field, but it
            # is not a modeling input. A linear value immediately before label
            # t can depend on the observed endpoint at t; masking to observed
            # hours prevents that endpoint from leaking into lag/rolling
            # features and matches live inference at a truncated origin.
            series = series.where(sensor_frame[observed_column].eq(1))
        features = pd.DataFrame(index=series.index)
        for lag in lags:
            features[f"lag_{lag}h"] = series.shift(lag)
        shifted = series.shift(1)
        for window in windows:
            rolling = shifted.rolling(
                window=window,
                min_periods=rolling_minimum_values(window, config),
            )
            features[f"rolling_mean_{window}h"] = rolling.mean()
            features[f"rolling_std_{window}h"] = rolling.std()
        features["hour_sin"] = np.sin(2 * np.pi * features.index.hour / 24.0)
        features["hour_cos"] = np.cos(2 * np.pi * features.index.hour / 24.0)
        features["dow_sin"] = np.sin(2 * np.pi * features.index.dayofweek / 7.0)
        features["dow_cos"] = np.cos(2 * np.pi * features.index.dayofweek / 7.0)
        features["doy_sin"] = np.sin(2 * np.pi * (features.index.dayofyear - 1) / 365.25)
        features["doy_cos"] = np.cos(2 * np.pi * (features.index.dayofyear - 1) / 365.25)
        for category in sensor_categories:
            features[f"sensor__{category}"] = 1.0 if str(sensor_id) == str(category) else 0.0
        features["lag_values_available"] = features[[f"lag_{lag}h" for lag in lags]].notna().sum(axis=1)
        features["target"] = series
        if observed_column in sensor_frame.columns:
            features["target_observed"] = sensor_frame[observed_column].astype(int)
        else:
            features["target_observed"] = series.notna().astype(int)
        features["sensor_id"] = str(sensor_id)
        features["timestamp"] = features.index
        features = features[features["lag_values_available"] >= minimum_lags]
        frames.append(features.reset_index(drop=True))

    dataset = pd.concat(frames, ignore_index=True)
    metadata = dataset[["sensor_id", "timestamp", "target_observed"]].copy()
    y = dataset.pop("target")
    dataset = dataset.drop(
        columns=["sensor_id", "timestamp", "target_observed", "lag_values_available"]
    )
    return dataset.astype(float), y.astype(float), metadata


def build_recursive_feature_row(
    history: pd.Series,
    timestamp: pd.Timestamp,
    sensor_id: str,
    sensor_categories: Sequence[str],
    feature_columns: Sequence[str],
    config: dict,
) -> pd.DataFrame:
    lags = [int(value) for value in config["features"]["lags_hours"]]
    windows = [int(value) for value in config["features"]["rolling_windows_hours"]]
    values: dict[str, float] = {}
    for lag in lags:
        values[f"lag_{lag}h"] = history.get(timestamp - pd.Timedelta(hours=lag), np.nan)
    for window in windows:
        start = timestamp - pd.Timedelta(hours=window)
        end = timestamp - pd.Timedelta(hours=1)
        window_values = history.loc[start:end]
        minimum = rolling_minimum_values(window, config)
        available = int(window_values.notna().sum())
        values[f"rolling_mean_{window}h"] = (
            float(window_values.mean()) if available >= minimum else np.nan
        )
        values[f"rolling_std_{window}h"] = (
            float(window_values.std()) if available >= minimum else np.nan
        )
    values.update(calendar_features(timestamp))
    for category in sensor_categories:
        values[f"sensor__{category}"] = 1.0 if str(sensor_id) == str(category) else 0.0
    frame = pd.DataFrame([values])
    for column in feature_columns:
        if column not in frame:
            frame[column] = 0.0 if column.startswith("sensor__") else np.nan
    return frame[list(feature_columns)].astype(float)
