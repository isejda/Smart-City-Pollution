"""Training, time-aware model selection, backtesting, and artifact creation."""

from __future__ import annotations

import json
import platform
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance

from .data_io import (
    canonical_mapping_sha256,
    model_code_tree_sha256,
    sha256_file,
    write_csv_safe,
    write_json,
)
from .features import build_feature_frame
from .forecasting import recursive_forecast, run_backtest
from .metrics import horizon_bucket, regression_metrics, summarize_predictions
from .preprocessing import PreparedData


warnings.filterwarnings(
    "ignore",
    message=r"`sklearn\.utils\.parallel\.delayed` should be used.*",
    category=UserWarning,
)


@dataclass
class TrainingOutputs:
    bundle_path: Path
    manifest_path: Path
    forecast_path: Path
    test_predictions_path: Path
    metrics_path: Path
    selection_path: Path
    feature_importance_path: Path
    active_series_path: Path
    split_summary_path: Path


class ResidualSeasonalRegressor(RegressorMixin, BaseEstimator):
    """Predict a correction on top of the 24-hour seasonal baseline."""

    def __init__(self, base_model):
        self.base_model = base_model

    def fit(self, X: pd.DataFrame, y: pd.Series):
        seasonal = X["lag_24h"]
        valid = seasonal.notna() & y.notna()
        if int(valid.sum()) < 100:
            raise ValueError("Insufficient rows with a 24-hour lag for residual training")
        self.base_model.fit(X.loc[valid], y.loc[valid] - seasonal.loc[valid])
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        seasonal = X["lag_24h"].to_numpy(dtype=float)
        fallback = X["lag_1h"].to_numpy(dtype=float)
        recent_mean = X["rolling_mean_24h"].to_numpy(dtype=float)
        long_mean = X["rolling_mean_168h"].to_numpy(dtype=float)
        baseline = np.where(
            np.isfinite(seasonal),
            seasonal,
            np.where(
                np.isfinite(fallback),
                fallback,
                np.where(np.isfinite(recent_mean), recent_mean, long_mean),
            ),
        )
        residual = self.base_model.predict(X)
        return baseline + residual


def _target_bounds(config: dict, target: str) -> tuple[float, float]:
    specification = config["data"]["targets"][target]
    return float(specification["lower_bound"]), float(specification["upper_bound"])


def _fit_hgb(X: pd.DataFrame, y: pd.Series, parameters: dict, config: dict):
    parameters = dict(parameters)
    mode = parameters.pop("mode", "absolute")
    base_model = HistGradientBoostingRegressor(
        loss=config["model"]["loss"],
        learning_rate=float(parameters["learning_rate"]),
        max_iter=int(parameters["max_iter"]),
        max_leaf_nodes=int(parameters["max_leaf_nodes"]),
        min_samples_leaf=int(parameters["min_samples_leaf"]),
        l2_regularization=float(parameters["l2_regularization"]),
        early_stopping=False,
        random_state=int(config["project"]["random_seed"]),
    )
    if mode == "residual_to_seasonal_24h":
        return ResidualSeasonalRegressor(base_model).fit(X, y)
    return base_model.fit(X, y)


def _make_origins(start: pd.Timestamp, end: pd.Timestamp, horizon_hours: int, count: int) -> list[pd.Timestamp]:
    latest = end - pd.Timedelta(hours=horizon_hours)
    if latest < start:
        return []
    values = pd.date_range(start=start, end=latest, periods=count)
    return sorted({pd.Timestamp(value).floor("h") for value in values})


def compute_splits(hourly: pd.DataFrame, config: dict) -> dict:
    data_end = pd.Timestamp(hourly["timestamp"].max()).floor("h")
    test_days = int(config["validation"]["test_days"])
    validation_days = int(config["validation"]["validation_days"])
    horizon = int(config["validation"]["forecast_horizon_hours"])
    test_start = (data_end - pd.Timedelta(days=test_days)).floor("h")
    validation_end = test_start - pd.Timedelta(hours=1)
    validation_start = validation_end - pd.Timedelta(days=validation_days) + pd.Timedelta(hours=1)
    train_end = validation_start - pd.Timedelta(hours=1)
    validation_origins = _make_origins(
        validation_start,
        validation_end,
        horizon,
        int(config["validation"]["validation_origin_count"]),
    )
    test_origins = _make_origins(
        test_start,
        data_end,
        horizon,
        int(config["validation"]["test_origin_count"]),
    )
    return {
        "data_end": data_end,
        "train_end": train_end,
        "validation_start": validation_start,
        "validation_end": validation_end,
        "test_start": test_start,
        "test_end": data_end,
        "validation_origins": validation_origins,
        "test_origins": test_origins,
        "forecast_horizon_hours": horizon,
    }


def _sensor_categories(hourly: pd.DataFrame, target: str, cutoff: pd.Timestamp | None = None) -> list[str]:
    observed_column = f"{target}__observed"
    if observed_column in hourly.columns:
        frame = hourly[hourly[observed_column].eq(1)]
    else:
        frame = hourly[hourly[target].notna()]
    if cutoff is not None:
        frame = frame[frame["timestamp"] <= cutoff]
    return sorted(frame["sensor_id"].astype(str).unique().tolist())


def _training_matrices(
    hourly: pd.DataFrame,
    target: str,
    sensor_categories: Sequence[str],
    cutoff: pd.Timestamp | None,
    config: dict,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    X, y, metadata = build_feature_frame(hourly, target, sensor_categories, config)
    valid = y.notna() & metadata["target_observed"].eq(1)
    if cutoff is not None:
        valid &= metadata["timestamp"].le(cutoff)
    return X.loc[valid].reset_index(drop=True), y.loc[valid].reset_index(drop=True), metadata.loc[valid].reset_index(drop=True)


def _candidate_validation(
    prepared: PreparedData,
    target: str,
    split: dict,
    config: dict,
) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    hourly = prepared.hourly
    horizon = int(split["forecast_horizon_hours"])
    categories = _sensor_categories(hourly, target, split["train_end"])
    X_train, y_train, _ = _training_matrices(hourly, target, categories, split["train_end"], config)
    if len(y_train) < 200:
        raise ValueError(f"Insufficient training rows for {target}: {len(y_train)}")
    bounds = _target_bounds(config, target)
    rows: list[dict] = []
    predictions: list[pd.DataFrame] = []
    fitted_models: dict[str, object] = {}

    for candidate_name, parameters in config["model"]["candidates"].items():
        model = _fit_hgb(X_train, y_train, parameters, config)
        fitted_models[candidate_name] = model
        forecast = run_backtest(
            hourly=hourly,
            target=target,
            origins=split["validation_origins"],
            horizon_hours=horizon,
            model=model,
            model_name=candidate_name,
            sensor_categories=categories,
            feature_columns=X_train.columns,
            bounds=bounds,
            config=config,
        )
        metrics = regression_metrics(forecast["actual"], forecast["prediction"])
        rows.append({"target": target, "model_name": candidate_name, "stage": "validation", **metrics})
        predictions.append(forecast)

    for baseline in config["model"]["baseline_candidates"]:
        forecast = run_backtest(
            hourly=hourly,
            target=target,
            origins=split["validation_origins"],
            horizon_hours=horizon,
            model=None,
            model_name=baseline,
            sensor_categories=categories,
            feature_columns=X_train.columns,
            bounds=bounds,
            config=config,
        )
        metrics = regression_metrics(forecast["actual"], forecast["prediction"])
        rows.append({"target": target, "model_name": baseline, "stage": "validation", **metrics})
        predictions.append(forecast)

    selection = pd.DataFrame(rows).sort_values(["mae", "rmse"], na_position="last")
    eligible = selection[selection["n"] >= 50]
    champion_name = str((eligible if not eligible.empty else selection).iloc[0]["model_name"])
    ml_rows = selection[selection["model_name"].str.startswith("hgb_")]
    best_ml_name = str(ml_rows.iloc[0]["model_name"])
    validation_predictions = pd.concat(predictions, ignore_index=True)
    champion_predictions = validation_predictions[
        validation_predictions["model_name"].eq(champion_name)
        & validation_predictions["actual"].notna()
    ].copy()
    absolute_errors = (champion_predictions["actual"] - champion_predictions["prediction"]).abs()
    calibration = {
        "absolute_error_q80": float(absolute_errors.quantile(0.80)) if not absolute_errors.empty else np.nan,
        "absolute_error_q95": float(absolute_errors.quantile(0.95)) if not absolute_errors.empty else np.nan,
        "calibration_rows": int(len(absolute_errors)),
    }
    info = {
        "champion_name": champion_name,
        "best_ml_name": best_ml_name,
        "best_ml_parameters": config["model"]["candidates"][best_ml_name],
        "sensor_categories": categories,
        "feature_columns": X_train.columns.tolist(),
        "training_rows": int(len(y_train)),
        "calibration": calibration,
    }
    return selection, info, champion_predictions


def _fit_for_cutoff(
    hourly: pd.DataFrame,
    target: str,
    candidate_name: str,
    cutoff: pd.Timestamp | None,
    config: dict,
) -> tuple[object, list[str], list[str], int]:
    categories = _sensor_categories(hourly, target, cutoff)
    X, y, _ = _training_matrices(hourly, target, categories, cutoff, config)
    model = _fit_hgb(X, y, config["model"]["candidates"][candidate_name], config)
    return model, categories, X.columns.tolist(), int(len(y))


def _test_target(
    prepared: PreparedData,
    target: str,
    selection_info: dict,
    split: dict,
    config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, object]:
    hourly = prepared.hourly
    best_ml_name = selection_info["best_ml_name"]
    model, categories, feature_columns, train_rows = _fit_for_cutoff(
        hourly, target, best_ml_name, split["validation_end"], config
    )
    bounds = _target_bounds(config, target)
    names = list(dict.fromkeys([selection_info["champion_name"], best_ml_name] + list(config["model"]["baseline_candidates"])))
    predictions: list[pd.DataFrame] = []
    for name in names:
        predictions.append(
            run_backtest(
                hourly=hourly,
                target=target,
                origins=split["test_origins"],
                horizon_hours=int(split["forecast_horizon_hours"]),
                model=model if name.startswith("hgb_") else None,
                model_name=name,
                sensor_categories=categories,
                feature_columns=feature_columns,
                bounds=bounds,
                config=config,
            )
        )
    combined = pd.concat(predictions, ignore_index=True)
    combined["horizon_bucket"] = combined["horizon_hour"].map(horizon_bucket)
    overall = summarize_predictions(combined, ["target", "model_name"])
    by_horizon = summarize_predictions(combined, ["target", "model_name", "horizon_bucket"])
    by_sensor = summarize_predictions(combined, ["target", "model_name", "sensor_id"])
    overall["stage"] = "test"
    by_horizon["stage"] = "test_by_horizon"
    by_sensor["stage"] = "test_by_sensor"
    overall["training_rows"] = train_rows
    by_horizon["training_rows"] = train_rows
    by_sensor["training_rows"] = train_rows

    X_all, y_all, metadata = build_feature_frame(hourly, target, categories, config)
    test_mask = (
        y_all.notna()
        & metadata["target_observed"].eq(1)
        & metadata["timestamp"].between(split["test_start"], split["test_end"])
    )
    X_test = X_all.loc[test_mask]
    y_test = y_all.loc[test_mask]
    # The residual wrapper adds its tree prediction to lag_24h, falling back to
    # lag_1h.  During permutation importance, shuffling a partially missing
    # seasonal column can create rows where both anchors are absent and the
    # wrapper correctly returns no finite point prediction.  Importance is a
    # diagnostic rather than the serving path, so evaluate this wrapper on the
    # common population where both anchors are defined.  Permutations then keep
    # the scoring population and denominator fixed.
    if isinstance(model, ResidualSeasonalRegressor):
        anchor_mask = X_test["lag_24h"].notna() & X_test["lag_1h"].notna()
        X_test = X_test.loc[anchor_mask]
        y_test = y_test.loc[anchor_mask]
    if len(X_test) > 1500:
        rng = np.random.default_rng(int(config["project"]["random_seed"]))
        chosen = rng.choice(X_test.index.to_numpy(), size=1500, replace=False)
        X_test = X_test.loc[chosen]
        y_test = y_test.loc[chosen]
    importance_records: list[dict] = []
    if len(X_test) >= 50:
        importance = permutation_importance(
            model,
            X_test,
            y_test,
            scoring="neg_mean_absolute_error",
            n_repeats=3,
            random_state=int(config["project"]["random_seed"]),
            n_jobs=1,
        )
        for feature, mean, std in zip(feature_columns, importance.importances_mean, importance.importances_std):
            importance_records.append(
                {
                    "target": target,
                    "feature": feature,
                    "importance_mae_increase": float(mean),
                    "importance_std": float(std),
                }
            )
    return (
        combined,
        pd.concat([overall, by_horizon, by_sensor], ignore_index=True),
        pd.DataFrame(importance_records),
        model,
    )


def _active_series(
    hourly: pd.DataFrame,
    target: str,
    origin: pd.Timestamp,
    config: dict,
    allowed_sensors: Sequence[str] | None = None,
) -> pd.DataFrame:
    max_age = int(config["deployment"]["active_sensor_max_age_hours"])
    window = int(config["deployment"]["recent_coverage_window_hours"])
    minimum_coverage = float(config["deployment"]["minimum_recent_target_coverage"])
    records: list[dict] = []
    allowed = {str(value) for value in allowed_sensors} if allowed_sensors is not None else None
    for sensor_id, frame in hourly.groupby("sensor_id", sort=True):
        frame = frame[frame["timestamp"] <= origin].sort_values("timestamp")
        observed_column = f"{target}__observed"
        observed_mask = (
            frame[observed_column].eq(1)
            if observed_column in frame.columns
            else frame[target].notna()
        )
        valid = frame[observed_mask]
        last_valid = pd.Timestamp(valid["timestamp"].max()) if not valid.empty else pd.NaT
        age = (
            float((origin - last_valid) / pd.Timedelta(hours=1))
            if pd.notna(last_valid)
            else np.nan
        )
        recent_start = origin - pd.Timedelta(hours=window - 1)
        recent = frame[frame["timestamp"].between(recent_start, origin)]
        if observed_column in recent.columns:
            observed_hours = int(recent[observed_column].eq(1).sum())
        else:
            observed_hours = int(recent[target].notna().sum())
        usable_hours = int(recent[target].notna().sum())
        coverage = float(observed_hours / window)
        usable_coverage = float(usable_hours / window)
        known_sensor = allowed is None or str(sensor_id) in allowed
        if not known_sensor:
            reason = "UNKNOWN_SENSOR"
        elif valid.empty:
            reason = "NO_VALID_HISTORY"
        elif age > max_age:
            reason = "STALE"
        elif coverage < minimum_coverage:
            reason = "LOW_OBSERVED_COVERAGE"
        else:
            reason = "ACTIVE"
        records.append(
            {
                "sensor_id": str(sensor_id),
                "target": target,
                "last_valid": last_valid,
                "age_hours": age,
                "observed_recent_hours": observed_hours,
                "usable_recent_hours": usable_hours,
                "recent_coverage": coverage,
                "usable_recent_coverage": usable_coverage,
                "known_sensor_category": known_sensor,
                "eligibility_reason": reason,
                "active": reason == "ACTIVE",
            }
        )
    return pd.DataFrame(records)


def _generate_final_forecast(
    prepared: PreparedData,
    target_models: dict,
    origin: pd.Timestamp,
    config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    hourly = prepared.hourly
    metadata = prepared.sensor_metadata.set_index("sensor_id")
    horizon = int(config["deployment"]["forecast_horizon_hours"])
    forecasts: list[pd.DataFrame] = []
    active_records: list[pd.DataFrame] = []

    for target, target_info in target_models.items():
        active = _active_series(
            hourly,
            target,
            origin,
            config,
            allowed_sensors=target_info["sensor_categories"],
        )
        active_records.append(active)
        for record in active[active["active"]].itertuples(index=False):
            sensor_id = str(record.sensor_id)
            sensor_frame = hourly[hourly["sensor_id"].eq(sensor_id)].set_index("timestamp").sort_index()
            history = sensor_frame.loc[:origin, target].copy()
            observed_column = f"{target}__observed"
            if observed_column in sensor_frame.columns:
                history = history.where(sensor_frame.loc[:origin, observed_column].eq(1))
            champion = target_info["champion_name"]
            forecast = recursive_forecast(
                history=history,
                origin=origin,
                horizon_hours=horizon,
                model=target_info["ml_model"] if champion.startswith("hgb_") else None,
                model_name=champion,
                sensor_id=sensor_id,
                sensor_categories=target_info["sensor_categories"],
                feature_columns=target_info["feature_columns"],
                bounds=_target_bounds(config, target),
                config=config,
            )
            expected_horizons = list(range(1, horizon + 1))
            actual_horizons = (
                forecast["horizon_hour"].astype(int).tolist()
                if not forecast.empty
                else []
            )
            if actual_horizons != expected_horizons or not np.isfinite(
                forecast["prediction"].to_numpy(dtype=float)
            ).all():
                raise RuntimeError(
                    f"Incomplete recursive forecast for ACTIVE pair {sensor_id}/{target}: "
                    f"expected {horizon} finite horizons, received {len(forecast)}."
                )
            lower_bound, upper_bound = _target_bounds(config, target)
            q80 = target_info["calibration"]["absolute_error_q80"]
            q95 = target_info["calibration"]["absolute_error_q95"]
            forecast["lower_80"] = np.clip(forecast["prediction"] - q80, lower_bound, upper_bound)
            forecast["upper_80"] = np.clip(forecast["prediction"] + q80, lower_bound, upper_bound)
            forecast["lower_95"] = np.clip(forecast["prediction"] - q95, lower_bound, upper_bound)
            forecast["upper_95"] = np.clip(forecast["prediction"] + q95, lower_bound, upper_bound)
            forecast["target"] = target
            forecast["target_label"] = config["data"]["targets"][target]["label"]
            forecast["unit"] = config["data"]["targets"][target]["unit"]
            forecast["source_data_cutoff"] = origin
            forecast["recent_coverage"] = float(record.recent_coverage)
            forecast["model_version"] = str(config["project"]["version"])
            forecast["release_status"] = target_info["release_status"]
            forecast["release_reason"] = target_info["release_reason"]
            forecast["interval_method"] = "validation_absolute_residual_quantiles"
            forecast["place"] = metadata.loc[sensor_id, "place"] if sensor_id in metadata.index else "unknown"
            forecasts.append(forecast)
    active_all = pd.concat(active_records, ignore_index=True) if active_records else pd.DataFrame()
    forecast_all = pd.concat(forecasts, ignore_index=True) if forecasts else pd.DataFrame()
    return forecast_all, active_all


def train_and_evaluate(
    prepared: PreparedData,
    config: dict,
    processed_csv_path: str | Path,
    artifacts_dir: str | Path,
    outputs_dir: str | Path,
) -> TrainingOutputs:
    interval_levels = [float(value) for value in config["deployment"]["interval_levels"]]
    if interval_levels != [0.8, 0.95]:
        raise ValueError(
            "This release emits fixed 80% and 95% interval fields; "
            "deployment.interval_levels must equal [0.80, 0.95]."
        )
    if int(config["deployment"]["forecast_horizon_hours"]) != int(
        config["validation"]["forecast_horizon_hours"]
    ):
        raise ValueError("Validation and deployment forecast horizons must match.")
    artifacts_dir = Path(artifacts_dir)
    outputs_dir = Path(outputs_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    created_at_utc = datetime.now(timezone.utc).isoformat()
    split = compute_splits(prepared.hourly, config)
    split_serializable = {
        key: ([str(value) for value in value] if isinstance(value, list) else str(value) if isinstance(value, pd.Timestamp) else value)
        for key, value in split.items()
    }
    split_summary_path = outputs_dir / "split_summary.json"
    write_json(split_summary_path, split_serializable)

    selections: list[pd.DataFrame] = []
    validation_champions: list[pd.DataFrame] = []
    test_predictions: list[pd.DataFrame] = []
    metrics: list[pd.DataFrame] = []
    importances: list[pd.DataFrame] = []
    target_models: dict = {}

    for target in config["data"]["targets"]:
        selection, info, champion_predictions = _candidate_validation(prepared, target, split, config)
        selections.append(selection)
        validation_champions.append(champion_predictions)
        test_prediction, target_metrics, importance, _ = _test_target(prepared, target, info, split, config)
        test_predictions.append(test_prediction)
        metrics.append(target_metrics)
        importances.append(importance)

        final_model, final_categories, final_feature_columns, final_training_rows = _fit_for_cutoff(
            prepared.hourly, target, info["best_ml_name"], None, config
        )
        target_models[target] = {
            "champion_name": info["champion_name"],
            "best_ml_name": info["best_ml_name"],
            "best_ml_parameters": info["best_ml_parameters"],
            "ml_model": final_model,
            "sensor_categories": final_categories,
            "feature_columns": final_feature_columns,
            "validation_training_rows": info["training_rows"],
            "final_training_rows": final_training_rows,
            "calibration": info["calibration"],
            "bounds": _target_bounds(config, target),
            "unit": config["data"]["targets"][target]["unit"],
            "label": config["data"]["targets"][target]["label"],
            "release_status": "pending_validation",
            "release_reason": "Held-out interval gates have not yet been evaluated.",
        }

    selection_frame = pd.concat(selections, ignore_index=True)
    test_prediction_frame = pd.concat(test_predictions, ignore_index=True)
    metrics_frame = pd.concat(metrics, ignore_index=True)
    importance_frame = pd.concat(importances, ignore_index=True) if importances else pd.DataFrame()

    champion_lookup = {target: info["champion_name"] for target, info in target_models.items()}
    champion_test = test_prediction_frame[
        test_prediction_frame.apply(lambda row: row["model_name"] == champion_lookup[row["target"]], axis=1)
    ].copy()
    champion_test["abs_error"] = (champion_test["actual"] - champion_test["prediction"]).abs()
    interval_metrics: list[dict] = []
    for target, frame in champion_test.groupby("target"):
        info = target_models[target]
        valid = frame[frame["actual"].notna()]
        q80 = info["calibration"]["absolute_error_q80"]
        q95 = info["calibration"]["absolute_error_q95"]
        interval_metrics.append(
            {
                "target": target,
                "model_name": info["champion_name"],
                "stage": "test_interval_coverage",
                "n": int(len(valid)),
                "mae": float(valid["abs_error"].mean()) if not valid.empty else np.nan,
                "rmse": np.nan,
                "smape_pct": np.nan,
                "r2": np.nan,
                "coverage_80": float((valid["abs_error"] <= q80).mean()) if not valid.empty else np.nan,
                "coverage_95": float((valid["abs_error"] <= q95).mean()) if not valid.empty else np.nan,
            }
        )
    interval_frame = pd.DataFrame(interval_metrics)
    metrics_frame = pd.concat([metrics_frame, interval_frame], ignore_index=True, sort=False)

    minimum_rows = int(config["deployment"]["minimum_release_rows"])
    minimum_80 = float(config["deployment"]["minimum_80_interval_coverage"])
    minimum_95 = float(config["deployment"]["minimum_95_interval_coverage"])
    interval_lookup = interval_frame.set_index("target").to_dict("index")
    release_overrides = config["deployment"].get("target_release_overrides", {})
    for target, info in target_models.items():
        evidence = interval_lookup.get(target, {})
        reasons: list[str] = []
        if int(evidence.get("n", 0)) < minimum_rows:
            reasons.append(f"fewer than {minimum_rows} held-out observed rows")
        if float(evidence.get("coverage_80", np.nan)) < minimum_80:
            reasons.append(f"80% interval coverage below {minimum_80:.0%}")
        if float(evidence.get("coverage_95", np.nan)) < minimum_95:
            reasons.append(f"95% interval coverage below {minimum_95:.0%}")
        if target in release_overrides:
            reasons.append(str(release_overrides[target]))
        info["release_status"] = "experimental" if reasons else "production_candidate"
        info["release_reason"] = (
            "; ".join(reasons)
            if reasons
            else "Passed configured held-out row-count and marginal interval-coverage gates."
        )

    origin = pd.Timestamp(prepared.hourly["timestamp"].max()).floor("h")
    forecast_frame, active_frame = _generate_final_forecast(prepared, target_models, origin, config)
    if not forecast_frame.empty:
        forecast_frame["generated_at_utc"] = created_at_utc

    config_sha256 = canonical_mapping_sha256(config)
    code_sha256 = model_code_tree_sha256(Path(__file__).resolve().parents[1])
    bundle = {
        "bundle_version": str(config["project"]["version"]),
        "created_at_utc": created_at_utc,
        "source_data_cutoff": origin,
        "source_csv_sha256": sha256_file(processed_csv_path),
        "config_sha256": config_sha256,
        "model_code_sha256": code_sha256,
        "config": config,
        "split": split_serializable,
        "targets": target_models,
        "library_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
    }
    bundle_path = artifacts_dir / "environmental_forecasting_model.joblib"
    joblib.dump(bundle, bundle_path, compress=3)

    manifest = {
        "bundle_version": bundle["bundle_version"],
        "created_at_utc": bundle["created_at_utc"],
        "source_data_cutoff": origin,
        "source_csv_sha256": bundle["source_csv_sha256"],
        "config_sha256": bundle["config_sha256"],
        "model_code_sha256": bundle["model_code_sha256"],
        "model_file": bundle_path.name,
        "model_file_sha256": sha256_file(bundle_path),
        "split": split_serializable,
        "library_versions": bundle["library_versions"],
        "targets": {
            target: {
                key: value
                for key, value in info.items()
                if key != "ml_model"
            }
            for target, info in target_models.items()
        },
        "forecast_scope": {
            "start": forecast_frame["timestamp"].min() if not forecast_frame.empty else None,
            "end": forecast_frame["timestamp"].max() if not forecast_frame.empty else None,
            "rows": int(len(forecast_frame)),
            "active_series": int(active_frame["active"].sum()) if not active_frame.empty else 0,
        },
    }
    manifest_path = artifacts_dir / "model_manifest.json"
    write_json(manifest_path, manifest)

    selection_path = outputs_dir / "model_selection_validation.csv"
    test_predictions_path = outputs_dir / "backtest_predictions.csv"
    metrics_path = outputs_dir / "model_metrics.csv"
    feature_importance_path = outputs_dir / "feature_importance.csv"
    forecast_path = outputs_dir / "forecast_72h.csv"
    active_series_path = outputs_dir / "active_series.csv"
    write_csv_safe(selection_frame, selection_path, index=False)
    write_csv_safe(test_prediction_frame, test_predictions_path, index=False)
    write_csv_safe(metrics_frame, metrics_path, index=False)
    write_csv_safe(
        importance_frame.sort_values(
            ["target", "importance_mae_increase"], ascending=[True, False]
        ),
        feature_importance_path,
        index=False,
    )
    write_csv_safe(forecast_frame, forecast_path, index=False)
    write_csv_safe(active_frame, active_series_path, index=False)

    return TrainingOutputs(
        bundle_path=bundle_path,
        manifest_path=manifest_path,
        forecast_path=forecast_path,
        test_predictions_path=test_predictions_path,
        metrics_path=metrics_path,
        selection_path=selection_path,
        feature_importance_path=feature_importance_path,
        active_series_path=active_series_path,
        split_summary_path=split_summary_path,
    )


def predict_from_bundle(
    bundle_path: str | Path,
    prepared: PreparedData,
    output_path: str | Path,
) -> pd.DataFrame:
    bundle = load_verified_bundle(bundle_path)
    return predict_from_loaded_bundle(bundle, prepared, output_path)


def load_verified_bundle(
    bundle_path: str | Path,
    manifest_path: str | Path | None = None,
) -> dict:
    """Verify the colocated manifest checksum before deserializing a trusted bundle.

    This blocks accidental corruption and single-file substitution.  Production
    deployments should additionally verify a detached signature stored outside
    the artifact write boundary because a colocated manifest is not a trust root.
    """

    bundle_path = Path(bundle_path)
    manifest_path = (
        Path(manifest_path)
        if manifest_path is not None
        else bundle_path.with_name("model_manifest.json")
    )
    if not manifest_path.exists():
        raise FileNotFoundError(f"Model manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hash = str(manifest.get("model_file_sha256", ""))
    computed_hash = sha256_file(bundle_path)
    if not expected_hash or computed_hash != expected_hash:
        raise ValueError(
            "Model checksum verification failed before deserialization: "
            f"computed={computed_hash}; expected={expected_hash or '<missing>'}"
        )
    bundle = joblib.load(bundle_path)
    if str(bundle.get("bundle_version")) != str(manifest.get("bundle_version")):
        raise ValueError("Model bundle version does not match the verified manifest.")
    computed_config_hash = canonical_mapping_sha256(bundle.get("config", {}))
    if (
        not manifest.get("config_sha256")
        or bundle.get("config_sha256") != manifest.get("config_sha256")
        or computed_config_hash != manifest.get("config_sha256")
    ):
        raise ValueError("Model configuration fingerprint does not match the verified manifest.")
    computed_code_hash = model_code_tree_sha256(Path(__file__).resolve().parents[1])
    if (
        not manifest.get("model_code_sha256")
        or bundle.get("model_code_sha256") != manifest.get("model_code_sha256")
        or computed_code_hash != manifest.get("model_code_sha256")
    ):
        raise ValueError("Model code fingerprint does not match the verified manifest.")
    return bundle


def predict_from_loaded_bundle(
    bundle: dict,
    prepared: PreparedData,
    output_path: str | Path,
    eligibility_output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Generate forecasts from an already verified and loaded bundle."""

    config = bundle["config"]
    known_sensors = {
        str(sensor)
        for target_info in bundle["targets"].values()
        for sensor in target_info["sensor_categories"]
    }
    known_rows = prepared.hourly[
        prepared.hourly["sensor_id"].astype(str).isin(known_sensors)
    ]
    if known_rows.empty:
        raise ValueError("Input contains no sensor category known to the verified model.")
    origin = pd.Timestamp(known_rows["timestamp"].max()).floor("h")
    maximum_future_skew = int(
        config["deployment"].get("maximum_future_clock_skew_hours", 24)
    )
    if maximum_future_skew < 0:
        raise ValueError("maximum_future_clock_skew_hours cannot be negative.")
    current_utc_naive = pd.Timestamp.now(tz="UTC").tz_localize(None)
    if origin > current_utc_naive + pd.Timedelta(hours=maximum_future_skew):
        raise ValueError(
            f"Known-sensor input watermark {origin} is beyond the permitted future clock skew."
        )
    forecasts, eligibility = _generate_final_forecast(
        prepared, bundle["targets"], origin, config
    )
    if not forecasts.empty:
        forecasts["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    write_csv_safe(forecasts, output_path, index=False)
    if eligibility_output_path is not None:
        eligibility_path = Path(eligibility_output_path)
        eligibility_path.parent.mkdir(parents=True, exist_ok=True)
        write_csv_safe(eligibility, eligibility_path, index=False)
    return forecasts
