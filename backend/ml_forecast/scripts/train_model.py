#!/usr/bin/env python3
"""Train, validate, backtest, and serialize the environmental forecast model."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_io import write_csv_safe, write_json
from src.modeling import train_and_evaluate
from src.preprocessing import load_config, prepare_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default=str(PROJECT_ROOT / "data" / "processed" / "sensor_readings.csv"),
    )
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "config" / "model_config.yaml"),
    )
    parser.add_argument(
        "--artifacts-dir",
        default=str(PROJECT_ROOT / "artifacts"),
    )
    parser.add_argument(
        "--outputs-dir",
        default=str(PROJECT_ROOT / "outputs"),
    )
    args = parser.parse_args()
    config = load_config(args.config)
    prepared = prepare_data(args.csv, config)

    outputs_dir = Path(args.outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    write_json(outputs_dir / "data_quality_summary.json", prepared.quality_summary)
    write_csv_safe(prepared.invalid_counts, outputs_dir / "invalid_measurements.csv", index=False)
    write_csv_safe(prepared.sensor_metadata, outputs_dir / "sensor_metadata.csv", index=False)
    write_csv_safe(prepared.sensor_coverage, outputs_dir / "sensor_coverage.csv", index=False)
    prepared.hourly.to_csv(PROJECT_ROOT / "data" / "processed" / "sensor_hourly_clean.csv", index=False)

    result = train_and_evaluate(
        prepared=prepared,
        config=config,
        processed_csv_path=args.csv,
        artifacts_dir=args.artifacts_dir,
        outputs_dir=args.outputs_dir,
    )
    print(f"Model bundle: {result.bundle_path}")
    print(f"Forecast: {result.forecast_path}")
    print(f"Metrics: {result.metrics_path}")


if __name__ == "__main__":
    main()
