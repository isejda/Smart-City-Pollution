"""Recursive ML and baseline forecasting primitives."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .features import build_recursive_feature_row


def clamp(value: float, bounds: tuple[float, float]) -> float:
    return float(np.clip(value, bounds[0], bounds[1]))


def _last_valid(history: pd.Series, before: pd.Timestamp) -> float:
    values = history.loc[:before].dropna()
    return float(values.iloc[-1]) if not values.empty else np.nan


def baseline_value(history: pd.Series, timestamp: pd.Timestamp, method: str) -> float:
    if method == "persistence":
        return _last_valid(history, timestamp - pd.Timedelta(hours=1))
    if method == "seasonal_24h":
        value = history.get(timestamp - pd.Timedelta(hours=24), np.nan)
        return float(value) if pd.notna(value) else _last_valid(history, timestamp - pd.Timedelta(hours=1))
    if method == "seasonal_blend_24h_168h":
        candidates = [
            history.get(timestamp - pd.Timedelta(hours=24), np.nan),
            history.get(timestamp - pd.Timedelta(hours=168), np.nan),
        ]
        candidates = [float(value) for value in candidates if pd.notna(value)]
        return float(np.mean(candidates)) if candidates else _last_valid(history, timestamp - pd.Timedelta(hours=1))
    raise ValueError(f"Unknown baseline method: {method}")


def recursive_forecast(
    history: pd.Series,
    origin: pd.Timestamp,
    horizon_hours: int,
    model,
    model_name: str,
    sensor_id: str,
    sensor_categories: Sequence[str],
    feature_columns: Sequence[str],
    bounds: tuple[float, float],
    config: dict,
) -> pd.DataFrame:
    history = history.sort_index().copy()
    records: list[dict] = []
    for horizon in range(1, horizon_hours + 1):
        timestamp = origin + pd.Timedelta(hours=horizon)
        if model_name.startswith("hgb_"):
            features = build_recursive_feature_row(
                history=history,
                timestamp=timestamp,
                sensor_id=sensor_id,
                sensor_categories=sensor_categories,
                feature_columns=feature_columns,
                config=config,
            )
            prediction = float(model.predict(features)[0])
        else:
            prediction = baseline_value(history, timestamp, model_name)
        if not np.isfinite(prediction):
            break
        prediction = clamp(prediction, bounds)
        history.loc[timestamp] = prediction
        records.append(
            {
                "sensor_id": sensor_id,
                "origin": origin,
                "timestamp": timestamp,
                "horizon_hour": horizon,
                "prediction": prediction,
                "model_name": model_name,
            }
        )
    return pd.DataFrame(records)


def eligible_sensors_at_origin(
    hourly: pd.DataFrame,
    target: str,
    origin: pd.Timestamp,
    staleness_hours: int,
) -> list[str]:
    eligible: list[str] = []
    for sensor_id, frame in hourly[hourly["timestamp"] <= origin].groupby("sensor_id"):
        observed_column = f"{target}__observed"
        if observed_column in frame.columns:
            valid = frame.loc[frame[observed_column].eq(1), "timestamp"]
        else:
            valid = frame.loc[frame[target].notna(), "timestamp"]
        if valid.empty:
            continue
        age = (origin - valid.max()) / pd.Timedelta(hours=1)
        if age <= staleness_hours:
            eligible.append(str(sensor_id))
    return eligible


def run_backtest(
    hourly: pd.DataFrame,
    target: str,
    origins: Sequence[pd.Timestamp],
    horizon_hours: int,
    model,
    model_name: str,
    sensor_categories: Sequence[str],
    feature_columns: Sequence[str],
    bounds: tuple[float, float],
    config: dict,
) -> pd.DataFrame:
    results: list[pd.DataFrame] = []
    staleness = int(config["validation"]["maximum_history_staleness_hours"])
    for origin in origins:
        for sensor_id in eligible_sensors_at_origin(hourly, target, origin, staleness):
            if str(sensor_id) not in {str(value) for value in sensor_categories}:
                continue
            sensor_frame = hourly[hourly["sensor_id"].eq(sensor_id)].set_index("timestamp").sort_index()
            history = sensor_frame.loc[:origin, target].copy()
            observed_column = f"{target}__observed"
            if observed_column in sensor_frame.columns:
                history = history.where(sensor_frame.loc[:origin, observed_column].eq(1))
            forecast = recursive_forecast(
                history=history,
                origin=origin,
                horizon_hours=horizon_hours,
                model=model,
                model_name=model_name,
                sensor_id=sensor_id,
                sensor_categories=sensor_categories,
                feature_columns=feature_columns,
                bounds=bounds,
                config=config,
            )
            if forecast.empty:
                continue
            observed_column = f"{target}__observed"
            actual = sensor_frame[target].copy()
            if observed_column in sensor_frame.columns:
                actual = actual.where(sensor_frame[observed_column].eq(1))
            actual = actual.rename("actual")
            forecast = forecast.join(actual, on="timestamp")
            forecast["target"] = target
            results.append(forecast)
    if not results:
        return pd.DataFrame(
            columns=["sensor_id", "origin", "timestamp", "horizon_hour", "prediction", "model_name", "actual", "target"]
        )
    return pd.concat(results, ignore_index=True)
