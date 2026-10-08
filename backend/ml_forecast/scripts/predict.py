#!/usr/bin/env python3
"""Generate a new 72-hour forecast from fresh sensor CSV data."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_io import xlsx_to_csv
from src.modeling import load_verified_bundle, predict_from_loaded_bundle
from src.preprocessing import prepare_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Fresh CSV or XLSX observations")
    parser.add_argument(
        "--model",
        default=str(PROJECT_ROOT / "artifacts" / "environmental_forecasting_model.joblib"),
    )
    parser.add_argument("--output", default=str(PROJECT_ROOT / "outputs" / "forecast_new_72h.csv"))
    parser.add_argument(
        "--eligibility-output",
        default=str(PROJECT_ROOT / "outputs" / "eligibility_new.csv"),
        help="Reason-coded eligibility output for every sensor-target pair",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    model_path = Path(args.model).resolve()
    output_path = Path(args.output).resolve()
    eligibility_path = Path(args.eligibility_output).resolve()
    if input_path.suffix.lower() not in {".csv", ".xlsx"}:
        parser.error("--input must use the .csv or .xlsx extension")
    if len({input_path, model_path, output_path, eligibility_path}) != 4:
        parser.error("Input, model, forecast output, and eligibility output must be distinct paths")
    if not input_path.is_file():
        parser.error(f"Input file not found: {input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    eligibility_path.parent.mkdir(parents=True, exist_ok=True)

    bundle = load_verified_bundle(model_path)
    with tempfile.NamedTemporaryFile(
        prefix=".forecast-", suffix=".csv", dir=output_path.parent, delete=False
    ) as forecast_handle, tempfile.NamedTemporaryFile(
        prefix=".eligibility-", suffix=".csv", dir=eligibility_path.parent, delete=False
    ) as eligibility_handle:
        temporary_forecast = Path(forecast_handle.name)
        temporary_eligibility = Path(eligibility_handle.name)
    try:
        if input_path.suffix.lower() == ".xlsx":
            with tempfile.TemporaryDirectory(prefix="sensor-forecast-") as temp_dir:
                csv_path = Path(temp_dir) / "sensor_readings.csv"
                xlsx_to_csv(
                    input_path,
                    csv_path,
                    expected_columns=int(bundle["config"]["data"]["expected_columns"]),
                    expected_header=bundle["config"]["data"]["source_columns"],
                )
                prepared = prepare_data(csv_path, bundle["config"])
        else:
            prepared = prepare_data(input_path, bundle["config"])
        forecast = predict_from_loaded_bundle(
            bundle, prepared, temporary_forecast, temporary_eligibility
        )
        os.replace(temporary_eligibility, eligibility_path)
        os.replace(temporary_forecast, output_path)
    finally:
        temporary_forecast.unlink(missing_ok=True)
        temporary_eligibility.unlink(missing_ok=True)
    print(f"Generated {len(forecast):,} forecast rows in {output_path}")


if __name__ == "__main__":
    main()
