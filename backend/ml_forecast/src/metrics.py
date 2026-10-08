"""Forecast accuracy and interval metrics with safe zero handling."""

from __future__ import annotations

import numpy as np
import pandas as pd


def regression_metrics(actual, predicted) -> dict[str, float | int]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    valid = np.isfinite(actual) & np.isfinite(predicted)
    actual = actual[valid]
    predicted = predicted[valid]
    if actual.size == 0:
        return {"n": 0, "mae": np.nan, "rmse": np.nan, "smape_pct": np.nan, "r2": np.nan}
    error = predicted - actual
    denominator = np.abs(actual) + np.abs(predicted)
    smape = np.zeros_like(denominator, dtype=float)
    np.divide(
        200.0 * np.abs(error),
        denominator,
        out=smape,
        where=denominator > 1e-12,
    )
    total = np.sum((actual - actual.mean()) ** 2)
    r2 = 1.0 - np.sum(error**2) / total if total > 1e-12 else np.nan
    return {
        "n": int(actual.size),
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "smape_pct": float(np.mean(smape)),
        "r2": float(r2) if np.isfinite(r2) else np.nan,
    }


def summarize_predictions(predictions: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    records: list[dict] = []
    for keys, frame in predictions.groupby(group_columns, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_columns, keys))
        record.update(regression_metrics(frame["actual"], frame["prediction"]))
        records.append(record)
    return pd.DataFrame(records)


def horizon_bucket(horizon: int) -> str:
    if horizon <= 6:
        return "01-06h"
    if horizon <= 24:
        return "07-24h"
    if horizon <= 48:
        return "25-48h"
    return "49-72h"
