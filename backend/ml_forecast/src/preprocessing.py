"""Data quality checks and hourly preprocessing for sensor time series."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


@dataclass
class PreparedData:
    raw: pd.DataFrame
    cleaned: pd.DataFrame
    hourly: pd.DataFrame
    sensor_metadata: pd.DataFrame
    quality_summary: dict
    invalid_counts: pd.DataFrame
    sensor_coverage: pd.DataFrame


def load_config(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_sensor_csv(path: str | Path, config: dict) -> pd.DataFrame:
    timestamp = config["data"]["timestamp_column"]
    frame = pd.read_csv(path, low_memory=False)
    expected = list(config["data"]["source_columns"])
    if frame.columns.tolist() != expected:
        raise ValueError(
            "Input schema mismatch. Expected columns in this exact order: "
            f"{expected}; found: {frame.columns.tolist()}"
        )
    if frame.empty:
        raise ValueError("Input contains the required header but no data rows.")

    raw_timestamps = frame[timestamp].copy()
    timestamp_text = raw_timestamps.astype("string").str.strip()
    blank_timestamps = raw_timestamps.isna() | timestamp_text.eq("")
    if blank_timestamps.any():
        raise ValueError(
            f"Input contains {int(blank_timestamps.sum())} blank timestamps in {timestamp!r}."
        )
    numeric_timestamps = pd.to_numeric(timestamp_text, errors="coerce").notna()
    if numeric_timestamps.any():
        raise ValueError(
            f"Input contains {int(numeric_timestamps.sum())} numeric timestamps in {timestamp!r}; "
            "provide explicit date-time text rather than Excel serials or epoch values."
        )
    parsed_timestamps = pd.to_datetime(timestamp_text, errors="coerce", format="mixed")
    if not pd.api.types.is_datetime64_any_dtype(parsed_timestamps.dtype):
        raise ValueError(
            "Timestamps must use one consistent timezone-naive text representation."
        )
    malformed_timestamps = parsed_timestamps.isna()
    if malformed_timestamps.any():
        raise ValueError(
            f"Input contains {int(malformed_timestamps.sum())} nonblank, unparseable timestamps."
        )
    minimum_year = int(config["data"].get("minimum_timestamp_year", 2000))
    maximum_year = int(config["data"].get("maximum_timestamp_year", 2100))
    if minimum_year > maximum_year:
        raise ValueError(
            "minimum_timestamp_year must be less than or equal to maximum_timestamp_year."
        )
    timestamp_years = parsed_timestamps.dt.year
    implausible_timestamps = timestamp_years.lt(minimum_year) | timestamp_years.gt(maximum_year)
    if implausible_timestamps.any():
        sample = timestamp_text.loc[implausible_timestamps].iloc[0]
        raise ValueError(
            f"Input contains {int(implausible_timestamps.sum())} timestamps outside the "
            f"configured calendar range {minimum_year}-{maximum_year}; example={sample!r}."
        )
    frame[timestamp] = parsed_timestamps

    for target in config["data"]["targets"]:
        raw_values = frame[target].copy()
        converted = pd.to_numeric(raw_values, errors="coerce")
        malformed = raw_values.notna() & converted.isna()
        if malformed.any():
            raise ValueError(
                f"Column {target!r} contains {int(malformed.sum())} nonblank, nonnumeric values."
            )
        frame[target] = converted
    sensor = config["data"]["sensor_id_column"]
    if frame[sensor].isna().any() or frame[sensor].astype(str).str.strip().eq("").any():
        raise ValueError(f"Stable sensor identifier {sensor!r} must be nonblank for every row.")

    raw_ids = frame["id"].copy()
    id_text = raw_ids.astype("string").str.strip()
    blank_ids = raw_ids.isna() | id_text.eq("")
    if blank_ids.any():
        raise ValueError(f"Source id contains {int(blank_ids.sum())} blank values.")
    numeric_ids = pd.to_numeric(id_text, errors="coerce")
    malformed_ids = numeric_ids.isna() | ~np.isfinite(numeric_ids)
    if malformed_ids.any():
        raise ValueError(
            f"Source id contains {int(malformed_ids.sum())} nonnumeric or non-finite values."
        )
    fractional_ids = numeric_ids.ne(np.floor(numeric_ids))
    if fractional_ids.any():
        raise ValueError(
            f"Source id contains {int(fractional_ids.sum())} non-integer values."
        )
    integer_limits = np.iinfo(np.int64)
    outside_integer_range = numeric_ids.lt(integer_limits.min) | numeric_ids.gt(integer_limits.max)
    if outside_integer_range.any():
        raise ValueError("Source id contains values outside the signed 64-bit integer range.")
    normalized_ids = numeric_ids.astype(np.int64)
    duplicate_ids = normalized_ids.duplicated(keep=False)
    if duplicate_ids.any():
        raise ValueError(
            f"Source id must be unique; {int(duplicate_ids.sum())} rows have duplicate ids."
        )
    frame["id"] = normalized_ids
    return frame


def _mode_or_unknown(series: pd.Series, unknown: str = "unknown") -> str:
    values = series.dropna().astype(str).str.strip()
    values = values[values.ne("")]
    if values.empty:
        return unknown
    return str(values.mode().iloc[0])


def _build_sensor_metadata(frame: pd.DataFrame, config: dict) -> pd.DataFrame:
    sensor = config["data"]["sensor_id_column"]
    timestamp = config["data"]["timestamp_column"]
    grouped = frame.groupby(sensor, dropna=False)
    metadata = grouped.agg(
        first_observation=(timestamp, "min"),
        last_observation=(timestamp, "max"),
        raw_rows=(timestamp, "size"),
        network_addresses=("indoor_lora_dev_adr", "nunique"),
        place=("place", _mode_or_unknown),
        description=("description", _mode_or_unknown),
    ).reset_index()
    metadata = metadata.rename(columns={sensor: "sensor_id"})
    return metadata.sort_values("sensor_id").reset_index(drop=True)


def clean_measurements(frame: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply explicit validity rules while preserving the original frame separately."""

    cleaned = frame.copy()
    targets = config["data"]["targets"]
    invalid_records: list[dict] = []

    simultaneous_zero = (
        cleaned["humidity_pct"].eq(0)
        & cleaned["temperature_c"].eq(0)
    )
    simultaneous_environment_zero = simultaneous_zero & cleaned["pm10_ugm3"].eq(0) & cleaned["pm25_ugm3"].eq(0)

    special_masks = {
        "humidity_pct": simultaneous_zero,
        "temperature_c": simultaneous_zero,
        "pm10_ugm3": simultaneous_environment_zero,
        "pm25_ugm3": simultaneous_environment_zero,
    }

    for target, specification in targets.items():
        series = cleaned[target]
        range_invalid = series.notna() & (
            series.lt(float(specification["lower_bound"]))
            | series.gt(float(specification["upper_bound"]))
        )
        special_invalid = special_masks.get(target, pd.Series(False, index=cleaned.index))
        invalid = range_invalid | special_invalid
        invalid_records.append(
            {
                "target": target,
                "source_non_null": int(series.notna().sum()),
                "source_null": int(series.isna().sum()),
                "range_invalid": int(range_invalid.sum()),
                "sentinel_zero_invalid": int(special_invalid.sum()),
                "total_invalidated": int(invalid.sum()),
                "retained_valid": int((series.notna() & ~invalid).sum()),
            }
        )
        cleaned.loc[invalid, target] = np.nan

    return cleaned, pd.DataFrame(invalid_records)


def interpolate_complete_internal_gaps(series: pd.Series, limit: int) -> pd.Series:
    """Linearly fill only complete internal missing runs no longer than ``limit``.

    Pandas' ``interpolate(limit=N)`` fills the first N cells of longer gaps.  The
    production policy is stricter: a run is filled only when the entire run has
    at most N cells and has a real value on both sides.
    """

    if limit <= 0 or series.empty:
        return series.copy()
    missing = series.isna()
    if not missing.any():
        return series.copy()
    groups = missing.ne(missing.shift(fill_value=False)).cumsum()
    run_lengths = missing.groupby(groups).transform("sum")
    internal = series.ffill().notna() & series.bfill().notna()
    fill_mask = missing & internal & run_lengths.le(limit)
    candidates = series.interpolate(method="time", limit_area="inside")
    result = series.copy()
    result.loc[fill_mask] = candidates.loc[fill_mask]
    return result


def _hourly_resample(cleaned: pd.DataFrame, config: dict) -> pd.DataFrame:
    sensor = config["data"]["sensor_id_column"]
    timestamp = config["data"]["timestamp_column"]
    targets = list(config["data"]["targets"])
    interpolation_limit = int(config["data"]["short_gap_interpolation_hours"])
    frequency = str(config["data"]["resample_frequency"])
    aggregation = str(config["data"]["aggregation"]).lower()
    if frequency.lower() not in {"1h", "h"}:
        raise ValueError("This model version requires an hourly resample frequency.")
    if aggregation != "median":
        raise ValueError("This model version supports median aggregation only.")
    frames: list[pd.DataFrame] = []

    for sensor_id, sensor_frame in cleaned.groupby(sensor, sort=True):
        sensor_frame = sensor_frame.sort_values(timestamp).set_index(timestamp)
        measures = sensor_frame[targets].resample(frequency).median()
        observed = measures.notna().astype(int)
        interpolated = measures.apply(
            lambda values: interpolate_complete_internal_gaps(values, interpolation_limit)
        )
        counts = sensor_frame[targets].resample(frequency).count()
        interpolated["reading_count"] = sensor_frame["id"].resample(frequency).count()
        for target in targets:
            interpolated[f"{target}__observed"] = observed[target]
            interpolated[f"{target}__interpolated"] = (
                measures[target].isna() & interpolated[target].notna()
            ).astype(int)
            interpolated[f"{target}__reading_count"] = counts[target]
        interpolated["sensor_id"] = str(sensor_id)
        interpolated["timestamp"] = interpolated.index
        frames.append(interpolated.reset_index(drop=True))

    hourly = pd.concat(frames, ignore_index=True)
    return hourly.sort_values(["sensor_id", "timestamp"]).reset_index(drop=True)


def _sensor_coverage(hourly: pd.DataFrame, metadata: pd.DataFrame, config: dict) -> pd.DataFrame:
    targets = list(config["data"]["targets"])
    rows: list[dict] = []
    metadata_lookup = metadata.set_index("sensor_id").to_dict("index")
    for sensor_id, sensor_frame in hourly.groupby("sensor_id", sort=True):
        row = {
            "sensor_id": sensor_id,
            "hourly_rows": int(len(sensor_frame)),
            "first_hour": sensor_frame["timestamp"].min(),
            "last_hour": sensor_frame["timestamp"].max(),
            "place": metadata_lookup.get(sensor_id, {}).get("place", "unknown"),
        }
        for target in targets:
            row[f"{target}_coverage"] = float(sensor_frame[target].notna().mean())
            row[f"{target}_observed_coverage"] = float(
                sensor_frame[f"{target}__observed"].mean()
            )
        rows.append(row)
    return pd.DataFrame(rows)


def prepare_data(csv_path: str | Path, config: dict) -> PreparedData:
    raw = load_sensor_csv(csv_path, config)
    sensor = config["data"]["sensor_id_column"]
    timestamp = config["data"]["timestamp_column"]
    targets = list(config["data"]["targets"])
    metadata = _build_sensor_metadata(raw, config)
    cleaned, invalid_counts = clean_measurements(raw, config)
    hourly = _hourly_resample(cleaned, config)
    coverage = _sensor_coverage(hourly, metadata, config)

    duplicate_key_columns = [sensor, timestamp]
    quality_summary = {
        "raw_rows": int(len(raw)),
        "raw_columns": int(raw.shape[1]),
        "data_start": raw[timestamp].min(),
        "data_end": raw[timestamp].max(),
        "sensor_count": int(raw[sensor].nunique(dropna=True)),
        "network_address_count": int(raw["indoor_lora_dev_adr"].nunique(dropna=True)),
        "exact_duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_sensor_timestamp_extra_rows": int(raw.duplicated(duplicate_key_columns).sum()),
        "duplicate_sensor_timestamp_affected_rows": int(raw.duplicated(duplicate_key_columns, keep=False).sum()),
        "timestamp_parse_failures": int(raw[timestamp].isna().sum()),
        "missing_percent": {
            column: float(raw[column].isna().mean()) for column in raw.columns
        },
        "hourly_rows": int(len(hourly)),
        "hourly_start": hourly["timestamp"].min(),
        "hourly_end": hourly["timestamp"].max(),
        "targets": targets,
        "timezone_assumption": config["project"]["timezone_assumption"],
    }
    return PreparedData(
        raw=raw,
        cleaned=cleaned,
        hourly=hourly,
        sensor_metadata=metadata,
        quality_summary=quality_summary,
        invalid_counts=invalid_counts,
        sensor_coverage=coverage,
    )
